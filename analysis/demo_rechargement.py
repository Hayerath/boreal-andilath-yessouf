"""Démonstration de soutenance : rejouer un mois ne crée aucun doublon.
Usage : python analysis/demo_rechargement.py [AAAA_MM]     (défaut : 2024_03, le fichier à l'en-tête atypique)"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import duckdb

from src.config import DEFAULT_DB
from src.pipeline import run

mois = sys.argv[1] if len(sys.argv) > 1 else "2024_03"


def etat():
    con = duckdb.connect(str(DEFAULT_DB), read_only=True)
    r = con.execute("""SELECT COUNT(*), COUNT(DISTINCT paiement_id), ROUND(SUM(montant), 2),
                       hash(list(paiement_id ORDER BY paiement_id)) FROM core.fact_reglement""").fetchone()
    n_mois = con.execute("SELECT COUNT(*) FROM core.fact_reglement WHERE source_file LIKE ?", [f"%{mois}%"]).fetchone()[0]
    raw = con.execute("SELECT COUNT(*) FROM raw.reglements WHERE _source_file LIKE ?", [f"%{mois}%"]).fetchone()[0]
    con.close()
    return dict(lignes=r[0], ids_uniques=r[1], montant_total=r[2], empreinte_ids=r[3], dans_cœur_pour_ce_mois=n_mois, dans_brut_pour_ce_mois=raw)


print(f"=== AVANT le rechargement du mois {mois} ===")
avant = etat()
for k, v in avant.items():
    print(f"  {k:26s} {v}")
print(f"\n=== Rechargement forcé du mois {mois} (puis transformations et 27 tests) ===")
run(DEFAULT_DB, reload_month=mois, verbose=True)
print(f"\n=== APRÈS ===")
apres = etat()
for k, v in apres.items():
    print(f"  {k:26s} {v}")
print("\nRésultat :", "IDENTIQUE : aucun doublon, mêmes montants, mêmes identifiants" if avant == apres else "ECART DETECTE", "\n")
con = duckdb.connect(str(DEFAULT_DB), read_only=True)
print("Journal d'ingestion (derniers passages sur ce fichier) :")
print(con.execute("""SELECT status, rows_read AS lues, rows_loaded AS chargees, rows_rejected AS rejetees, message,
                     STRFTIME(logged_at, '%H:%M:%S') AS heure FROM ops.ingestion_log WHERE file LIKE ? ORDER BY logged_at""",
                  [f"%{mois}%"]).df().to_string(index=False))