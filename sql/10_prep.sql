-- COUCHE PRÉPARATION : typage et normalisation uniquement. Aucune ligne n'est supprimée ici.
-- Les défauts sont mesurés (src/quality_rules.py) puis traités en 20_quarantine.sql / 30_core.sql.

CREATE OR REPLACE TABLE prep.clients AS
SELECT
  TRY_CAST(client_id AS INTEGER)                                   AS client_id,
  date_naissance                                                   AS date_naissance_raw,
  -- 01/01/1890 est une valeur factice (18 occurrences) : traitée comme inconnue
  CASE WHEN date_naissance = '01/01/1890' THEN NULL
       ELSE TRY_STRPTIME(date_naissance, '%d/%m/%Y')::DATE END     AS date_naissance,
  region, csp,
  (TRY_CAST(consent_marketing AS INTEGER) = 1)                     AS consent_marketing,
  email_hash,
  -- clé de rapprochement : email_hash ; survivant = plus petit client_id
  ROW_NUMBER() OVER (PARTITION BY email_hash ORDER BY TRY_CAST(client_id AS INTEGER)) AS rang_email,
  FIRST_VALUE(TRY_CAST(client_id AS INTEGER)) OVER (PARTITION BY email_hash
        ORDER BY TRY_CAST(client_id AS INTEGER))                   AS client_id_survivant,
  _source_file, _row_num
FROM raw.clients;

CREATE OR REPLACE TABLE prep.contrats AS
SELECT
  TRY_CAST(contrat_id AS INTEGER) AS contrat_id, TRY_CAST(client_id AS INTEGER) AS client_id,
  produit, TRY_CAST(date_effet AS DATE) AS date_effet, TRY_CAST(date_resiliation AS DATE) AS date_resiliation,
  formule, canal_distribution, TRY_CAST(zone_risque AS INTEGER) AS zone_risque,
  TRY_CAST(franchise AS INTEGER) AS franchise, TRY_CAST(bonus_malus AS DOUBLE) AS bonus_malus,
  TRY_CAST(puissance_cv AS DOUBLE) AS puissance_cv, TRY_CAST(surface_m2 AS DOUBLE) AS surface_m2,
  TRY_CAST(prime_annuelle AS DOUBLE) AS prime_annuelle,
  date_effet AS date_effet_raw, _source_file, _row_num
FROM raw.contrats;

CREATE OR REPLACE TABLE prep.sinistres AS
SELECT
  TRY_CAST(sinistre_id AS INTEGER) AS sinistre_id, TRY_CAST(contrat_id AS INTEGER) AS contrat_id,
  TRY_CAST(date_survenance AS DATE) AS date_survenance, TRY_CAST(date_declaration AS DATE) AS date_declaration,
  garantie, statut, TRY_CAST(reserve_initiale AS DOUBLE) AS reserve_initiale, _source_file, _row_num
FROM raw.sinistres;

-- Règlements : l'en-tête varie (montant / montant_eur) -> COALESCE. rang_occ > 1 = re-livraison.
CREATE OR REPLACE TABLE prep.reglements AS
SELECT
  TRY_CAST(paiement_id AS INTEGER) AS paiement_id, TRY_CAST(sinistre_id AS INTEGER) AS sinistre_id,
  TRY_CAST(date_paiement AS DATE) AS date_paiement,
  COALESCE(TRY_CAST(montant AS DOUBLE), TRY_CAST(montant_eur AS DOUBLE)) AS montant,
  ROW_NUMBER() OVER (PARTITION BY paiement_id ORDER BY _source_file, _row_num) AS rang_occ,
  REPLACE(REGEXP_EXTRACT(_source_file, '(\d{4}_\d{2})', 1), '_', '-') AS mois_fichier,
  STRFTIME(TRY_CAST(date_paiement AS DATE), '%Y-%m') AS mois_paiement,
  _source_file, _row_num
FROM raw.reglements;

CREATE OR REPLACE TABLE prep.audits AS
SELECT TRY_CAST(sinistre_id AS INTEGER) AS sinistre_id, TRY_CAST(date_audit AS DATE) AS date_audit,
       TRY_CAST(fraude_confirmee AS INTEGER) AS fraude_confirmee, _source_file, _row_num
FROM raw.audits;
