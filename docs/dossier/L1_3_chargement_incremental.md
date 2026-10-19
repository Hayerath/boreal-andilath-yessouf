# Livrable 1 · 1.3 Chargement incrémental

## Le journal d'ingestion
Chaque passage sur un fichier écrit une ligne dans `ops.ingestion_log` : source, fichier, empreinte, lignes lues, chargées et rejetées, durée, statut (`LOADED`, `SKIPPED_UNCHANGED` ou `FAILED`), message et heure. Chaque lancement complet écrit aussi une ligne dans `ops.pipeline_runs` (statut `SUCCES`, `ECHEC_INGESTION` ou `ECHEC_TESTS`, nombre de tests réussis).

## Trois niveaux d'idempotence
1. **Fichier inchangé** : si l'empreinte SHA-256 du fichier est déjà dans le brut, il est ignoré (`SKIPPED_UNCHANGED`). Relancer `python -m src.pipeline run` donne « 0 fichier chargé, 68 inchangés ».
2. **Rechargement d'un mois** : `python -m src.pipeline reload --month 2024_03` supprime puis réinsère uniquement les lignes de ce fichier, dans une transaction. Si le chargement échoue, `ROLLBACK` : l'ancien contenu reste intact.
3. **Cœur** : `core.fact_reglement` est alimentée par `INSERT … WHERE NOT EXISTS (SELECT 1 … WHERE paiement_id = …)`.

## Interprétation obligatoire de la requête `NOT EXISTS`
Au **premier passage**, aucun `paiement_id` n'existe dans la table : tous les paiements de la préparation sont insérés (3 174). Au **second passage**, chaque `paiement_id` y est déjà : le `NOT EXISTS` est faux pour toutes les lignes, la requête insère 0 ligne, et le résultat est identique. Une re-livraison d'un paiement déjà chargé n'est donc jamais comptée deux fois. Elle reste visible dans la quarantaine (règle U04) : c'est ce qui permet de réconcilier le brut avec le cœur.

## Preuve
- **Test automatisé** (`tests/test_pipeline.py`) : rejeu complet deux fois, rechargement des mois `2024_03` et `2023_06`, et fichier livré en double (une copie de `reglements_2023_06.csv`). Dans tous les cas : même nombre de paiements, même montant total, mêmes identifiants (empreinte). Pour le fichier livré en double, le brut garde toutes les lignes (copie fidèle) et la quarantaine trace chaque ligne re-livrée.
- **Démonstration en direct** : `python analysis/demo_rechargement.py 2024_03` affiche avant et après : 3 174 paiements, 3 174 identifiants uniques, montant total 11 221 001,06 EUR, même empreinte d'identifiants.
- **Test bloquant** : un test en échec annule les transformations (`ROLLBACK`) et le cœur reste dans son dernier état valide (test `test_test_bloquant_annule_les_transformations`).
