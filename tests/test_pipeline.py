"""Démonstrations exigées : rejeu sans doublon, fichier livré deux fois, rechargement d'un mois, test bloquant."""
import shutil
from pathlib import Path

import duckdb
import pytest

from src.config import DEFAULT_SRC
from src.pipeline import run

TABLES = ["raw.reglements", "prep.reglements", "core.fact_reglement", "core.fact_sinistre", "core.fact_exposition",
          "core.dim_contrat", "core.dim_client", "quarantine.rows"]


def fingerprint(db):
    con = duckdb.connect(str(db), read_only=True)
    fp = {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in TABLES}
    fp["montant_total"] = con.execute("SELECT SUM(montant) FROM core.fact_reglement").fetchone()[0]
    fp["ids"] = con.execute("SELECT hash(list(paiement_id ORDER BY paiement_id)) FROM core.fact_reglement").fetchone()[0]
    con.close()
    return fp


@pytest.fixture()
def env(tmp_path):
    src = tmp_path / "sources"
    shutil.copytree(DEFAULT_SRC, src)
    db = tmp_path / "t.duckdb"
    run(db, src, verbose=False)
    return db, src


def test_chargement_initial(env):
    db, _ = env
    fp = fingerprint(db)
    assert fp["core.dim_client"] == 15000          # 15 200 lignes - 200 doublons
    assert fp["core.fact_reglement"] == 3174       # 3 175 uniques - 1 règlement d'un sinistre en quarantaine
    assert fp["raw.reglements"] == 3207            # copie fidèle, doublons compris


def test_rejeu_complet_idempotent(env):
    db, src = env
    avant = fingerprint(db)
    run(db, src, verbose=False)
    run(db, src, verbose=False)
    assert fingerprint(db) == avant


def test_rechargement_d_un_mois_idempotent(env):
    db, src = env
    avant = fingerprint(db)
    run(db, src, reload_month="2024_03", verbose=False)   # fichier à l'en-tête atypique
    run(db, src, reload_month="2023_06", verbose=False)
    assert fingerprint(db) == avant
    con = duckdb.connect(str(db), read_only=True)
    assert con.execute("SELECT COUNT(*) FROM ops.ingestion_log WHERE message='rechargement forcé'").fetchone()[0] == 2


def test_fichier_livre_deux_fois(env):
    db, src = env
    avant = fingerprint(db)
    n = sum(1 for _ in open(src / "reglements/reglements_2023_06.csv")) - 1
    shutil.copy(src / "reglements/reglements_2023_06.csv", src / "reglements/reglements_2023_06_bis.csv")
    run(db, src, verbose=False)
    apres = fingerprint(db)
    assert apres["core.fact_reglement"] == avant["core.fact_reglement"]
    assert apres["montant_total"] == avant["montant_total"]
    assert apres["quarantine.rows"] == avant["quarantine.rows"] + n   # chaque ligne re-livrée est tracée
    assert apres["raw.reglements"] == avant["raw.reglements"] + n     # le brut reste une copie fidèle


def test_test_bloquant_annule_les_transformations(env):
    db, src = env
    avant = fingerprint(db)
    shutil.copy(src / "reglements/reglements_2023_06.csv", src / "reglements/reglements_2023_06_bis.csv")
    faux_test = [("T99_force_echec", "Test volontairement en échec", "SELECT 1")]
    with pytest.raises(SystemExit):
        run(db, src, extra_tests=faux_test, verbose=False)
    con = duckdb.connect(str(db), read_only=True)
    assert con.execute("SELECT status FROM ops.pipeline_runs ORDER BY started_at DESC LIMIT 1").fetchone()[0] == "ECHEC_TESTS"
    con.close()
    apres = fingerprint(db)
    assert apres["raw.reglements"] > avant["raw.reglements"]   # le brut garde la livraison (copie fidèle)
    for k in avant:                                              # mais prep/cœur/quarantaine n'ont pas bougé
        if not k.startswith("raw."):
            assert apres[k] == avant[k], k


def test_derive_de_schema_stoppe_l_ingestion(env):
    db, src = env
    f = src / "reglements/reglements_2025_08.csv"
    f.write_text("paiement_id,sinistre_id,date_paiement,montant,colonne_surprise\n1,1,2025-08-01,10,x\n")
    with pytest.raises(SystemExit):
        run(db, src, verbose=False)
    con = duckdb.connect(str(db), read_only=True)
    assert con.execute("SELECT COUNT(*) FROM ops.ingestion_log WHERE status='FAILED'").fetchone()[0] == 1


def test_source_absente_declenche_un_echec(tmp_path):
    """Une livraison manquante doit faire echouer le pipeline (et donc declencher l'alerte), pas passer en silence."""
    with pytest.raises(SystemExit):
        run(tmp_path / "t.duckdb", tmp_path / "vide", verbose=False)
