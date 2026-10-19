"""Orchestration : brut -> préparation -> quarantaine -> cœur -> marts, avec tests bloquants.

  python -m src.pipeline run                 # chargement complet (idempotent)
  python -m src.pipeline reload --month 2024_03   # rechargement d'un mois
  python -m src.pipeline test                # tests seuls
Les transformations (prep/quarantaine/cœur/marts) tournent dans UNE transaction : si un test
échoue, ROLLBACK -> le cœur reste dans son dernier état valide et le code de sortie est 1.
"""
import argparse, sys, uuid
from datetime import datetime
from pathlib import Path

import duckdb

from .config import DEFAULT_DB, DEFAULT_SRC, EXTRACT_DATE, OBS_END, SQL_DIR
from .ingest import create_raw_tables, ingest_all
from .quality_rules import RULES
from .tests_sql import TESTS


def sql(text: str) -> str:
    return text.replace("${EXTRACT_DATE}", EXTRACT_DATE).replace("${OBS_END}", OBS_END)


def run_tests(con, extra_tests=()):
    out = []
    for tid, desc, q in list(TESTS) + list(extra_tests):
        n = con.execute(sql(q)).fetchone()[0] or 0
        out.append((tid, desc, int(n), "OK" if n == 0 else "ECHEC"))
    return out


def measure_rules(con):
    return [(rid, dim, tbl, desc, grav, trait, int(con.execute(sql(q)).fetchone()[0] or 0), sql(q))
            for rid, dim, tbl, desc, grav, trait, q in RULES]


def persist_reports(con, run_id, rules, tests):
    con.execute("""CREATE TABLE IF NOT EXISTS dq.rule_results (run_id VARCHAR, rule_id VARCHAR, dimension VARCHAR,
        entity VARCHAR, description VARCHAR, severity VARCHAR, treatment VARCHAR, volume INTEGER, query VARCHAR,
        computed_at TIMESTAMP)""")
    con.execute("""CREATE TABLE IF NOT EXISTS ops.test_results (run_id VARCHAR, test_id VARCHAR, description VARCHAR,
        violations INTEGER, status VARCHAR, executed_at TIMESTAMP)""")
    now = datetime.now()
    if rules:
        con.execute("DELETE FROM dq.rule_results")  # état courant ; l'historique des runs est dans ops.pipeline_runs
        for r in rules:
            con.execute("INSERT INTO dq.rule_results VALUES (?,?,?,?,?,?,?,?,?,?)", [run_id, *r, now])
    for t in tests:
        con.execute("INSERT INTO ops.test_results VALUES (?,?,?,?,?,?)", [run_id, *t, now])


def run(db=DEFAULT_DB, src=DEFAULT_SRC, reload_month=None, extra_tests=(), verbose=True):
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S_") + uuid.uuid4().hex[:6]
    started = datetime.now()
    con = duckdb.connect(str(db))
    create_raw_tables(con)
    try:
        res = ingest_all(con, Path(src), run_id, reload_month)
    except Exception as e:
        con.execute("INSERT INTO ops.pipeline_runs VALUES (?,?,?,?,?,?,?)",
                    [run_id, started, datetime.now(), "ECHEC_INGESTION", 0, 0, str(e)])
        con.close()
        raise SystemExit(f"Ingestion en échec : {e}")
    if verbose:
        loaded = sum(v == "LOADED" for v in res.values())
        print(f"[ingestion] {loaded} fichier(s) chargé(s), {len(res) - loaded} inchangé(s)")

    con.execute("BEGIN")
    try:
        for f in ("10_prep.sql", "20_quarantine.sql", "30_core.sql", "40_marts.sql"):
            con.execute(sql((SQL_DIR / f).read_text(encoding="utf-8")))
        rules = measure_rules(con)
        tests = run_tests(con, extra_tests)
    except Exception:
        con.execute("ROLLBACK"); con.close(); raise
    failed = [t for t in tests if t[3] != "OK"]
    if failed:
        con.execute("ROLLBACK")
        persist_reports(con, run_id, [], tests)
        con.execute("INSERT INTO ops.pipeline_runs VALUES (?,?,?,?,?,?,?)",
                    [run_id, started, datetime.now(), "ECHEC_TESTS", len(tests), len(failed),
                     "; ".join(f"{t[0]}={t[2]}" for t in failed)])
        con.close()
        for t in failed:
            print(f"[test ECHEC] {t[0]} : {t[1]} -> {t[2]} violation(s)", file=sys.stderr)
        raise SystemExit("Tests bloquants en échec : transformations annulées (cœur inchangé).")
    con.execute("COMMIT")
    persist_reports(con, run_id, rules, tests)
    con.execute("INSERT INTO ops.pipeline_runs VALUES (?,?,?,?,?,?,?)",
                [run_id, started, datetime.now(), "SUCCES", len(tests), 0, ""])
    if verbose:
        print(f"[tests] {len(tests)}/{len(tests)} OK   [règles qualité] {len(rules)} mesurées")
    con.close()
    return run_id


def main():
    p = argparse.ArgumentParser(prog="boreal")
    p.add_argument("cmd", choices=["run", "reload", "test"])
    p.add_argument("--db", default=str(DEFAULT_DB)); p.add_argument("--src", default=str(DEFAULT_SRC))
    p.add_argument("--month", help="ex. 2024_03 (avec reload)")
    a = p.parse_args()
    if a.cmd == "reload" and not a.month:
        p.error("--month requis")
    if a.cmd == "test":
        con = duckdb.connect(a.db, read_only=True)
        bad = [t for t in run_tests(con) if t[3] != "OK"]
        for t in bad: print("ECHEC", t)
        sys.exit(1 if bad else 0)
    run(a.db, a.src, a.month if a.cmd == "reload" else None)


if __name__ == "__main__":
    main()
