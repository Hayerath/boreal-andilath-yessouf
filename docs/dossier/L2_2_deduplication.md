# Livrable 2 · 2.2 Déduplication des clients

## Clé de rapprochement : `email_hash`
Le CRM ne contient ni nom ni coordonnée (données pseudonymisées) mais une empreinte d'e-mail. Deux fiches avec la même empreinte désignent la même adresse, donc la même personne. C'est la seule clé stable et propre à une personne dans la source.

**Pourquoi pas la date de naissance + la région ?** Je l'ai testé : 740 groupes de clients partagent la même date de naissance et la même région, et dans **559 d'entre eux les empreintes d'e-mail sont différentes**. Cette clé aurait fusionné à tort des personnes distinctes (même jour de naissance, même région : cas fréquent).

**Validation de la clé.** Sur les 200 paires détectées par `email_hash`, la date de naissance, la région, la CSP et le consentement marketing concordent à 100 % (règle U06 : 0 contradiction). Une collision accidentelle d'empreinte aurait produit des fiches différentes ; ce n'est pas le cas.

## Taux de doublons
15 200 fiches pour 15 000 empreintes distinctes : **200 doublons, soit 1,32 %**. Tous les groupes comptent exactement 2 fiches (14 800 clients uniques + 200 paires).

## Règle de survie
- **Identifiant conservé** : le plus petit `client_id` du groupe. La fiche conservée est la plus ancienne, et c'est celle sur laquelle les contrats existants sont déjà rattachés.
- **Constat** : les 200 doublons ont des identifiants de 15 001 à 15 200 (ajoutés en fin de fichier) et **aucun contrat** n'y est rattaché dans cette extraction.
- **Contrats rattachés à un doublon** (cas absent ici, mais prévu) : ils sont rebasculés sur le survivant grâce à la table `core.client_alias` (doublon → survivant), appliquée lors de la construction de `dim_contrat`. Aucun contrat ne peut donc rester accroché à un identifiant fusionné.
- **Traçabilité** : les 200 fiches fusionnées ne sont pas supprimées. Elles sont dans `quarantine.rows` (règle U02) avec leur ligne complète, et dans `core.client_alias`.

## Contrôles automatiques
- Test `T17_dedup_email` : aucune empreinte en double dans `core.dim_client` (15 000 clients).
- Test `T16_alias_survivants` : tout alias pointe un survivant présent.
- Test `T14_recon_clients` : 15 200 lignes du brut = 15 000 clients du cœur + 200 alias.

## Limite
La clé ne détecte pas une même personne ayant utilisé deux adresses e-mail différentes. Ces cas ne sont pas mesurables avec les données disponibles.
