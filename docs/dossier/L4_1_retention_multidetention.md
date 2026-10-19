# L4 · 4.1 Rétention par cohorte et multi-détention

## Rétention par cohorte
Cohorte = année de souscription. Cellule = part des contrats encore en vigueur au k-ième
anniversaire. Seuls les anniversaires **observables** (atteints avant le 30/06/2025) sont comptés :
les cellules vides ne sont pas des zéros, ce sont des anniversaires qui n'ont pas encore eu lieu.

Auto (%) :

| Cohorte | An 1 | An 2 | An 3 | An 4 | An 5 |
|---|---|---|---|---|---|
| 2020 | 85,2 | 73,5 | 62,2 | 53,9 | 45,9 |
| 2021 | 86,8 | 74,4 | 63,6 | 58,7 | |
| 2022 | 86,5 | 75,3 | 65,9 | | |
| 2023 | 85,8 | 74,3 | | | |
| 2024 | 87,3 | | | | |

Habitation (%) :

| Cohorte | An 1 | An 2 | An 3 | An 4 | An 5 |
|---|---|---|---|---|---|
| 2020 | 85,8 | 75,0 | 65,0 | 56,6 | 49,1 |
| 2021 | 85,6 | 73,7 | 63,3 | 52,6 | |
| 2022 | 86,4 | 73,3 | 65,7 | | |
| 2023 | 87,0 | 73,4 | | | |
| 2024 | 86,9 | | | | |

Lecture :
- Environ 86 % des contrats passent la première année, 74 % la deuxième, 64 % la troisième ;
  à 5 ans, moins de la moitié subsiste (46 % en auto, 49 % en habitation).
- Les cohortes se ressemblent : à ancienneté égale, une cohorte récente ne résilie pas plus qu'une
  ancienne. Le portefeuille ne se dégrade pas, il se renouvelle au même rythme.
- Auto et habitation ont la même courbe.
- Les cellules récentes reposent sur environ la moitié des contrats de la cohorte (par exemple
  977 sur 1 954 en an 1 de la cohorte 2024), car l'autre moitié n'a pas encore atteint son anniversaire.

## Multi-détention : détenir auto ET habitation fidélise-t-il ?
5 242 clients sur 14 977 (35,0 %) détiennent les deux produits.

**Piège : le biais de survie.** L'écart médian entre les deux souscriptions est de 555 jours : pour
devenir multi-détenteur, il faut d'abord être resté client. Comparer « multi » et « mono » à
la date d'extraction favorise mécaniquement les multi.

| Comparaison | Mono | Multi | Test |
|---|---|---|---|
| Naïve (détient les deux produits à l'extraction) | 74,3 % [73,2 ; 75,4] (n=6 479) | 74,3 % [73,0 ; 75,5] (n=4 670) | khi-deux p = 1 |
| Prudente (repère à 12 mois) | 86,4 % [85,6 ; 87,1] (n=8 502) | 86,9 % [84,7 ; 88,7] (n=1 081) | khi-deux p = 0,7 |

La comparaison prudente fixe un repère à 12 mois : on ne regarde que les clients dont le premier
contrat est actif à ce moment, on définit multi/mono à ce moment, puis on observe 12 mois plus
tard. Ainsi, le futur ne sert pas à définir le groupe.

## Conclusion
Dans ces données, la multi-détention n'est **pas associée** à une meilleure rétention (écart de
0,5 point, non significatif, intervalles très proches). Précaution : l'absence de différence
détectable n'est pas la preuve d'une absence d'effet ; l'intervalle prudent permet des écarts
d'environ deux points dans les deux sens.

## Phrase actionnable
Ne pas justifier une campagne de vente croisée par la fidélisation : les données ne la montrent
pas. Si une campagne est menée, la juger sur sa marge propre, et mesurer la rétention avec un
groupe témoin.
