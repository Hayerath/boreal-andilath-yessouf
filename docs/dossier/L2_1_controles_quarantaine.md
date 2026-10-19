# Livrable 2 · 2.1 Contrôles et quarantaine

## Vue d'ensemble
36 règles de qualité, réparties sur les cinq dimensions demandées, ont été mesurées sur la couche préparation, avant tout traitement. **14 révèlent une anomalie, 22 sont à zéro** : ces dernières prouvent que le contrôle a été fait (par exemple : aucun orphelin entre tables, aucun doublon de contrat, aucun règlement sur un sinistre rejeté). Les requêtes de chaque règle sont dans `docs/regles_qualite.md`, générées depuis l'entrepôt.

| Dimension | Règles | Avec anomalie |
|---|---:|---:|
| Complétude | 4 | 1 |
| Unicité | 6 | 2 |
| Validité | 9 | 4 |
| Cohérence entre tables | 4 | 0 |
| Cohérence métier | 4 | 1 |
| Cohérence temporelle | 9 | 6 |

## Les 14 anomalies, leur traitement et sa justification

| Règle | Anomalie | Volume | Gravité | Traitement | Justification chiffrée |
|---|---|---:|---|---|---|
| U04 | Paiement livré deux fois (re-livraison) | 32 | Majeure | **Exclure** la re-livraison, garder la première, tracer en quarantaine | Évite de compter deux fois 73 150 € (0,65 % du payé total) |
| U02 | Client présent deux fois (même `email_hash`) | 200 | Majeure | **Fusionner** : garder le plus petit `client_id`, alias conservés | 1,3 % des clients ; voir 2.2 |
| V03 | Prime annuelle nulle ou négative (11 à 0 €, 14 à −50 €) | 25 | Bloquante | **Exclure** (quarantaine) | Une prime négative fausserait primes acquises et ratio ; 0,12 % des contrats |
| T01 | Résiliation antérieure à l'effet | 20 | Bloquante | **Exclure** (quarantaine) | Exposition négative impossible ; 0,10 % des contrats |
| P01 / P02 | Sinistres (5) et règlement (1) rattachés à un contrat en quarantaine | 6 | Bloquante | **Exclure** en cascade | 5 sinistres (4 536 € de réserve) et 1 règlement de 684,32 € |
| C01 | Date de naissance manquante | 226 | Mineure | **Signaler** ; tranche d'âge `INCONNU` | Reste utilisable : seul l'axe « âge » est touché |
| V01 | Date de naissance factice (01/01/1890) | 18 | Mineure | **Corriger** : mise à NULL | Une date à 135 ans fausserait la tranche d'âge |
| V02 | Titulaire mineur à l'extraction | 22 | Mineure | **Signaler** | 22 clients mineurs ont des contrats : à faire confirmer par le client |
| T02 | Résiliation le jour de l'effet | 6 | Mineure | **Signaler** | Aucune exposition générée, le contrat reste dans la dimension |
| T03 | Déclaration antérieure à la survenance | 15 | Majeure | **Signaler** ; délai non calculé | 229 228 € payés : le sinistre existe, on ne l'exclut pas |
| T04 / T05 | Survenance avant l'effet (17) ou après la résiliation (1) | 18 | Majeure | **Signaler** par un drapeau | 17 sinistres dans le cœur, 44 341 € payés ; décision de couverture = décision métier |
| T08 | Fichier mensuel contenant un paiement d'un autre mois | 32 | Mineure | **Signaler** | Ce sont les mêmes lignes que U04 |
| K03 | Audit sur un sinistre ouvert ou sans suite | 36 | Mineure | **Signaler** ; population précisée dans l'analyse | Les taux de confirmation ne valent que pour les audités |
| V07 | Sinistre dont le cumul payé dépasse 500 000 € | 1 | Majeure | **Signaler**, conserver | Sinistre n° 1129 : 2 475 975 € ; analysé avec et sans |

## Quarantaine
283 lignes sont écartées du cœur et conservées dans `quarantine.rows`, avec leur règle, leur motif et la ligne source complète (JSON) : 200 clients (U02), 32 règlements (U04), 25 contrats (V03), 20 contrats (T01), 5 sinistres (P01) et 1 règlement (P02). Aucune ligne n'est supprimée : le test de réconciliation montre que lignes du brut = lignes du cœur + lignes en quarantaine, pour chaque table.

## Pourquoi ces choix de traitement
- **Exclure** quand la ligne rendrait un indicateur faux : prime négative, dates impossibles, doublon qui double un montant.
- **Corriger** seulement quand la valeur est manifestement factice (date de 1890), jamais en inventant une valeur.
- **Signaler** quand la donnée est suspecte mais exploitable, et laisser la décision au métier (sinistre hors période de couverture, mineur titulaire).
