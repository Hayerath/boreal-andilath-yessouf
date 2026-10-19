# L3 · 3.2 Ratio sinistres / primes (S/P) par segment

## Définition
S/P = sinistres payés / primes acquises = fréquence × coût moyen / prime moyenne.
Cette identité permet de dire, pour chaque segment, si un écart vient du nombre de sinistres,
de leur coût ou du prix.

## Le sinistre n°1129
Un seul sinistre pèse 2 475 974,67 € : auto, zone 4, canal Agent, formule Confort,
conducteur 35-49 ans, survenu en 2023. Il apparaît dans quatre lignes du tableau des segments
auto et les fait toutes ressortir comme « dangereuses ».

| Segment auto | S/P avec 1129 | S/P hors 1129 (estimation) | Coût moyen avec -> hors |
|---|---|---|---|
| Zone 4 | 1,129 | 0,30 | 15 749 -> 4 198 |
| Âge 35-49 | 0,867 | 0,36 | 12 192 -> 5 073 |
| Canal Agent | 0,813 | 0,39 | 10 897 -> 5 165 |
| Formule Confort | 0,861 | 0,41 | 8 285 -> 3 933 |

(Estimation à partir du tableau en retirant ce sinistre ; le tableau de bord donne les valeurs exactes.)

Décision : le sinistre est **conservé dans tous les totaux** (c'est un vrai sinistre payé) et
toujours présenté avec le chiffre « hors 1129 » à côté.

## Effets qui ne dépendent pas du 1129
- Auto, moins de 25 ans : fréquence 0,0689 contre environ 0,040 pour les autres âges ; la prime
  est plus haute (758 €), mais le S/P reste correct (0,38).
- Auto, formule Essentielle : fréquence 0,0171, environ 3 fois plus faible que Confort (0,0611).
- Canal Web : résiliations de 0,1875 par année-police en auto contre environ 0,12 pour Agent et
  Courtier. Même constat en habitation (0,1824).
- Habitation : fréquence croissante avec la zone (0,0299 en zone 1, 0,0582 en zone 5), prime croissante aussi.

## Phrase actionnable
Aucun segment auto n'est structurellement déficitaire une fois le sinistre 1129 isolé ; avant
toute hausse de tarif en zone 4 ou chez les 35-49 ans, il faut traiter ce sinistre comme un
événement exceptionnel (réassurance, plafonnement) et non comme un signal de risque.
