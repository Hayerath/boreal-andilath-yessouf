# L5 · Données personnelles et RGPD

Analyse technique réalisée par l'équipe projet ; elle ne remplace pas l'avis du délégué à la protection des données (DPO) ni d'un juriste.

## 1. Quelles données personnelles ?
Source clients (`crm/clients.csv`) : `client_id`, `date_naissance`, `region`, `csp`, `consent_marketing`, `email_hash`.
Aucun nom, adresse, e-mail en clair ni téléphone n'est reçu. Les autres sources (contrats, sinistres, règlements, audits) ne contiennent
pas d'identité, mais elles se rattachent à un client par `client_id` : ce sont des données personnelles dès qu'on peut remonter au client.

Points d'attention :
- **`email_hash`** : pseudonyme, pas anonymisation. Il reste une donnée personnelle, car quiconque connaît une adresse e-mail peut recalculer
  son empreinte (surtout si l'empreinte n'est pas salée ; le mode de calcul est inconnu de l'équipe, à demander à la source).
- **`date_naissance` + `region` + `csp`** : combinés, ils permettent de réidentifier une personne dans un petit effectif.
- **`fraude_confirmee`** : information sur une suspicion puis une confirmation de fraude, d'une sensibilité élevée : à traiter avec un accès restreint.
- **`consent_marketing`** : indique une base légale pour la prospection ; il n'est pas utilisé dans les analyses.

## 2. Où se trouvent ces données dans l'entrepôt ?

| Couche | Données personnelles présentes | Commentaire |
|---|---|---|
| raw | toutes les colonnes de la source | copie fidèle, par choix |
| quarantine | la ligne complète en JSON (`payload`) | réplique des lignes écartées, y compris `date_naissance` et `email_hash` des clients doublons |
| core | `dim_client` (date de naissance, région, CSP, e-mail haché), clés client partout | niveau individuel |
| marts | `marts.valeur_client` (une ligne par client : `client_id`, région, CSP, valeur) ; autres marts agrégés | le tableau de bord n'affiche que des agrégats, mais la table est individuelle |
| ops / dq | noms de fichiers, comptes, motifs | pas de donnée personnelle directe |

## 3. Principes appliqués dans le projet
- **Minimisation** : les analyses utilisent la tranche d'âge (calculée à la souscription) et non la date de naissance exacte ; aucun nom ni adresse n'est collecté.
- **Pseudonymisation** : l'e-mail n'est manipulé que sous forme d'empreinte, y compris pour la déduplication.
- **Finalité** : analyse technique et pilotage du portefeuille ; pas de prospection, pas de décision individuelle automatique.
- **Traçabilité** : chaque ligne sait de quel fichier elle vient (`source_file`, `loaded_at`).

## 4. Durée de conservation (propositions à valider par le DPO)
- Les durées sont fixées par la finalité et les obligations légales du métier (contrats et sinistres), pas par le confort technique.
- Proposition : conserver les données individuelles (raw, core) pendant la durée de la relation contractuelle et des délais de prescription applicables, puis anonymiser ;
  les marts agrégés peuvent être conservés plus longtemps s'ils ne permettent plus d'identifier une personne (pas de `client_id`).
- La quarantaine est un stock de travail : à purger une fois les lignes corrigées ou classées.

## 5. Droit à l'effacement : procédure proposée
Le projet n'implémente pas encore cette procédure automatiquement ; voici comment elle serait menée :
1. Identifier le `client_id` (et ses alias dans `client_alias`).
2. Faire supprimer le client dans la source, sinon l'ingestion le rechargerait.
3. Supprimer ses lignes dans `raw` (c'est une exception documentée au principe « le brut est une copie fidèle »), dans `quarantine.rows` (le JSON contient ses données) et dans les journaux si besoin.
4. Reconstruire core et marts depuis le brut (`python -m src.pipeline run`) : le rejeu est idempotent, donc le client disparaît partout.
5. Traiter les sauvegardes et exports (dossier, copies du fichier DuckDB).
6. Garder une trace de la demande (date, périmètre) sans conserver les données effacées.

Réserve : une obligation légale de conservation (contrat d'assurance, sinistre en cours) peut limiter l'effacement ; le DPO tranche.

## 6. Mesures de sécurité recommandées
- Fichier DuckDB hors dépôt Git (déjà dans `.gitignore`) ; données sources non versionnées.
- Accès restreint aux couches raw, core et quarantine ; le tableau de bord ne lit que les marts.
- Masquer ou retirer `client_id`, région et CSP des exports partagés ; ne diffuser que des agrégats avec un effectif minimum par cellule.
- Journaliser les accès et les chargements (`ops.ingestion_log` existe déjà pour les chargements).
