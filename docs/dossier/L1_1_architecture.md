# Livrable 1 · 1.1 Architecture cible

## Chaîne de bout en bout

Sources (5 systèmes, 68 fichiers, 41 848 lignes) → **raw** (copie fidèle) → **prep** (typage, normalisation) → **quarantine** (lignes écartées + motif) et **core** (schéma en étoile) → **marts** (agrégats métier) → **dashboard**. Deux schémas transverses : **ops** (journal d'ingestion, exécutions, tests) et **dq** (règles de qualité).

Aucune transformation n'a lieu dans la couche brute. Les écarts entre le brut et le cœur sont toujours expliqués par la quarantaine.

## Choix d'outils, justifiés par des critères mesurés

| Brique | Choix | Critère mesuré dans ce projet | Alternative écartée |
|---|---|---|---|
| Stockage et SQL | DuckDB | 41 848 lignes (2,6 Mo) ; entrepôt de 24,9 Mo ; chargement complet + 36 règles + 28 tests en 10,6 s ; rejeu en 3,1 s ; aucun serveur ; SQL analytique complet | PostgreSQL : serveur et droits à administrer, sans gain à ce volume |
| Ingestion | Python (csv, json, pandas) | 3 formats (CSV virgule UTF-8, CSV point-virgule latin-1, JSONL) ; 1 fichier de règlements sur 64 avec un en-tête différent (`montant_eur`) ; lecture par nom de colonne | `COPY` SQL seul : ne tolère pas les en-têtes variables |
| Transformations | SQL versionné, un fichier par couche | 4 fichiers lisibles par un analyste ; rejouables | dbt : surdimensionné pour 5 sources et une équipe |
| Orchestration | Makefile, puis planification mensuelle | 1 commande ; aucune dépendance | Airflow : coût d'exploitation disproportionné |
| Restitution | Streamlit sur les marts | Lit uniquement `marts.*` ; page chargée en environ 1 s | Power BI / Tableau : licence, et dashboard non versionnable avec le code |

## Avec 100 fois plus de données

Environ 4,2 millions de lignes et 260 Mo de CSV ; entrepôt de l'ordre de 2,5 Go (extrapolation linéaire). DuckDB tiendrait encore sur une machine. Ce qui changerait :
- **Ingestion** : le chargement ligne à ligne en pandas deviendrait le point de rupture. On passerait à la lecture native `read_csv` de DuckDB, ou à des fichiers Parquet partitionnés par mois.
- **Cœur** : les dimensions, reconstruites en entier à chaque lancement, passeraient en `MERGE` incrémental ; les règlements resteraient en insertion seule par mois.
- **Exploitation** : si plusieurs équipes écrivent en parallèle, PostgreSQL ou un entrepôt cloud ; dbt pour les tests et le lignage ; Airflow ou Dagster pour planifier. Le modèle en couches ne change pas.
