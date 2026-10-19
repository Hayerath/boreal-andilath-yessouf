"""Paramètres communs du pipeline Boréal."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SQL_DIR = ROOT / "sql"
DEFAULT_SRC = ROOT / "data" / "sources"
DEFAULT_DB = ROOT / "data" / "boreal.duckdb"

# Date d'extraction des sources (incluse) et borne d'observation (exclue) :
# une couverture est observée jusqu'au 30/06/2025 inclus.
EXTRACT_DATE = "2025-06-30"
OBS_END = "2025-07-01"

# Schéma attendu de chaque source (noms de colonnes tels que livrés).
SCHEMAS = {
    "clients": ["client_id", "date_naissance", "region", "csp", "consent_marketing", "email_hash"],
    "contrats": ["contrat_id", "client_id", "produit", "date_effet", "date_resiliation", "formule",
                 "canal_distribution", "zone_risque", "franchise", "bonus_malus", "puissance_cv",
                 "surface_m2", "prime_annuelle"],
    "sinistres": ["sinistre_id", "contrat_id", "date_survenance", "date_declaration", "garantie",
                  "statut", "reserve_initiale"],
    # `montant_eur` : variante de nom rencontrée dans reglements_2024_03.csv
    "reglements": ["paiement_id", "sinistre_id", "date_paiement", "montant", "montant_eur"],
    "audits": ["sinistre_id", "date_audit", "fraude_confirmee"],
}
# Colonnes qui peuvent légitimement manquer d'un fichier à l'autre (une seule des deux est requise).
OPTIONAL = {"reglements": {"montant", "montant_eur"}}

PATTERNS = {
    "clients": "crm/clients.csv",
    "contrats": "contrats/contrats.csv",
    "sinistres": "sinistres/sinistres.jsonl",
    "reglements": "reglements/reglements_*.csv",
    "audits": "antifraude/audits.csv",
}
