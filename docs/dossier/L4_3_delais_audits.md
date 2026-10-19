# L4 · 4.3 Délais de traitement et audits antifraude

## A. Délais (en jours), par garantie
Trois délais, chacun sur sa propre population :

| Délai | Population | Médiane | 95e centile |
|---|---|---|---|
| Survenance -> déclaration | sinistres dont la déclaration n'est pas antérieure à la survenance | 4 à 6 j | 22 à 39 j |
| Déclaration -> 1er règlement | sinistres avec au moins un règlement | 45 à 54 j | 120 à 175 j |
| Déclaration -> dernier règlement (clôture approximée) | 1 785 sinistres CLOTURE avec règlement | 71 à 92 j | 189 à 269 j |

Les garanties se ressemblent : aucune ne se détache nettement. La tempête en habitation a le 1er règlement le
plus tardif (médiane 53,5 j, 95e centile 175 j), mais sur 114 dossiers seulement.

Limites :
- La date de clôture n'existe pas dans la source ; elle est approximée par le dernier règlement.
- Les sinistres OUVERT sont exclus du délai de clôture (leur délai n'est pas terminé), ce qui le sous-estime.
- Sinistres encore ouverts : 154 de 2025 (dont 98 sans aucun paiement) et 18 de 2024 (dont 2 sans paiement).
  Leur coût final n'est pas connu : le ratio 2025 (0,284 payé) est provisoire.

Phrase actionnable : un client attend en médiane environ sept semaines son premier paiement, et un dossier
sur vingt plus de quatre mois ; c'est le délai à suivre et à réduire, pas le délai de déclaration (5 jours).

## B. Audits antifraude : à qui s'appliquent les chiffres
Sinistres déclarés : 2 800. Audités : 372 (13,3 %). Fraudes confirmées : 37.

**Le taux de confirmation de 9,9 % (IC 95 % : 7,3 % à 13,4 %) ne concerne que les dossiers audités.** Les audits ne sont pas tirés
au hasard : on ne peut donc pas dire que 9,9 % des sinistres sont frauduleux, ni estimer la fraude
parmi les 2 428 dossiers non audités.

| Par garantie | Audités | Fraudes | Taux de confirmation | Couverture d'audit |
|---|---|---|---|---|
| Bris de glace | 13 | 4 | 30,8 % | 3,9 % |
| Vol | 59 | 12 | 20,3 % | 15,1 % |
| Collision | 66 | 9 | 13,6 % | 9,5 % |
| Dégâts des eaux | 68 | 6 | 8,8 % | 11,4 % |
| Incendie | 49 | 4 | 8,2 % | 45,0 % |
| RC | 106 | 2 | 1,9 % | 23,9 % |
| Tempête | 11 | 0 | 0 % | 4,7 % |

Les petits effectifs (13 et 11 audités) rendent le bris de glace et la tempête peu interprétables
(IC 95 % du bris de glace : 12,7 % à 57,6 %).

| Par taille de réserve | Audités | Fraudes | Taux | Couverture |
|---|---|---|---|---|
| moins de 1 k EUR | 58 | 9 | 15,5 % | 4,0 % |
| 1 à 5 k EUR | 74 | 12 | 16,2 % | 8,6 % |
| 5 à 20 k EUR | 197 | 12 | 6,1 % | 46,2 % |
| plus de 20 k EUR | 43 | 4 | 9,3 % | 57,3 % |

Les audits visent les gros dossiers (couverture de 46 à 57 % au-dessus de 5 k EUR), alors que les fraudes
confirmées sont plus fréquentes parmi les petits dossiers audités : 15,9 % en dessous de 5 k EUR (IC 10,6 à 23,1 %)
contre 6,7 % au-dessus (IC 4,1 à 10,6 %). L'écart tient dans les dossiers *audités* ; on ne sait pas ce qu'on
trouverait sans ciblage.

## C. Intérêt des audits en montants (hors sinistre 1129, audité et non frauduleux : 2,48 M EUR)
- 371 dossiers audités ont coûté 3,96 M EUR ; les 37 fraudes confirmées représentent 487 k EUR, soit 12,3 % de ce montant.
- Médiane payée : fraudes confirmées 4 380 EUR, audités non frauduleux 7 312 EUR, non audités avec suite 1 402 EUR.
- Lecture : les audits visent des dossiers beaucoup plus chers que la moyenne (ciblage), mais la fraude
  confirmée pèse peu en montant.

## Phrase actionnable
Le ciblage actuel (gros dossiers, RC, incendie) rapporte peu de fraudes confirmées. Avant de déplacer
l'effort d'audit, il faut mesurer le vrai taux de fraude avec un petit échantillon d'audits tirés au
hasard ; sans cela, on ne sait pas si l'on rate de la fraude sur les petits dossiers ou si elle y est simplement
plus facile à confirmer.
