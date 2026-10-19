# Catalogue de données

Généré par `python -m src.gen_catalogue` à partir de l'entrepôt. Toute table ou colonne y figure.


## Schéma `raw`

Copie fidèle des fichiers sources, plus 6 colonnes techniques. Rien n'est corrigé.


### `raw.audits`

Audits antifraude tels que livrés. Lignes : 372.


| Colonne | Type | Description |
|---|---|---|
| `sinistre_id` | VARCHAR | Identifiant sinistre |
| `date_audit` | VARCHAR | Date de l'audit |
| `fraude_confirmee` | VARCHAR | Fraude confirmée par l'audit |
| `_source_file` | VARCHAR | Fichier d'origine de la ligne |
| `_file_hash` | VARCHAR | Empreinte SHA-256 du fichier (détecte un fichier modifié) |
| `_row_num` | INTEGER | Numéro de ligne dans le fichier |
| `_loaded_at` | TIMESTAMP | Horodatage du chargement |
| `_run_id` | VARCHAR | Exécution qui a chargé la ligne |
| `_encoding` | VARCHAR | Encodage détecté (UTF-8 ou latin-1) |

### `raw.clients`

Clients tels que livrés par le CRM (un client peut apparaître en doublon). Lignes : 15 200.


| Colonne | Type | Description |
|---|---|---|
| `client_id` | VARCHAR | Identifiant client |
| `date_naissance` | VARCHAR | Date de naissance (donnée personnelle) |
| `region` | VARCHAR | Région du client |
| `csp` | VARCHAR | Catégorie socioprofessionnelle |
| `consent_marketing` | VARCHAR | Consentement à la prospection |
| `email_hash` | VARCHAR | Empreinte de l'e-mail (pseudonyme, clé de dédoublonnage) |
| `_source_file` | VARCHAR | Fichier d'origine de la ligne |
| `_file_hash` | VARCHAR | Empreinte SHA-256 du fichier (détecte un fichier modifié) |
| `_row_num` | INTEGER | Numéro de ligne dans le fichier |
| `_loaded_at` | TIMESTAMP | Horodatage du chargement |
| `_run_id` | VARCHAR | Exécution qui a chargé la ligne |
| `_encoding` | VARCHAR | Encodage détecté (UTF-8 ou latin-1) |

### `raw.contrats`

Contrats tels que livrés. Lignes : 20 264.


| Colonne | Type | Description |
|---|---|---|
| `contrat_id` | VARCHAR | Identifiant contrat |
| `client_id` | VARCHAR | Identifiant client |
| `produit` | VARCHAR | Produit : AUTO ou HABITATION |
| `date_effet` | VARCHAR | Date d'effet du contrat |
| `date_resiliation` | VARCHAR | Date de résiliation (vide si en vigueur) |
| `formule` | VARCHAR | Formule : ESSENTIELLE, CONFORT, PREMIUM |
| `canal_distribution` | VARCHAR | Canal : AGENT, COURTIER, WEB |
| `zone_risque` | VARCHAR | Zone de risque de 1 à 5 |
| `franchise` | VARCHAR | Franchise du contrat |
| `bonus_malus` | VARCHAR | Coefficient bonus-malus (auto) |
| `puissance_cv` | VARCHAR | Puissance fiscale (auto) |
| `surface_m2` | VARCHAR | Surface du logement (habitation) |
| `prime_annuelle` | VARCHAR | Prime annuelle du contrat |
| `_source_file` | VARCHAR | Fichier d'origine de la ligne |
| `_file_hash` | VARCHAR | Empreinte SHA-256 du fichier (détecte un fichier modifié) |
| `_row_num` | INTEGER | Numéro de ligne dans le fichier |
| `_loaded_at` | TIMESTAMP | Horodatage du chargement |
| `_run_id` | VARCHAR | Exécution qui a chargé la ligne |
| `_encoding` | VARCHAR | Encodage détecté (UTF-8 ou latin-1) |

### `raw.reglements`

Paiements  un fichier par mois ; le nom du montant varie selon le fichier. Lignes : 3 207.


| Colonne | Type | Description |
|---|---|---|
| `paiement_id` | VARCHAR | Identifiant paiement |
| `sinistre_id` | VARCHAR | Identifiant sinistre |
| `date_paiement` | VARCHAR | Date du paiement |
| `montant` | VARCHAR | Montant du paiement |
| `montant_eur` | VARCHAR | Montant du paiement (variante de nom de colonne) |
| `_source_file` | VARCHAR | Fichier d'origine de la ligne |
| `_file_hash` | VARCHAR | Empreinte SHA-256 du fichier (détecte un fichier modifié) |
| `_row_num` | INTEGER | Numéro de ligne dans le fichier |
| `_loaded_at` | TIMESTAMP | Horodatage du chargement |
| `_run_id` | VARCHAR | Exécution qui a chargé la ligne |
| `_encoding` | VARCHAR | Encodage détecté (UTF-8 ou latin-1) |

### `raw.sinistres`

Sinistres tels que livrés (JSON lignes). Lignes : 2 805.


| Colonne | Type | Description |
|---|---|---|
| `sinistre_id` | VARCHAR | Identifiant sinistre |
| `contrat_id` | VARCHAR | Identifiant contrat |
| `date_survenance` | VARCHAR | Date de survenance |
| `date_declaration` | VARCHAR | Date de déclaration |
| `garantie` | VARCHAR | Garantie du sinistre |
| `statut` | VARCHAR | Statut : CLOTURE, OUVERT, SANS_SUITE, REJETE |
| `reserve_initiale` | VARCHAR | Réserve initiale du dossier |
| `_source_file` | VARCHAR | Fichier d'origine de la ligne |
| `_file_hash` | VARCHAR | Empreinte SHA-256 du fichier (détecte un fichier modifié) |
| `_row_num` | INTEGER | Numéro de ligne dans le fichier |
| `_loaded_at` | TIMESTAMP | Horodatage du chargement |
| `_run_id` | VARCHAR | Exécution qui a chargé la ligne |
| `_encoding` | VARCHAR | Encodage détecté (UTF-8 ou latin-1) |

## Schéma `prep`

Préparation : typage, dates normalisées, clés de dédoublonnage. Intermédiaire.


### `prep.audits`

Audits typés. Lignes : 372.


| Colonne | Type | Description |
|---|---|---|
| `sinistre_id` | INTEGER | Identifiant sinistre |
| `date_audit` | DATE | Date de l'audit |
| `fraude_confirmee` | INTEGER | Fraude confirmée par l'audit |
| `_source_file` | VARCHAR | Fichier d'origine de la ligne |
| `_row_num` | INTEGER | Numéro de ligne dans le fichier |

### `prep.audits_ok` (vue)

Audits qui passent les règles bloquantes (vue). Lignes : 372.


| Colonne | Type | Description |
|---|---|---|
| `sinistre_id` | INTEGER | Identifiant sinistre |
| `date_audit` | DATE | Date de l'audit |
| `fraude_confirmee` | INTEGER | Fraude confirmée par l'audit |
| `_source_file` | VARCHAR | Fichier d'origine de la ligne |
| `_row_num` | INTEGER | Numéro de ligne dans le fichier |

### `prep.clients`

Clients typés avec clé de doublon et survivant. Lignes : 15 200.


| Colonne | Type | Description |
|---|---|---|
| `client_id` | INTEGER | Identifiant client |
| `date_naissance_raw` | VARCHAR | Date de naissance telle que livrée |
| `date_naissance` | DATE | Date de naissance (donnée personnelle) |
| `region` | VARCHAR | Région du client |
| `csp` | VARCHAR | Catégorie socioprofessionnelle |
| `consent_marketing` | BOOLEAN | Consentement à la prospection |
| `email_hash` | VARCHAR | Empreinte de l'e-mail (pseudonyme, clé de dédoublonnage) |
| `rang_email` | BIGINT | Rang du client parmi ceux de même e-mail |
| `client_id_survivant` | INTEGER | Identifiant du client conservé |
| `_source_file` | VARCHAR | Fichier d'origine de la ligne |
| `_row_num` | INTEGER | Numéro de ligne dans le fichier |

### `prep.contrats`

Contrats typés. Lignes : 20 264.


| Colonne | Type | Description |
|---|---|---|
| `contrat_id` | INTEGER | Identifiant contrat |
| `client_id` | INTEGER | Identifiant client |
| `produit` | VARCHAR | Produit : AUTO ou HABITATION |
| `date_effet` | DATE | Date d'effet du contrat |
| `date_resiliation` | DATE | Date de résiliation (vide si en vigueur) |
| `formule` | VARCHAR | Formule : ESSENTIELLE, CONFORT, PREMIUM |
| `canal_distribution` | VARCHAR | Canal : AGENT, COURTIER, WEB |
| `zone_risque` | INTEGER | Zone de risque de 1 à 5 |
| `franchise` | INTEGER | Franchise du contrat |
| `bonus_malus` | DOUBLE | Coefficient bonus-malus (auto) |
| `puissance_cv` | DOUBLE | Puissance fiscale (auto) |
| `surface_m2` | DOUBLE | Surface du logement (habitation) |
| `prime_annuelle` | DOUBLE | Prime annuelle du contrat |
| `date_effet_raw` | VARCHAR | Date d'effet telle que livrée |
| `_source_file` | VARCHAR | Fichier d'origine de la ligne |
| `_row_num` | INTEGER | Numéro de ligne dans le fichier |

### `prep.contrats_ok` (vue)

Contrats qui passent les règles bloquantes (vue). Lignes : 20 219.


| Colonne | Type | Description |
|---|---|---|
| `contrat_id` | INTEGER | Identifiant contrat |
| `client_id` | INTEGER | Identifiant client |
| `produit` | VARCHAR | Produit : AUTO ou HABITATION |
| `date_effet` | DATE | Date d'effet du contrat |
| `date_resiliation` | DATE | Date de résiliation (vide si en vigueur) |
| `formule` | VARCHAR | Formule : ESSENTIELLE, CONFORT, PREMIUM |
| `canal_distribution` | VARCHAR | Canal : AGENT, COURTIER, WEB |
| `zone_risque` | INTEGER | Zone de risque de 1 à 5 |
| `franchise` | INTEGER | Franchise du contrat |
| `bonus_malus` | DOUBLE | Coefficient bonus-malus (auto) |
| `puissance_cv` | DOUBLE | Puissance fiscale (auto) |
| `surface_m2` | DOUBLE | Surface du logement (habitation) |
| `prime_annuelle` | DOUBLE | Prime annuelle du contrat |
| `date_effet_raw` | VARCHAR | Date d'effet telle que livrée |
| `_source_file` | VARCHAR | Fichier d'origine de la ligne |
| `_row_num` | INTEGER | Numéro de ligne dans le fichier |

### `prep.reglements`

Paiements typés avec rang d'occurrence (détection des doublons). Lignes : 3 207.


| Colonne | Type | Description |
|---|---|---|
| `paiement_id` | INTEGER | Identifiant paiement |
| `sinistre_id` | INTEGER | Identifiant sinistre |
| `date_paiement` | DATE | Date du paiement |
| `montant` | DOUBLE | Montant du paiement |
| `rang_occ` | BIGINT | Rang d'occurrence du paiement (doublons) |
| `mois_fichier` | VARCHAR | Mois du fichier |
| `mois_paiement` | VARCHAR | Mois du paiement |
| `_source_file` | VARCHAR | Fichier d'origine de la ligne |
| `_row_num` | INTEGER | Numéro de ligne dans le fichier |

### `prep.reglements_ok` (vue)

Paiements qui passent les règles bloquantes (vue). Lignes : 3 174.


| Colonne | Type | Description |
|---|---|---|
| `paiement_id` | INTEGER | Identifiant paiement |
| `sinistre_id` | INTEGER | Identifiant sinistre |
| `date_paiement` | DATE | Date du paiement |
| `montant` | DOUBLE | Montant du paiement |
| `rang_occ` | BIGINT | Rang d'occurrence du paiement (doublons) |
| `mois_fichier` | VARCHAR | Mois du fichier |
| `mois_paiement` | VARCHAR | Mois du paiement |
| `_source_file` | VARCHAR | Fichier d'origine de la ligne |
| `_row_num` | INTEGER | Numéro de ligne dans le fichier |

### `prep.sinistres`

Sinistres typés. Lignes : 2 805.


| Colonne | Type | Description |
|---|---|---|
| `sinistre_id` | INTEGER | Identifiant sinistre |
| `contrat_id` | INTEGER | Identifiant contrat |
| `date_survenance` | DATE | Date de survenance |
| `date_declaration` | DATE | Date de déclaration |
| `garantie` | VARCHAR | Garantie du sinistre |
| `statut` | VARCHAR | Statut : CLOTURE, OUVERT, SANS_SUITE, REJETE |
| `reserve_initiale` | DOUBLE | Réserve initiale du dossier |
| `_source_file` | VARCHAR | Fichier d'origine de la ligne |
| `_row_num` | INTEGER | Numéro de ligne dans le fichier |

### `prep.sinistres_ok` (vue)

Sinistres qui passent les règles bloquantes (vue). Lignes : 2 800.


| Colonne | Type | Description |
|---|---|---|
| `sinistre_id` | INTEGER | Identifiant sinistre |
| `contrat_id` | INTEGER | Identifiant contrat |
| `date_survenance` | DATE | Date de survenance |
| `date_declaration` | DATE | Date de déclaration |
| `garantie` | VARCHAR | Garantie du sinistre |
| `statut` | VARCHAR | Statut : CLOTURE, OUVERT, SANS_SUITE, REJETE |
| `reserve_initiale` | DOUBLE | Réserve initiale du dossier |
| `_source_file` | VARCHAR | Fichier d'origine de la ligne |
| `_row_num` | INTEGER | Numéro de ligne dans le fichier |

## Schéma `quarantine`

Lignes écartées des calculs, avec la règle et le motif. Rien n'est supprimé.


### `quarantine.raw_rejects`

Lignes illisibles dès la lecture du fichier (format cassé). Lignes : 0.


| Colonne | Type | Description |
|---|---|---|
| `source` | VARCHAR | Source de données |
| `source_file` | VARCHAR | Fichier d'origine |
| `row_num` | INTEGER | Numéro de ligne |
| `motif` | VARCHAR | Motif de l'écart |
| `raw_line` | VARCHAR | Ligne brute illisible |
| `run_id` | VARCHAR | Identifiant d'exécution |

### `quarantine.rows`

Une ligne par enregistrement écarté : règle  entité  clé  fichier  motif  ligne d'origine en JSON. Lignes : 283.


| Colonne | Type | Description |
|---|---|---|
| `rule_id` | VARCHAR | Identifiant de la règle |
| `entity` | VARCHAR | Entité concernée |
| `record_key` | VARCHAR | Clé de l'enregistrement écarté |
| `source_file` | VARCHAR | Fichier d'origine |
| `motif` | VARCHAR | Motif de l'écart |
| `payload` | VARCHAR | Ligne d'origine en JSON |

## Schéma `core`

Modèle dimensionnel (étoile) : dimensions et faits utilisés pour tous les calculs.


### `core.client_alias`

Table de passage doublon -> client survivant. Lignes : 200.


| Colonne | Type | Description |
|---|---|---|
| `client_id_doublon` | INTEGER | Identifiant du client fusionné |
| `client_id_survivant` | INTEGER | Identifiant du client conservé |

### `core.dim_client`

Dimension client dédoublonnée  prête pour l'historisation SCD2. Lignes : 15 000.


| Colonne | Type | Description |
|---|---|---|
| `client_id` | INTEGER | Identifiant client |
| `date_naissance` | DATE | Date de naissance (donnée personnelle) |
| `region` | VARCHAR | Région du client |
| `csp` | VARCHAR | Catégorie socioprofessionnelle |
| `consent_marketing` | BOOLEAN | Consentement à la prospection |
| `email_hash` | VARCHAR | Empreinte de l'e-mail (pseudonyme, clé de dédoublonnage) |
| `valid_from` | DATE | Début de validité de la version (SCD2) |
| `valid_to` | DATE | Fin de validité de la version (SCD2) |
| `is_current` | BOOLEAN | Version en vigueur |

### `core.dim_contrat`

Dimension contrat (SCD1) : caractéristiques et dates de vie du contrat. Lignes : 20 219.


| Colonne | Type | Description |
|---|---|---|
| `contrat_id` | INTEGER | Identifiant contrat |
| `client_id` | INTEGER | Identifiant client |
| `segment_sk` | BIGINT | Clé du segment de risque |
| `produit` | VARCHAR | Produit : AUTO ou HABITATION |
| `formule` | VARCHAR | Formule : ESSENTIELLE, CONFORT, PREMIUM |
| `canal_distribution` | VARCHAR | Canal : AGENT, COURTIER, WEB |
| `zone_risque` | INTEGER | Zone de risque de 1 à 5 |
| `franchise` | INTEGER | Franchise du contrat |
| `bonus_malus` | DOUBLE | Coefficient bonus-malus (auto) |
| `puissance_cv` | DOUBLE | Puissance fiscale (auto) |
| `surface_m2` | DOUBLE | Surface du logement (habitation) |
| `prime_annuelle` | DOUBLE | Prime annuelle du contrat |
| `tranche_age` | VARCHAR | Tranche d'âge du souscripteur à la souscription |
| `date_effet` | DATE | Date d'effet du contrat |
| `date_resiliation` | DATE | Date de résiliation (vide si en vigueur) |
| `date_effet_key` | INTEGER | Clé de date de l'effet |
| `date_resiliation_key` | INTEGER | Clé de date de résiliation |
| `est_resilie` | BOOLEAN | Contrat résilié |

### `core.dim_date`

Calendrier  clé entière AAAAMMJJ. Lignes : 2 192.


| Colonne | Type | Description |
|---|---|---|
| `date_key` | INTEGER | Clé de date AAAAMMJJ |
| `date` | DATE | Date |
| `annee` | BIGINT | Année civile |
| `mois` | BIGINT | Mois |
| `trimestre` | BIGINT | Trimestre |
| `annee_mois` | VARCHAR | Année et mois (AAAA-MM) |
| `debut_mois` | DATE | Premier jour du mois |
| `est_futur` | BOOLEAN | Date postérieure à l'extraction |

### `core.dim_garantie`

Garanties par produit. Lignes : 8.


| Colonne | Type | Description |
|---|---|---|
| `garantie_sk` | BIGINT | Clé de la garantie |
| `produit` | VARCHAR | Produit : AUTO ou HABITATION |
| `garantie_code` | VARCHAR | Code de la garantie |
| `libelle` | VARCHAR | Libellé de la garantie |

### `core.dim_segment_risque`

Segment de risque figé à la souscription (produit  zone  formule  canal  tranche d'âge). Lignes : 533.


| Colonne | Type | Description |
|---|---|---|
| `segment_sk` | BIGINT | Clé du segment de risque |
| `produit` | VARCHAR | Produit : AUTO ou HABITATION |
| `zone_risque` | INTEGER | Zone de risque de 1 à 5 |
| `formule` | VARCHAR | Formule : ESSENTIELLE, CONFORT, PREMIUM |
| `canal_distribution` | VARCHAR | Canal : AGENT, COURTIER, WEB |
| `tranche_age` | VARCHAR | Tranche d'âge du souscripteur à la souscription |

### `core.fact_audit`

Grain : un sinistre audité  avec le résultat de l'audit. Lignes : 372.


| Colonne | Type | Description |
|---|---|---|
| `sinistre_id` | INTEGER | Identifiant sinistre |
| `date_audit` | DATE | Date de l'audit |
| `date_audit_key` | INTEGER | Clé de date de l'audit |
| `fraude_confirmee` | BOOLEAN | Fraude confirmée par l'audit |

### `core.fact_exposition`

Grain : un contrat par année civile. Jours couverts  année-police  prime acquise. Lignes : 65 081.


| Colonne | Type | Description |
|---|---|---|
| `contrat_id` | INTEGER | Identifiant contrat |
| `annee` | BIGINT | Année civile |
| `client_id` | INTEGER | Identifiant client |
| `segment_sk` | BIGINT | Clé du segment de risque |
| `date_debut` | DATE | Début de couverture dans l'année |
| `date_fin_exclue` | DATE | Fin de couverture (exclue) |
| `jours_couverture` | BIGINT | Jours couverts dans l'année |
| `jours_annee` | BIGINT | Jours de l'année |
| `exposition_annee_police` | DOUBLE | Année-police : jours couverts / jours de l'année |
| `prime_acquise` | DOUBLE | Prime acquise : prime annuelle x année-police |

### `core.fact_reglement`

Grain : un paiement. Chargée de façon incrémentale  jamais modifiée. Lignes : 3 174.


| Colonne | Type | Description |
|---|---|---|
| `paiement_id` | INTEGER | Identifiant paiement |
| `sinistre_id` | INTEGER | Identifiant sinistre |
| `contrat_id` | INTEGER | Identifiant contrat |
| `date_key` | INTEGER | Clé de date AAAAMMJJ |
| `date_paiement` | DATE | Date du paiement |
| `montant` | DECIMAL(14,2) | Montant du paiement |
| `source_file` | VARCHAR | Fichier d'origine |
| `loaded_at` | TIMESTAMP | Horodatage du chargement |

### `core.fact_sinistre`

Grain : un sinistre. Dates  statut  réserve  règlements cumulés. Lignes : 2 800.


| Colonne | Type | Description |
|---|---|---|
| `sinistre_id` | INTEGER | Identifiant sinistre |
| `contrat_id` | INTEGER | Identifiant contrat |
| `client_id` | INTEGER | Identifiant client |
| `segment_sk` | BIGINT | Clé du segment de risque |
| `garantie_sk` | BIGINT | Clé de la garantie |
| `date_survenance_key` | INTEGER | Clé de date de survenance |
| `date_declaration_key` | INTEGER | Clé de date de déclaration |
| `date_survenance` | DATE | Date de survenance |
| `date_declaration` | DATE | Date de déclaration |
| `annee_survenance` | BIGINT | Année de survenance |
| `statut` | VARCHAR | Statut : CLOTURE, OUVERT, SANS_SUITE, REJETE |
| `reserve_initiale` | DECIMAL(14,2) | Réserve initiale du dossier |
| `delai_declaration_j` | BIGINT | Délai de déclaration en jours |
| `anomalie_declaration_avant_survenance` | BOOLEAN | Déclaration antérieure à la survenance |
| `anomalie_hors_couverture` | BOOLEAN | Survenance hors période de couverture |
| `nb_reglements` | BIGINT | Nombre de règlements |
| `montant_regle` | DECIMAL(14,2) | Montant payé cumulé |
| `date_premier_reglement` | DATE | Date du premier paiement |
| `date_dernier_reglement` | DATE | Date du dernier paiement |

## Schéma `marts`

Tables prêtes pour le tableau de bord. Le tableau de bord ne lit que ce schéma.


### `marts.audit_critere`

Résultats d'audit par critère (garantie  produit  tranche de réserve...). Lignes : 18.


| Colonne | Type | Description |
|---|---|---|
| `critere` | VARCHAR | Critère d'analyse |
| `modalite` | VARCHAR | Modalité du critère |
| `sinistres` | BIGINT | Sinistres |
| `audites` | BIGINT | Sinistres audités |
| `fraudes_confirmees` | BIGINT | Fraudes confirmées |
| `taux_confirmation` | DOUBLE | Fraudes confirmées / audités (population auditée seulement) |
| `couverture_audit` | DOUBLE | Audités / sinistres |

### `marts.contribution_segment`

Contribution de chaque segment à la variation du ratio global. Lignes : 100.


| Colonne | Type | Description |
|---|---|---|
| `annee` | BIGINT | Année civile |
| `perimetre` | VARCHAR | Périmètre : tous les sinistres ou hors sinistre extrême |
| `produit` | VARCHAR | Produit : AUTO ou HABITATION |
| `zone_risque` | INTEGER | Zone de risque de 1 à 5 |
| `poids_avant` | DOUBLE | Poids du segment, année précédente |
| `poids_apres` | DOUBLE | Poids du segment, année courante |
| `ratio_avant` | DOUBLE | Ratio du segment, année précédente |
| `ratio_apres` | DOUBLE | Ratio du segment, année courante |
| `contribution` | DOUBLE | Contribution à la variation du ratio global (points) |

### `marts.decomposition_annuelle`

Décomposition de la variation annuelle du ratio S/P (fréquence  coût  prime). Lignes : 12.


| Colonne | Type | Description |
|---|---|---|
| `annee` | BIGINT | Année civile |
| `perimetre` | VARCHAR | Périmètre : tous les sinistres ou hors sinistre extrême |
| `exposition` | DOUBLE | Années-police |
| `prime_acquise` | DOUBLE | Prime acquise : prime annuelle x année-police |
| `sinistres_avec_suite` | HUGEINT | Sinistres CLOTURE ou OUVERT |
| `paye` | DOUBLE | Sinistres payés |
| `frequence` | DOUBLE | Fréquence |
| `cout_moyen` | DOUBLE | Coût moyen |
| `prime_moyenne` | DOUBLE | Prime moyenne |
| `ratio` | DOUBLE | Ratio sinistres / primes |
| `var_ratio_log` | DOUBLE | Variation du ratio (logarithme) |
| `effet_frequence` | DOUBLE | Part due à la fréquence |
| `effet_cout` | DOUBLE | Part due au coût moyen |
| `effet_prime` | DOUBLE | Part due à la prime |
| `variation_volume_log` | DOUBLE | Variation du volume (information) |
| `statut_annee` | VARCHAR | Année complète, partielle ou de démarrage |

### `marts.delais_garantie`

Délais de déclaration  de règlement et de clôture par garantie. Lignes : 24.


| Colonne | Type | Description |
|---|---|---|
| `produit` | VARCHAR | Produit : AUTO ou HABITATION |
| `garantie` | VARCHAR | Garantie du sinistre |
| `libelle` | VARCHAR | Libellé de la garantie |
| `etape` | VARCHAR | Étape mesurée du délai |
| `n` | BIGINT | Effectif |
| `mediane` | DOUBLE | Médiane (jours) |
| `q75` | DOUBLE | 75e centile |
| `q90` | DOUBLE | 90e centile |
| `q95` | DOUBLE | 95e centile |
| `maximum` | BIGINT | Maximum |

### `marts.ops_chargement_source` (vue)

Vue : lignes lues  chargées  rejetées par source. Lignes : 5.


| Colonne | Type | Description |
|---|---|---|
| `source` | VARCHAR | Source de données |
| `fichiers` | BIGINT | Nombre de fichiers |
| `lignes_lues` | HUGEINT | Lignes lues |
| `lignes_chargees` | HUGEINT | Lignes chargées |
| `lignes_rejetees_lecture` | HUGEINT | Lignes rejetées à la lecture |
| `dernier_chargement` | TIMESTAMP | Dernier chargement |
| `fichiers_en_echec` | BIGINT | Fichiers en échec |

### `marts.ops_fraicheur` (vue)

Vue : date métier la plus récente par source. Lignes : 5.


| Colonne | Type | Description |
|---|---|---|
| `source` | VARCHAR | Source de données |
| `derniere_date_metier` | DATE | Date métier la plus récente |
| `date_extraction` | DATE | Date d'extraction |

### `marts.ops_regles_qualite` (vue)

Vue : règles de qualité et nombre d'anomalies. Lignes : 36.


| Colonne | Type | Description |
|---|---|---|
| `rule_id` | VARCHAR | Identifiant de la règle |
| `dimension` | VARCHAR | Dimension de qualité |
| `entity` | VARCHAR | Entité concernée |
| `description` | VARCHAR | Description |
| `severity` | VARCHAR | Gravité |
| `treatment` | VARCHAR | Traitement appliqué |
| `volume` | INTEGER | Nombre de lignes concernées |

### `marts.ops_rejets_regle` (vue)

Vue : nombre de lignes en quarantaine par règle. Lignes : 6.


| Colonne | Type | Description |
|---|---|---|
| `rule_id` | VARCHAR | Identifiant de la règle |
| `entity` | VARCHAR | Entité concernée |
| `lignes` | BIGINT | Nombre de lignes |
| `exemple_motif` | VARCHAR | Exemple de motif |

### `marts.ops_runs` (vue)

Vue : historique des exécutions du pipeline. Lignes : 1.


| Colonne | Type | Description |
|---|---|---|
| `run_id` | VARCHAR | Identifiant d'exécution |
| `started_at` | TIMESTAMP | Début |
| `finished_at` | TIMESTAMP | Fin |
| `status` | VARCHAR | Statut |
| `n_tests` | INTEGER | Nombre de tests |
| `n_tests_failed` | INTEGER | Tests en échec |
| `message` | VARCHAR | Message |

### `marts.ops_tests` (vue)

Vue : résultat des tests du dernier passage. Lignes : 28.


| Colonne | Type | Description |
|---|---|---|
| `test_id` | VARCHAR | Identifiant du test |
| `description` | VARCHAR | Description |
| `violations` | INTEGER | Nombre de violations |
| `status` | VARCHAR | Statut |
| `executed_at` | TIMESTAMP | Horodatage d'exécution |

### `marts.pareto_valeur`

Courbe de concentration de la valeur client. Lignes : 200.


| Colonne | Type | Description |
|---|---|---|
| `perimetre` | VARCHAR | Périmètre : tous les sinistres ou hors sinistre extrême |
| `pct_clients` | INTEGER | Part des clients, du plus au moins rentable |
| `valeur_cumulee` | DOUBLE | Valeur cumulée |
| `part_cumulee_valeur` | DOUBLE | Part cumulée de la valeur nette |

### `marts.portefeuille_annee_produit`

Indicateurs annuels par produit : exposition  primes  sinistres  fréquence  coût  S/P. Lignes : 12.


| Colonne | Type | Description |
|---|---|---|
| `annee` | BIGINT | Année civile |
| `produit` | VARCHAR | Produit : AUTO ou HABITATION |
| `contrats_exposes` | BIGINT | Contrats exposés |
| `exposition` | DOUBLE | Années-police |
| `prime_acquise` | DOUBLE | Prime acquise : prime annuelle x année-police |
| `sinistres_declares` | BIGINT | Sinistres déclarés |
| `sinistres_avec_suite` | BIGINT | Sinistres CLOTURE ou OUVERT |
| `sinistres_sans_suite` | BIGINT | Sinistres sans suite |
| `sinistres_rejetes` | BIGINT | Sinistres rejetés |
| `montant_regle` | DOUBLE | Montant payé cumulé |
| `frequence_par_annee_police` | DOUBLE | Sinistres avec suite / année-police |
| `cout_moyen_par_sinistre` | DOUBLE | Payé / sinistres avec suite |
| `ratio_sinistres_primes` | DOUBLE | Payé / primes acquises |

### `marts.portefeuille_mois`

Indicateurs mensuels par produit  zone  canal  région. Lignes : 23 336.


| Colonne | Type | Description |
|---|---|---|
| `mois` | DATE | Mois |
| `annee` | BIGINT | Année civile |
| `mois_num` | BIGINT | Numéro du mois |
| `produit` | VARCHAR | Produit : AUTO ou HABITATION |
| `zone_risque` | INTEGER | Zone de risque de 1 à 5 |
| `canal` | VARCHAR | Canal de distribution |
| `region` | VARCHAR | Région du client |
| `exposition` | DOUBLE | Années-police |
| `prime_acquise` | DOUBLE | Prime acquise : prime annuelle x année-police |
| `contrats_actifs_fin_mois` | BIGINT | Contrats actifs en fin de mois |
| `nouveaux_contrats` | BIGINT | Contrats souscrits |
| `resiliations` | BIGINT | Contrats résiliés |
| `sinistres_declares` | BIGINT | Sinistres déclarés |
| `sinistres_avec_suite` | BIGINT | Sinistres CLOTURE ou OUVERT |
| `sinistres_extremes` | BIGINT | Sinistres extrêmes (cumul payé > 500 000 EUR) |
| `paye` | DOUBLE | Sinistres payés |
| `paye_hors_extreme` | DOUBLE | Sinistres payés hors sinistre extrême |

### `marts.profil_decile`

Profil moyen de chaque décile de valeur client. Lignes : 10.


| Colonne | Type | Description |
|---|---|---|
| `decile` | BIGINT | Décile de valeur (1 = plus rentable) |
| `clients` | BIGINT | Nombre de clients |
| `exposition_moy` | DOUBLE | Exposition moyenne |
| `valeur_par_annee_police_moy` | DOUBLE | Valeur moyenne par année-police |
| `valeur_moy` | DOUBLE | Valeur moyenne |
| `prime_moy` | DOUBLE | Prime acquise moyenne |
| `paye_moy` | DOUBLE | Payé moyen |
| `sinistres_moy` | DOUBLE | Sinistres moyens |
| `contrats_moy` | DOUBLE | Contrats moyens |
| `part_multi_detenteurs` | DOUBLE | Part de clients à deux produits |

### `marts.retention_cohorte`

Rétention des contrats par cohorte et anniversaire observable. Lignes : 30.


| Colonne | Type | Description |
|---|---|---|
| `produit` | VARCHAR | Produit : AUTO ou HABITATION |
| `cohorte` | BIGINT | Année de souscription |
| `annee_anniversaire` | BIGINT | Rang de l'anniversaire |
| `contrats_eligibles` | BIGINT | Contrats ayant atteint l'anniversaire |
| `contrats_retenus` | BIGINT | Contrats encore en vigueur |
| `retention` | DOUBLE | Part retenue |

### `marts.technique_segment`

Indicateurs techniques par année et segment de risque. Lignes : 3 090.


| Colonne | Type | Description |
|---|---|---|
| `annee` | BIGINT | Année civile |
| `produit` | VARCHAR | Produit : AUTO ou HABITATION |
| `zone_risque` | INTEGER | Zone de risque de 1 à 5 |
| `formule` | VARCHAR | Formule : ESSENTIELLE, CONFORT, PREMIUM |
| `canal` | VARCHAR | Canal de distribution |
| `tranche_age` | VARCHAR | Tranche d'âge du souscripteur à la souscription |
| `exposition` | DOUBLE | Années-police |
| `prime_acquise` | DOUBLE | Prime acquise : prime annuelle x année-police |
| `sinistres_avec_suite` | BIGINT | Sinistres CLOTURE ou OUVERT |
| `sinistres_sans_suite` | BIGINT | Sinistres sans suite |
| `sinistres_rejetes` | BIGINT | Sinistres rejetés |
| `sinistres_extremes` | BIGINT | Sinistres extrêmes (cumul payé > 500 000 EUR) |
| `paye` | DOUBLE | Sinistres payés |
| `paye_hors_extreme` | DOUBLE | Sinistres payés hors sinistre extrême |
| `reserve_residuelle_ouverts` | DOUBLE | Réserve restante des dossiers ouverts |
| `resiliations` | BIGINT | Contrats résiliés |

### `marts.valeur_client`

Une ligne par client : primes acquises  sinistres payés  valeur. Niveau individuel. Lignes : 14 977.


| Colonne | Type | Description |
|---|---|---|
| `client_id` | INTEGER | Identifiant client |
| `region` | VARCHAR | Région du client |
| `csp` | VARCHAR | Catégorie socioprofessionnelle |
| `nb_contrats` | BIGINT | Nombre de contrats |
| `nb_produits` | BIGINT | Nombre de produits détenus |
| `cohorte` | BIGINT | Année de souscription |
| `prime_acquise` | DOUBLE | Prime acquise : prime annuelle x année-police |
| `exposition` | DOUBLE | Années-police |
| `paye` | DOUBLE | Sinistres payés |
| `nb_sinistres` | BIGINT | Sinistres avec suite |
| `client_sinistre_extreme` | BOOLEAN | Client portant un sinistre extrême |
| `valeur` | DOUBLE | Primes acquises - sinistres payés |

## Schéma `ops`

Journal d'exploitation : chargements, exécutions, résultats des tests.


### `ops.ingestion_log`

Un enregistrement par fichier chargé : empreinte  lignes lues  chargées  rejetées  statut. Lignes : 68.


| Colonne | Type | Description |
|---|---|---|
| `run_id` | VARCHAR | Identifiant d'exécution |
| `source` | VARCHAR | Source de données |
| `file` | VARCHAR | Nom du fichier |
| `file_hash` | VARCHAR | Empreinte du fichier |
| `rows_read` | INTEGER | Lignes lues |
| `rows_loaded` | INTEGER | Lignes chargées |
| `rows_rejected` | INTEGER | Lignes rejetées |
| `duration_s` | DOUBLE | Durée en secondes |
| `status` | VARCHAR | Statut |
| `message` | VARCHAR | Message |
| `logged_at` | TIMESTAMP | Horodatage |

### `ops.pipeline_runs`

Une ligne par exécution du pipeline. Lignes : 1.


| Colonne | Type | Description |
|---|---|---|
| `run_id` | VARCHAR | Identifiant d'exécution |
| `started_at` | TIMESTAMP | Début |
| `finished_at` | TIMESTAMP | Fin |
| `status` | VARCHAR | Statut |
| `n_tests` | INTEGER | Nombre de tests |
| `n_tests_failed` | INTEGER | Tests en échec |
| `message` | VARCHAR | Message |

### `ops.test_results`

Résultat de chaque test à chaque exécution. Lignes : 28.


| Colonne | Type | Description |
|---|---|---|
| `run_id` | VARCHAR | Identifiant d'exécution |
| `test_id` | VARCHAR | Identifiant du test |
| `description` | VARCHAR | Description |
| `violations` | INTEGER | Nombre de violations |
| `status` | VARCHAR | Statut |
| `executed_at` | TIMESTAMP | Horodatage d'exécution |

## Schéma `dq`

Résultats des règles de qualité des données.


### `dq.rule_results`

Mesure de chaque règle de qualité à chaque exécution. Lignes : 36.


| Colonne | Type | Description |
|---|---|---|
| `run_id` | VARCHAR | Identifiant d'exécution |
| `rule_id` | VARCHAR | Identifiant de la règle |
| `dimension` | VARCHAR | Dimension de qualité |
| `entity` | VARCHAR | Entité concernée |
| `description` | VARCHAR | Description |
| `severity` | VARCHAR | Gravité |
| `treatment` | VARCHAR | Traitement appliqué |
| `volume` | INTEGER | Nombre de lignes concernées |
| `query` | VARCHAR | Requête de mesure |
| `computed_at` | TIMESTAMP | Horodatage du calcul |
