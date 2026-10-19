# L2 · 2.4 Tests automatisés

28 tests SQL (le sujet en demande au moins 8), exécutés à chaque lancement du pipeline.
Un test = une requête qui compte les violations ; **0 = succès**.

## Les tests sont bloquants
Les transformations et les tests s'exécutent dans une même transaction. Si un test échoue,
la transaction est annulée (ROLLBACK) : le cœur reste dans son dernier état valide, le
programme sort avec le code 1 et un message explicite. Un chiffre faux n'arrive donc
jamais jusqu'au tableau de bord. Ce comportement est lui-même testé (pytest : test_blocking_test_rollback).

## Les 5 familles

| Famille | Tests | Ce qu'on protège |
|---|---|---|
| Unicité des clés | T01 à T05 | pas de doublon (contrat, client, sinistre, paiement, grain d'exposition) |
| Intégrité référentielle | T06 à T09 | pas de contrat sans client, de sinistre sans contrat, de règlement sans sinistre, de date inconnue |
| Réconciliation | T11 à T15, T19 | brut = cœur + quarantaine : aucune ligne ne disparaît sans trace |
| Cohérence métier | T10, T16 à T18, T20, T21 | exposition bornée, alias valides, motif de quarantaine renseigné, prime acquise ≤ prime annuelle, texte correctement encodé |
| Cohérence des marts | M01 à M07 | chaque indicateur du tableau de bord retombe sur le cœur |

## Exemple de bug réel attrapé
Sous Windows, la lecture des fichiers SQL dans l'encodage par défaut produisait « RÃ©siliation »
dans les motifs de quarantaine. Correctif : lecture explicite en UTF-8, puis ajout de T21,
qui compte les caractères « Ã » dans les textes. Vérifié en le faisant échouer volontairement
sur une copie cassée (255 violations).

## Rejeu et idempotence (pytest, 7 tests)
Chargement initial, rejeu complet, rechargement d'un mois, fichier livré deux fois,
test bloquant avec annulation, dérive de schéma qui arrête l'ingestion, source absente qui fait échouer le passage.
