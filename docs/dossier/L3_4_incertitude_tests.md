# L3 · 3.4 Incertitude, tests et queue de distribution

## Intervalles de confiance à 95 %

| Produit | Indicateur | Valeur | IC 95 % | Méthode |
|---|---|---|---|---|
| Auto | Fréquence | 0,0442 | 0,0415 - 0,0470 | Poisson exact |
| Auto | Coût moyen, 1129 inclus (EUR) | 7 191 | 4 271 - 12 481 | bootstrap, 3 000 tirages, graine 42 |
| Auto | Coût moyen, hors 1129 (EUR) | 4 782 | 4 140 - 5 522 | bootstrap |
| Auto | S/P | 0,539 | 0,317 - 0,947 | bootstrap sur contrats |
| Auto | Résiliations par année-police | 0,1467 | 0,1418 - 0,1517 | Poisson exact |
| Habitation | Fréquence | 0,0424 | 0,0397 - 0,0452 | Poisson exact |
| Habitation | Coût moyen (EUR) | 4 128 | 3 597 - 4 724 | bootstrap |
| Habitation | S/P | 0,610 | 0,526 - 0,710 | bootstrap sur contrats |
| Habitation | Résiliations par année-police | 0,1444 | 0,1394 - 0,1495 | Poisson exact |

Lecture :
- Les fréquences auto et habitation ont des intervalles qui se chevauchent : on ne peut pas dire que l'un des produits sinistre plus que l'autre.
- Le S/P auto (0,32 à 0,95) est beaucoup plus incertain que celui de l'habitation (0,53 à 0,71), à cause du sinistre 1129. Les deux intervalles se chevauchent : **on ne peut pas affirmer que l'auto est plus rentable que l'habitation**.
- Le bootstrap rééchantillonne les contrats (pas les sinistres), pour respecter la dépendance entre le coût et l'exposition d'un même contrat.

## Tests

| Question | Résultat | Conclusion |
|---|---|---|
| Fréquence habitation, zone 5 contre zone 1 | 0,0582 contre 0,0299, rapport 1,95, p = 6e-8 | Différence réelle : la zone 5 sinistre presque deux fois plus. Test exact binomial. |
| Coût auto, Agent contre Web | moyennes 10 897 contre 4 488, médianes 2 010 contre 2 127 ; Mann-Whitney p = 0,64 (0,60 hors 1129) | Aucune différence : l'écart des moyennes vient du seul sinistre 1129. |
| Résiliations, Web contre Agent | 0,185 contre 0,120, p = 8e-56 | Le Web résilie nettement plus (tous produits). |

Pourquoi Mann-Whitney : les coûts ont une queue très épaisse ; un test sur les moyennes (t de Welch) est
dominé par quelques valeurs extrêmes. Mann-Whitney compare les rangs et résiste à ce problème.

## Queue de distribution des coûts

| | Tous sinistres | Hors 1129 |
|---|---|---|
| Nombre | 1 957 | 1 956 |
| Médiane (EUR) | 1 814 | 1 814 |
| Moyenne (EUR) | 5 734 | 4 471 |
| 99e centile (EUR) | 42 752 | 41 820 |
| Maximum (EUR) | 2 475 975 | 200 291 |
| Part du total payé par les 1 % les plus chers | 34,9 % | 16,9 % |
| Part du total payé par les 10 % les plus chers | 62,9 % | 52,6 % |

La médiane (1 814 EUR) est trois fois plus basse que la moyenne : quelques gros sinistres portent
l'essentiel du coût. Même sans le 1129, 10 % des sinistres paient plus de la moitié du total.

## Phrases actionnables
- Piloter le coût avec la médiane et les gros sinistres plutôt qu'avec la moyenne seule.
- Le canal Web résilie 1,5 fois plus : c'est le levier de rétention le plus net.
- Une surprime de zone 5 en habitation est justifiée statistiquement (fréquence presque doublée).
