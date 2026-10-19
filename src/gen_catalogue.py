"""Genere docs/catalogue_donnees.md : toutes les tables et colonnes de l'entrepot, avec type et description.

Usage : python -m src.gen_catalogue
Les descriptions sont dans ce fichier ; une colonne sans description est signalee 'A DOCUMENTER'
(et le script le dit), de sorte que le catalogue ne peut pas devenir incomplet sans que ca se voie.
"""
import duckdb
from .config import DEFAULT_DB, ROOT

SCHEMAS = [
    ("raw", "Copie fidèle des fichiers sources, plus 6 colonnes techniques. Rien n'est corrigé."),
    ("prep", "Préparation : typage, dates normalisées, clés de dédoublonnage. Intermédiaire."),
    ("quarantine", "Lignes écartées des calculs, avec la règle et le motif. Rien n'est supprimé."),
    ("core", "Modèle dimensionnel (étoile) : dimensions et faits utilisés pour tous les calculs."),
    ("marts", "Tables prêtes pour le tableau de bord. Le tableau de bord ne lit que ce schéma."),
    ("ops", "Journal d'exploitation : chargements, exécutions, résultats des tests."),
    ("dq", "Résultats des règles de qualité des données."),
]

TABLES = {
    "raw.clients": "Clients tels que livrés par le CRM (un client peut apparaître en doublon).",
    "raw.contrats": "Contrats tels que livrés.",
    "raw.sinistres": "Sinistres tels que livrés (JSON lignes).",
    "raw.reglements": "Paiements, un fichier par mois ; le nom du montant varie selon le fichier.",
    "raw.audits": "Audits antifraude tels que livrés.",
    "prep.clients": "Clients typés avec clé de doublon et survivant.",
    "prep.contrats": "Contrats typés.",
    "prep.sinistres": "Sinistres typés.",
    "prep.reglements": "Paiements typés avec rang d'occurrence (détection des doublons).",
    "prep.audits": "Audits typés.",
    "prep.contrats_ok": "Contrats qui passent les règles bloquantes (vue).",
    "prep.sinistres_ok": "Sinistres qui passent les règles bloquantes (vue).",
    "prep.reglements_ok": "Paiements qui passent les règles bloquantes (vue).",
    "prep.audits_ok": "Audits qui passent les règles bloquantes (vue).",
    "quarantine.rows": "Une ligne par enregistrement écarté : règle, entité, clé, fichier, motif, ligne d'origine en JSON.",
    "quarantine.raw_rejects": "Lignes illisibles dès la lecture du fichier (format cassé).",
    "core.client_alias": "Table de passage doublon -> client survivant.",
    "core.dim_client": "Dimension client dédoublonnée, prête pour l'historisation SCD2.",
    "core.dim_contrat": "Dimension contrat (SCD1) : caractéristiques et dates de vie du contrat.",
    "core.dim_date": "Calendrier, clé entière AAAAMMJJ.",
    "core.dim_garantie": "Garanties par produit.",
    "core.dim_segment_risque": "Segment de risque figé à la souscription (produit, zone, formule, canal, tranche d'âge).",
    "core.fact_exposition": "Grain : un contrat par année civile. Jours couverts, année-police, prime acquise.",
    "core.fact_sinistre": "Grain : un sinistre. Dates, statut, réserve, règlements cumulés.",
    "core.fact_reglement": "Grain : un paiement. Chargée de façon incrémentale, jamais modifiée.",
    "core.fact_audit": "Grain : un sinistre audité, avec le résultat de l'audit.",
    "marts.portefeuille_annee_produit": "Indicateurs annuels par produit : exposition, primes, sinistres, fréquence, coût, S/P.",
    "marts.portefeuille_mois": "Indicateurs mensuels par produit, zone, canal, région.",
    "marts.technique_segment": "Indicateurs techniques par année et segment de risque.",
    "marts.decomposition_annuelle": "Décomposition de la variation annuelle du ratio S/P (fréquence, coût, prime).",
    "marts.contribution_segment": "Contribution de chaque segment à la variation du ratio global.",
    "marts.retention_cohorte": "Rétention des contrats par cohorte et anniversaire observable.",
    "marts.valeur_client": "Une ligne par client : primes acquises, sinistres payés, valeur. Niveau individuel.",
    "marts.pareto_valeur": "Courbe de concentration de la valeur client.",
    "marts.profil_decile": "Profil moyen de chaque décile de valeur client.",
    "marts.delais_garantie": "Délais de déclaration, de règlement et de clôture par garantie.",
    "marts.audit_critere": "Résultats d'audit par critère (garantie, produit, tranche de réserve...).",
    "marts.ops_chargement_source": "Vue : lignes lues, chargées, rejetées par source.",
    "marts.ops_fraicheur": "Vue : date métier la plus récente par source.",
    "marts.ops_regles_qualite": "Vue : règles de qualité et nombre d'anomalies.",
    "marts.ops_rejets_regle": "Vue : nombre de lignes en quarantaine par règle.",
    "marts.ops_runs": "Vue : historique des exécutions du pipeline.",
    "marts.ops_tests": "Vue : résultat des tests du dernier passage.",
    "ops.ingestion_log": "Un enregistrement par fichier chargé : empreinte, lignes lues, chargées, rejetées, statut.",
    "ops.pipeline_runs": "Une ligne par exécution du pipeline.",
    "ops.test_results": "Résultat de chaque test à chaque exécution.",
    "dq.rule_results": "Mesure de chaque règle de qualité à chaque exécution.",
}

# Descriptions de colonnes (par nom ; valables pour toutes les tables où le nom apparaît)
COLS = {
 # techniques
 "_source_file": "Fichier d'origine de la ligne", "_file_hash": "Empreinte SHA-256 du fichier (détecte un fichier modifié)",
 "_row_num": "Numéro de ligne dans le fichier", "_loaded_at": "Horodatage du chargement", "_run_id": "Exécution qui a chargé la ligne",
 "_encoding": "Encodage détecté (UTF-8 ou latin-1)",
 # clés et clients
 "client_id": "Identifiant client", "client_id_doublon": "Identifiant du client fusionné", "client_id_survivant": "Identifiant du client conservé",
 "date_naissance": "Date de naissance (donnée personnelle)", "date_naissance_raw": "Date de naissance telle que livrée",
 "region": "Région du client", "csp": "Catégorie socioprofessionnelle", "consent_marketing": "Consentement à la prospection",
 "email_hash": "Empreinte de l'e-mail (pseudonyme, clé de dédoublonnage)", "rang_email": "Rang du client parmi ceux de même e-mail",
 "valid_from": "Début de validité de la version (SCD2)", "valid_to": "Fin de validité de la version (SCD2)", "is_current": "Version en vigueur",
 # contrat
 "contrat_id": "Identifiant contrat", "produit": "Produit : AUTO ou HABITATION", "formule": "Formule : ESSENTIELLE, CONFORT, PREMIUM",
 "canal_distribution": "Canal : AGENT, COURTIER, WEB", "canal": "Canal de distribution", "zone_risque": "Zone de risque de 1 à 5",
 "franchise": "Franchise du contrat", "bonus_malus": "Coefficient bonus-malus (auto)", "puissance_cv": "Puissance fiscale (auto)",
 "surface_m2": "Surface du logement (habitation)", "prime_annuelle": "Prime annuelle du contrat",
 "tranche_age": "Tranche d'âge du souscripteur à la souscription", "date_effet": "Date d'effet du contrat", "date_effet_raw": "Date d'effet telle que livrée",
 "date_resiliation": "Date de résiliation (vide si en vigueur)", "date_effet_key": "Clé de date de l'effet", "date_resiliation_key": "Clé de date de résiliation",
 "est_resilie": "Contrat résilié", "segment_sk": "Clé du segment de risque",
 # dates
 "date_key": "Clé de date AAAAMMJJ", "date": "Date", "annee": "Année civile", "mois": "Mois", "trimestre": "Trimestre", "annee_mois": "Année et mois (AAAA-MM)",
 "debut_mois": "Premier jour du mois", "est_futur": "Date postérieure à l'extraction",
 # garantie
 "garantie_sk": "Clé de la garantie", "garantie_code": "Code de la garantie", "libelle": "Libellé de la garantie", "garantie": "Garantie du sinistre",
 # exposition
 "date_debut": "Début de couverture dans l'année", "date_fin_exclue": "Fin de couverture (exclue)", "jours_couverture": "Jours couverts dans l'année",
 "jours_annee": "Jours de l'année", "exposition_annee_police": "Année-police : jours couverts / jours de l'année", "prime_acquise": "Prime acquise : prime annuelle x année-police",
 # sinistre
 "sinistre_id": "Identifiant sinistre", "date_survenance": "Date de survenance", "date_declaration": "Date de déclaration", "statut": "Statut : CLOTURE, OUVERT, SANS_SUITE, REJETE",
 "reserve_initiale": "Réserve initiale du dossier", "date_survenance_key": "Clé de date de survenance", "date_declaration_key": "Clé de date de déclaration",
 "annee_survenance": "Année de survenance", "delai_declaration_j": "Délai de déclaration en jours",
 "anomalie_declaration_avant_survenance": "Déclaration antérieure à la survenance", "anomalie_hors_couverture": "Survenance hors période de couverture",
 "nb_reglements": "Nombre de règlements", "montant_regle": "Montant payé cumulé", "date_premier_reglement": "Date du premier paiement", "date_dernier_reglement": "Date du dernier paiement",
 # reglement
 "paiement_id": "Identifiant paiement", "date_paiement": "Date du paiement", "montant": "Montant du paiement", "montant_eur": "Montant du paiement (variante de nom de colonne)",
 "source_file": "Fichier d'origine", "loaded_at": "Horodatage du chargement", "rang_occ": "Rang d'occurrence du paiement (doublons)",
 "mois_fichier": "Mois du fichier", "mois_paiement": "Mois du paiement",
 # audit
 "date_audit": "Date de l'audit", "date_audit_key": "Clé de date de l'audit", "fraude_confirmee": "Fraude confirmée par l'audit",
 # quarantaine
 "rule_id": "Identifiant de la règle", "entity": "Entité concernée", "record_key": "Clé de l'enregistrement écarté", "motif": "Motif de l'écart", "payload": "Ligne d'origine en JSON",
 "source": "Source de données", "row_num": "Numéro de ligne", "raw_line": "Ligne brute illisible", "run_id": "Identifiant d'exécution",
 # ops / dq
 "file": "Nom du fichier", "file_hash": "Empreinte du fichier", "rows_read": "Lignes lues", "rows_loaded": "Lignes chargées", "rows_rejected": "Lignes rejetées",
 "duration_s": "Durée en secondes", "status": "Statut", "message": "Message", "logged_at": "Horodatage", "started_at": "Début", "finished_at": "Fin",
 "n_tests": "Nombre de tests", "n_tests_failed": "Tests en échec", "test_id": "Identifiant du test", "description": "Description", "violations": "Nombre de violations",
 "executed_at": "Horodatage d'exécution", "dimension": "Dimension de qualité", "severity": "Gravité", "treatment": "Traitement appliqué", "volume": "Nombre de lignes concernées",
 "query": "Requête de mesure", "computed_at": "Horodatage du calcul",
 "fichiers": "Nombre de fichiers", "lignes_lues": "Lignes lues", "lignes_chargees": "Lignes chargées", "lignes_rejetees_lecture": "Lignes rejetées à la lecture",
 "dernier_chargement": "Dernier chargement", "fichiers_en_echec": "Fichiers en échec", "derniere_date_metier": "Date métier la plus récente", "date_extraction": "Date d'extraction",
 "lignes": "Nombre de lignes", "exemple_motif": "Exemple de motif",
 # marts
 "mois_num": "Numéro du mois", "perimetre": "Périmètre : tous les sinistres ou hors sinistre extrême", "exposition": "Années-police", "contrats_exposes": "Contrats exposés",
 "contrats_actifs_fin_mois": "Contrats actifs en fin de mois", "nouveaux_contrats": "Contrats souscrits", "resiliations": "Contrats résiliés",
 "sinistres_declares": "Sinistres déclarés", "sinistres_avec_suite": "Sinistres CLOTURE ou OUVERT", "sinistres_sans_suite": "Sinistres sans suite", "sinistres_rejetes": "Sinistres rejetés",
 "sinistres_extremes": "Sinistres extrêmes (cumul payé > 500 000 EUR)", "paye": "Sinistres payés", "paye_hors_extreme": "Sinistres payés hors sinistre extrême",
 "frequence_par_annee_police": "Sinistres avec suite / année-police", "cout_moyen_par_sinistre": "Payé / sinistres avec suite", "ratio_sinistres_primes": "Payé / primes acquises",
 "frequence": "Fréquence", "cout_moyen": "Coût moyen", "prime_moyenne": "Prime moyenne", "ratio": "Ratio sinistres / primes",
 "var_ratio_log": "Variation du ratio (logarithme)", "effet_frequence": "Part due à la fréquence", "effet_cout": "Part due au coût moyen", "effet_prime": "Part due à la prime",
 "variation_volume_log": "Variation du volume (information)", "statut_annee": "Année complète, partielle ou de démarrage",
 "poids_avant": "Poids du segment, année précédente", "poids_apres": "Poids du segment, année courante", "ratio_avant": "Ratio du segment, année précédente", "ratio_apres": "Ratio du segment, année courante",
 "contribution": "Contribution à la variation du ratio global (points)", "reserve_residuelle_ouverts": "Réserve restante des dossiers ouverts",
 "cohorte": "Année de souscription", "annee_anniversaire": "Rang de l'anniversaire", "contrats_eligibles": "Contrats ayant atteint l'anniversaire", "contrats_retenus": "Contrats encore en vigueur", "retention": "Part retenue",
 "nb_contrats": "Nombre de contrats", "nb_produits": "Nombre de produits détenus", "nb_sinistres": "Sinistres avec suite", "client_sinistre_extreme": "Client portant un sinistre extrême", "valeur": "Primes acquises - sinistres payés",
 "pct_clients": "Part des clients, du plus au moins rentable", "valeur_cumulee": "Valeur cumulée", "part_cumulee_valeur": "Part cumulée de la valeur nette",
 "decile": "Décile de valeur (1 = plus rentable)", "clients": "Nombre de clients", "exposition_moy": "Exposition moyenne", "valeur_par_annee_police_moy": "Valeur moyenne par année-police",
 "valeur_moy": "Valeur moyenne", "prime_moy": "Prime acquise moyenne", "paye_moy": "Payé moyen", "sinistres_moy": "Sinistres moyens", "contrats_moy": "Contrats moyens", "part_multi_detenteurs": "Part de clients à deux produits",
 "etape": "Étape mesurée du délai", "n": "Effectif", "mediane": "Médiane (jours)", "q75": "75e centile", "q90": "90e centile", "q95": "95e centile", "maximum": "Maximum",
 "critere": "Critère d'analyse", "modalite": "Modalité du critère", "sinistres": "Sinistres", "audites": "Sinistres audités", "fraudes_confirmees": "Fraudes confirmées",
 "taux_confirmation": "Fraudes confirmées / audités (population auditée seulement)", "couverture_audit": "Audités / sinistres",
}


def main():
    con = duckdb.connect(str(DEFAULT_DB), read_only=True)
    manque = []
    out = ["# Catalogue de données\n",
           "Généré par `python -m src.gen_catalogue` à partir de l'entrepôt. Toute table ou colonne y figure.\n"]
    for schema, desc in SCHEMAS:
        out.append(f"\n## Schéma `{schema}`\n\n{desc}\n")
        tabs = con.execute("SELECT table_name, table_type FROM information_schema.tables WHERE table_schema=? ORDER BY 1", [schema]).fetchall()
        for t, ttype in tabs:
            full = f"{schema}.{t}"
            n = con.execute(f"SELECT COUNT(*) FROM {full}").fetchone()[0]
            d = TABLES.get(full)
            if not d:
                d = "A DOCUMENTER"; manque.append(full)
            out.append(f"\n### `{full}`{' (vue)' if ttype == 'VIEW' else ''}\n\n{d} Lignes : {n:,}.\n".replace(",", " "))
            out.append("\n| Colonne | Type | Description |\n|---|---|---|")
            for c, ty in con.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema=? AND table_name=? ORDER BY ordinal_position", [schema, t]).fetchall():
                cd = COLS.get(c)
                if not cd:
                    cd = "A DOCUMENTER"; manque.append(f"{full}.{c}")
                out.append(f"| `{c}` | {ty} | {cd} |")
    (ROOT / "docs" / "catalogue_donnees.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"catalogue ecrit : docs/catalogue_donnees.md ; elements sans description : {len(manque)}")
    for m in manque:
        print("  A DOCUMENTER :", m)


if __name__ == "__main__":
    main()
