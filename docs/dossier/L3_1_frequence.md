# L3 · 3.1 Fréquence des sinistres : année-police contre nombre de contrats

## Définition retenue
Fréquence = sinistres avec suite (statut CLOTURE ou OUVERT) / années-police.
Une année-police = un contrat couvert toute une année ; un contrat couvert 3 mois compte 0,25.
Les sinistres sont rattachés à leur année de survenance.

## Résultat

| Produit | Années-police | Sinistres avec suite | Fréquence (années-police) | Fréquence « naïve » (par contrat) |
|---|---|---|---|---|
| Auto | 23 208,6 | 1 026 | **0,0442** | 0,099 |
| Habitation | 21 948,7 | 931 | **0,0424** | 0,095 |

Soit environ 4,4 sinistres pour 100 années-police en auto et 4,2 en habitation.

## Pourquoi la méthode naïve est fausse
Diviser par le nombre de contrats compte chaque contrat une seule fois, alors qu'il est
exposé plusieurs années (en moyenne 2,2 années-police par contrat) : elle surestime la
fréquence d'un facteur 2,2 pour les deux produits. Elle ignore aussi les contrats
souscrits ou résiliés en cours d'année.

## Phrase actionnable
Les deux produits ont une fréquence comparable (4,2 à 4,4 %) : l'écart de rentabilité entre
auto et habitation ne vient donc pas du nombre de sinistres, mais de leur coût et de la prime.
