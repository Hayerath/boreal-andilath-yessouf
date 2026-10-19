# Livrable 2 – Modèle dimensionnel

| Table | Type | Grain | Clé |
|---|---|---|---|
| `core.fact_exposition` | Fait | 1 contrat × 1 année civile avec couverture > 0 jour | (contrat_id, annee) |
| `core.fact_sinistre` | Fait | 1 sinistre déclaré (tous statuts) | sinistre_id |
| `core.fact_reglement` | Fait (incrémental) | 1 paiement | paiement_id |
| `core.fact_audit` | Fait | 1 audit (population auditée seulement) | sinistre_id |
| `core.dim_contrat` | Dimension | 1 contrat | contrat_id |
| `core.dim_client` | Dimension | 1 client unique, après fusion des doublons | client_id (+ valid_from) |
| `core.dim_segment_risque` | Dimension | produit × zone × formule × canal × tranche d'âge à la souscription | segment_sk |
| `core.dim_garantie` | Dimension | produit × garantie (VOL existe en auto et en habitation) | garantie_sk |
| `core.dim_date` | Dimension | 1 jour, 2020-2025 | date_key (AAAAMMJJ) |
| `core.client_alias` | Pont | 1 doublon → son survivant | client_id_doublon |

## Pourquoi ces grains
- **Exposition au grain contrat × année** : c'est le plus fin qui permet de rapprocher primes acquises et sinistres par année sans scinder artificiellement les contrats. Exposition = jours couverts / jours de l'année civile (1,0 = une année-police). Convention : effet inclus, résiliation exclue, observation jusqu'au 30/06/2025 inclus. 2025 n'a donc que six mois d'exposition.
- **Sinistre à son grain natif** : les rejetés et sans suite restent présents, distingués par statut, pour calculer fréquence avec suite et taux de rejet sans perdre de lignes.
- **Règlement à son grain natif** : les paiements sont immuables, donc `insert-only` avec `NOT EXISTS`.

## Historique des dimensions
- `dim_client` : colonnes `valid_from / valid_to / is_current` (SCD type 2 prêt). Le CRM ne livre qu'un instantané : une seule version existe aujourd'hui ; une région ou une CSP qui changerait créerait une nouvelle version, sans réécrire l'historique des faits.
- `dim_contrat` : SCD type 1. Les attributs contractuels sont figés dans la source ; un avenant serait un nouveau contrat.
- Le segment de risque est calculé à la **souscription** (âge à l'effet) pour qu'un contrat ne change pas de segment au fil des années.

## Déduplication des clients
Clé : `email_hash` (même adresse = même personne). Elle est validée par la règle U06 : sur les 200 paires, date de naissance et région concordent à 100 %. Survivant : plus petit `client_id`. Les 200 doublons ont des identifiants supérieurs à 15 000 et n'ont aucun contrat ; la règle prévoit néanmoins la bascule des contrats via `core.client_alias`. Taux de doublons : 200 / 15 200 = 1,3 %.
