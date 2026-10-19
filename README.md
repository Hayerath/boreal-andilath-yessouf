# Boréal Assurances – entrepôt de données IARD (livrables 1 et 2)

Pipeline reproductible : sources → **brut** → **préparation** → **quarantaine** → **cœur** (étoile) → **marts**, en DuckDB (un seul fichier `data/boreal.duckdb`).

## Exécution en 5 commandes
```bash
python3 -m venv .venv && source .venv/bin/activate     # 1. environnement (Python 3.10+)
make install                                           # 2. dépendances
make load                                              # 3. chargement complet + 36 règles qualité + 28 tests bloquants
make test                                              # 4. preuves : rejeu, fichier livré 2 fois, rechargement d'un mois, test bloquant
make reload MONTH=2024_03                              # 5. rechargement d'un mois (ex. le fichier à l'en-tête atypique)
```
Les sources sont dans `data/sources/` (extraction du 30/06/2025). Relancer `make load` ne change jamais le résultat.

## Garanties
- **Brut = copie fidèle** : tout en texte, + fichier d'origine, empreinte, n° de ligne, date de chargement, run.
- **Idempotence** : fichier déjà chargé (même empreinte) ignoré ; `reload` remplace uniquement les lignes du fichier ; `core.fact_reglement` s'alimente en `INSERT … WHERE NOT EXISTS`.
- **Quarantaine** : aucune suppression ; `quarantine.rows` garde règle, motif et ligne complète (JSON).
- **Tests bloquants** : exécutés dans la transaction de transformation ; un échec fait `ROLLBACK` (le cœur garde son dernier état valide) et le code de sortie est 1.
- **Journal** : `ops.ingestion_log` (fichier, lignes lues / chargées / rejetées, durée, statut), `ops.pipeline_runs`, `ops.test_results`, `dq.rule_results`.

## Arborescence
`src/` ingestion, règles, tests, orchestration · `sql/` transformations par couche · `tests/` pytest · `docs/` architecture, modèle, règles (générées) · `analysis/` requêtes et scripts des livrables 3 et 4 · `app/dashboard.py` dashboard (livrable 5).

## Analyses (livrables 3 et 4) et dashboard (livrable 5)
```bash
python analysis/q.py analysis/etape1.sql      # fréquence : méthode naïve vs années-police
python analysis/q.py analysis/etape2.sql      # indicateurs par zone, formule, canal, âge
python analysis/q.py analysis/etape2c.sql     # payés, réserves, sans suite, rejetés
python analysis/q.py analysis/etape3.sql      # décomposition du ratio et contribution des segments
python analysis/etape4.py                     # intervalles de confiance, tests, queue des coûts (graine 42)
python analysis/etape5.py                     # rétention par cohorte, multi-détention
python analysis/etape6.py                     # valeur client, Pareto, profils
python analysis/etape7.py                     # délais de gestion, audits
python -m src.gen_catalogue                   # catalogue de données (docs/catalogue_donnees.md)
python scripts/orchestrate.py                 # lancement planifié : journal + alerte en cas d'échec
python -m streamlit run app/dashboard.py      # dashboard (lit uniquement marts.*)
```
Le dashboard ne lit que le schéma `marts`. Les mêmes marts alimentent les chiffres du dossier.
