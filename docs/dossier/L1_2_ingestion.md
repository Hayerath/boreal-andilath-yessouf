# Livrable 1 · 1.2 Ingestion des sources

## Ce que contiennent les sources

| Source | Fichiers | Format constaté | Particularité traitée |
|---|---|---|---|
| CRM `clients` | 1 | CSV, séparateur `;`, dates `jj/mm/aaaa` | Annoncé en latin-1 ; le contenu est entièrement ASCII (0 octet accentué), donc lisible dans les deux encodages |
| `contrats` | 1 | CSV, séparateur `,`, dates ISO | Champs propres au produit vides selon AUTO / HABITATION |
| `sinistres` | 1 | JSON Lines, un objet par ligne | Types JSON (nombres) lus en texte dans le brut |
| `reglements` | 64 | 64 CSV mensuels, `,` | 1 fichier (`2024_03`) a un en-tête et un ordre de colonnes différents (`montant_eur` en première colonne) ; 1 fichier (`2025_07`) postérieur à l'extraction du 30/06/2025 |
| `audits` | 1 | CSV | Population auditée seulement |

## Méthode

- **Brut = copie fidèle.** Toutes les colonnes sont stockées en texte, sans typage ni correction. Chaque ligne garde six champs de traçabilité : `_source_file`, `_file_hash` (SHA-256 du fichier), `_row_num`, `_loaded_at`, `_run_id`, `_encoding`.
- **Les différences de format sont absorbées sans intervention manuelle** :
  - séparateur détecté sur l'en-tête (`;` ou `,`) ;
  - encodage : UTF-8 d'abord, repli sur latin-1, résultat enregistré dans `_encoding` ;
  - colonnes lues **par nom** et non par position : c'est ce qui rend le fichier `2024_03` lisible. Lues par position, ses montants auraient été chargés dans la colonne des identifiants.
- **Protections** : une colonne inconnue (dérive de schéma) ou manquante arrête le chargement du fichier, qui est tracé `FAILED` au journal. Une ligne illisible va en `quarantine.raw_rejects`. Sur ces données, 0 ligne est illisible.
- **Résultat** : 41 848 lignes dans le brut (15 200 clients, 20 264 contrats, 2 805 sinistres, 3 207 lignes de règlements, 372 audits). Les 3 207 lignes de règlements contiennent 32 re-livraisons, soit 3 175 paiements uniques.

## Démonstration
`python -m src.pipeline run`, puis relancer : « 0 fichier chargé, 68 inchangés ».
