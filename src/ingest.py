"""Ingestion vers la couche BRUTE : copie fidèle, tout en texte, aucune transformation.

Chaque ligne conserve : fichier d'origine, empreinte du fichier, numéro de ligne,
date de chargement, run. Les lignes illisibles vont dans quarantine.raw_rejects.
Idempotence : un fichier déjà chargé (même empreinte) est ignoré ; un fichier modifié
ou un rechargement forcé remplace UNIQUEMENT les lignes de ce fichier.
"""
import csv, hashlib, io, json, time
from datetime import datetime
from pathlib import Path

import pandas as pd

from .config import SCHEMAS, OPTIONAL, PATTERNS

META = ["_source_file", "_file_hash", "_row_num", "_loaded_at", "_run_id", "_encoding"]


def create_raw_tables(con):
    for s in ("raw", "prep", "quarantine", "dq", "core", "marts", "ops"):
        con.execute(f"CREATE SCHEMA IF NOT EXISTS {s}")
    for src, cols in SCHEMAS.items():
        defs = ", ".join(f"{c} VARCHAR" for c in cols)
        con.execute(f"""CREATE TABLE IF NOT EXISTS raw.{src} ({defs}, _source_file VARCHAR,
            _file_hash VARCHAR, _row_num INTEGER, _loaded_at TIMESTAMP, _run_id VARCHAR, _encoding VARCHAR)""")
    con.execute("""CREATE TABLE IF NOT EXISTS quarantine.raw_rejects (source VARCHAR, source_file VARCHAR,
        row_num INTEGER, motif VARCHAR, raw_line VARCHAR, run_id VARCHAR)""")
    con.execute("""CREATE TABLE IF NOT EXISTS ops.ingestion_log (run_id VARCHAR, source VARCHAR, file VARCHAR,
        file_hash VARCHAR, rows_read INTEGER, rows_loaded INTEGER, rows_rejected INTEGER,
        duration_s DOUBLE, status VARCHAR, message VARCHAR, logged_at TIMESTAMP)""")
    _create_report_tables(con)
    con.execute("""CREATE TABLE IF NOT EXISTS ops.pipeline_runs (run_id VARCHAR, started_at TIMESTAMP,
        finished_at TIMESTAMP, status VARCHAR, n_tests INTEGER, n_tests_failed INTEGER, message VARCHAR)""")


def _create_report_tables(con):
    """Tables de rapport créées dès l'ingestion : les vues marts.ops_* en dépendent."""
    con.execute("""CREATE TABLE IF NOT EXISTS dq.rule_results (run_id VARCHAR, rule_id VARCHAR, dimension VARCHAR,
        entity VARCHAR, description VARCHAR, severity VARCHAR, treatment VARCHAR, volume INTEGER, query VARCHAR,
        computed_at TIMESTAMP)""")
    con.execute("""CREATE TABLE IF NOT EXISTS ops.test_results (run_id VARCHAR, test_id VARCHAR, description VARCHAR,
        violations INTEGER, status VARCHAR, executed_at TIMESTAMP)""")


def decode(data: bytes):
    """UTF-8 d'abord (BOM toléré), repli latin-1 : couvre CRM (latin-1) et les autres sources."""
    try:
        return data.decode("utf-8-sig"), "utf-8"
    except UnicodeDecodeError:
        return data.decode("latin-1"), "latin-1"


def parse_file(source, path: Path):
    """Retourne (lignes valides [(row_num, dict)], rejets [(row_num, motif, ligne)], encodage)."""
    text, enc = decode(path.read_bytes())
    lines = text.splitlines()
    schema = set(SCHEMAS[source])
    good, bad = [], []
    if path.suffix == ".jsonl":
        for i, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
                if not isinstance(obj, dict):
                    raise ValueError("ligne JSON qui n'est pas un objet")
            except ValueError as e:
                bad.append((i, f"JSON invalide : {e}", line)); continue
            unknown = set(obj) - schema
            if unknown:
                raise ValueError(f"{path.name} : champs inconnus {sorted(unknown)} (dérive de schéma)")
            good.append((i, {k: (None if v is None else str(v)) for k, v in obj.items()}))
        return good, bad, enc
    header_line = lines[0]
    delim = ";" if header_line.count(";") > header_line.count(",") else ","
    reader = csv.reader(io.StringIO(text), delimiter=delim)
    header = [h.strip().lower() for h in next(reader)]
    unknown = set(header) - schema
    if unknown:
        raise ValueError(f"{path.name} : colonnes inconnues {sorted(unknown)} (dérive de schéma)")
    required = schema - OPTIONAL.get(source, set())
    missing = required - set(header)
    if missing:
        raise ValueError(f"{path.name} : colonnes manquantes {sorted(missing)}")
    if OPTIONAL.get(source) and not (set(header) & OPTIONAL[source]):
        raise ValueError(f"{path.name} : aucune colonne montant")
    for i, row in enumerate(reader, start=2):
        if not row:
            continue
        if len(row) != len(header):
            bad.append((i, f"{len(row)} champs au lieu de {len(header)}", delim.join(row))); continue
        good.append((i, {h: (v if v != "" else None) for h, v in zip(header, row)}))
    return good, bad, enc


def log(con, run_id, source, rel, fhash, read, loaded, rejected, dur, status, msg=""):
    con.execute("INSERT INTO ops.ingestion_log VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                [run_id, source, rel, fhash, read, loaded, rejected, round(dur, 3), status, msg, datetime.now()])


def load_file(con, source, path: Path, rel: str, run_id: str, force=False):
    t0 = time.time()
    fhash = hashlib.sha256(path.read_bytes()).hexdigest()
    already = con.execute(f"SELECT count(*) FROM raw.{source} WHERE _source_file=? AND _file_hash=?",
                          [rel, fhash]).fetchone()[0]
    if already and not force:
        log(con, run_id, source, rel, fhash, 0, 0, 0, time.time() - t0, "SKIPPED_UNCHANGED",
            "fichier déjà chargé (même empreinte)")
        return "SKIPPED_UNCHANGED"
    try:
        good, bad, enc = parse_file(source, path)
    except Exception as e:  # dérive de schéma, fichier illisible...
        log(con, run_id, source, rel, fhash, 0, 0, 0, time.time() - t0, "FAILED", str(e))
        raise
    cols = SCHEMAS[source]
    now = datetime.now()
    df = pd.DataFrame([[d.get(c) for c in cols] + [rel, fhash, n, now, run_id, enc] for n, d in good],
                      columns=cols + META)
    con.execute("BEGIN")
    try:
        con.execute(f"DELETE FROM raw.{source} WHERE _source_file=?", [rel])
        con.execute("DELETE FROM quarantine.raw_rejects WHERE source_file=?", [rel])
        if len(df):
            con.register("_df", df)
            con.execute(f"INSERT INTO raw.{source} SELECT * FROM _df")
            con.unregister("_df")
        for n, motif, line in bad:
            con.execute("INSERT INTO quarantine.raw_rejects VALUES (?,?,?,?,?,?)",
                        [source, rel, n, motif, line, run_id])
        con.execute("COMMIT")
    except Exception as e:
        con.execute("ROLLBACK")
        log(con, run_id, source, rel, fhash, len(good) + len(bad), 0, len(bad), time.time() - t0, "FAILED", str(e))
        raise
    msg = "rechargement forcé" if (already and force) else ""
    log(con, run_id, source, rel, fhash, len(good) + len(bad), len(good), len(bad), time.time() - t0, "LOADED", msg)
    return "LOADED"


def ingest_all(con, src_dir: Path, run_id: str, reload_pattern: str | None = None):
    """Charge toutes les sources. reload_pattern (ex. '2024_03') force le rechargement des fichiers concernés."""
    create_raw_tables(con)
    results = {}
    manquantes = [s for s, pat in PATTERNS.items() if not list(src_dir.glob(pat))]
    if manquantes:  # une livraison absente doit declencher une alerte, pas un 'rien a charger' silencieux
        raise FileNotFoundError(f"Aucun fichier trouve pour : {', '.join(manquantes)} (dossier {src_dir})")
    for source, pattern in PATTERNS.items():
        for path in sorted(src_dir.glob(pattern)):
            rel = path.relative_to(src_dir).as_posix()
            force = bool(reload_pattern and reload_pattern in path.name)
            results[rel] = load_file(con, source, path, rel, run_id, force)
    return results
