# L5 · Orchestration mensuelle

## Principe
Le pipeline est lancé par un planificateur (cron sous Linux, Planificateur de tâches sous Windows) avec une seule commande :

```
python scripts/orchestrate.py
```

Il est **sûr de le lancer souvent** : chaque fichier a une empreinte (SHA-256), un fichier déjà chargé et inchangé est ignoré
(SKIPPED_UNCHANGED). Sans nouveau fichier, le passage ne change rien (rejeu mesuré : 3,1 s). Un nouveau mois de règlements, livré en
`reglements_AAAA_MM.csv`, est détecté par son nom et sa nouvelle empreinte, puis chargé sans toucher aux mois précédents (insertion
`NOT EXISTS` sur `paiement_id`).

## Déclenchement
| Besoin | Réalisation |
|---|---|
| Traiter un nouveau mois dès son arrivée | planificateur lancé chaque jour (ou chaque heure) ; sans nouveau fichier, rien ne change |
| Recharger un mois corrigé | `python scripts/orchestrate.py --reload 2024_03` |
| Rejouer tout depuis le brut | `python -m src.pipeline run` (idempotent) |

## Journal et alerte
- Chaque passage écrit `logs/pipeline_AAAAMMJJ_HHMMSS.log` et ses résultats dans `ops.pipeline_runs`, `ops.ingestion_log` et `ops.test_results`
  (visibles dans la page Exploitation du tableau de bord).
- Tout échec rend un code de sortie non nul : fichier illisible, colonnes modifiées dans une source, **source absente**, test bloquant.
  Le script écrit alors `logs/ALERTE.txt` et, si la variable `BOREAL_ALERT_WEBHOOK` est définie, envoie le message à cette adresse
  (messagerie d'équipe). L'alerte disparaît dès qu'un passage réussit.
- Dans tous les cas d'échec, **le cœur reste dans son dernier état valide** : les transformations et les tests s'exécutent dans une
  transaction annulée en cas d'erreur.

## Ce qui est démontré, et ce qui reste à brancher
Démontré et testé : le rejeu, la double livraison, le rechargement d'un mois, le test bloquant avec annulation, l'arrêt sur changement de
schéma, l'arrêt quand une source manque (7 tests pytest), et le script d'alerte (échec simulé, puis retour à la normale).
À brancher en production : le planificateur lui-même et l'adresse de la messagerie d'équipe ; ce sont des réglages de l'environnement,
pas du code.
