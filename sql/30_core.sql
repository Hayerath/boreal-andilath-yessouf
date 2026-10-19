-- CŒUR : schéma en étoile. Dimensions reconstruites à chaque run (sources en instantané) ;
-- core.fact_reglement est INCRÉMENTALE (paiements immuables, insert-only, NOT EXISTS).

CREATE OR REPLACE TABLE core.dim_date AS
SELECT STRFTIME(d,'%Y%m%d')::INTEGER AS date_key, d::DATE AS date, YEAR(d) AS annee, MONTH(d) AS mois,
       QUARTER(d) AS trimestre, STRFTIME(d,'%Y-%m') AS annee_mois, DATE_TRUNC('month', d)::DATE AS debut_mois,
       (d::DATE > DATE '${EXTRACT_DATE}') AS est_futur
FROM GENERATE_SERIES(DATE '2020-01-01', DATE '2025-12-31', INTERVAL 1 DAY) t(d);

-- Client : instantané CRM, SCD type 2 prêt (valid_from / valid_to / is_current), une seule version aujourd'hui.
CREATE OR REPLACE TABLE core.dim_client AS
SELECT client_id, date_naissance, region, csp, consent_marketing, email_hash,
       DATE '${EXTRACT_DATE}' AS valid_from, DATE '9999-12-31' AS valid_to, TRUE AS is_current
FROM prep.clients WHERE rang_email = 1;

CREATE OR REPLACE TABLE core.client_alias AS
SELECT client_id AS client_id_doublon, client_id_survivant FROM prep.clients WHERE rang_email > 1;

CREATE OR REPLACE TABLE core._ctr AS
SELECT c.contrat_id, COALESCE(cl.client_id_survivant, c.client_id) AS client_id, c.produit, c.date_effet,
       c.date_resiliation, c.formule, c.canal_distribution, c.zone_risque, c.franchise, c.bonus_malus,
       c.puissance_cv, c.surface_m2, c.prime_annuelle,
       CASE WHEN d.date_naissance IS NULL THEN 'INCONNU'
            WHEN DATE_SUB('year', d.date_naissance, c.date_effet) < 25 THEN '<25'
            WHEN DATE_SUB('year', d.date_naissance, c.date_effet) < 35 THEN '25-34'
            WHEN DATE_SUB('year', d.date_naissance, c.date_effet) < 50 THEN '35-49'
            WHEN DATE_SUB('year', d.date_naissance, c.date_effet) < 65 THEN '50-64'
            ELSE '65+' END AS tranche_age
FROM prep.contrats_ok c
JOIN prep.clients cl ON cl.client_id = c.client_id
LEFT JOIN core.dim_client d ON d.client_id = cl.client_id_survivant;

-- Segment de risque : produit x zone x formule x canal x tranche d'âge à la souscription
CREATE OR REPLACE TABLE core.dim_segment_risque AS
SELECT ROW_NUMBER() OVER (ORDER BY produit, zone_risque, formule, canal_distribution, tranche_age) AS segment_sk, *
FROM (SELECT DISTINCT produit, zone_risque, formule, canal_distribution, tranche_age FROM core._ctr);

-- Contrat : SCD type 1 (attributs contractuels figés dans la source ; un avenant serait un nouveau contrat)
CREATE OR REPLACE TABLE core.dim_contrat AS
SELECT c.contrat_id, c.client_id, s.segment_sk, c.produit, c.formule, c.canal_distribution, c.zone_risque,
       c.franchise, c.bonus_malus, c.puissance_cv, c.surface_m2, c.prime_annuelle, c.tranche_age,
       c.date_effet, c.date_resiliation,
       STRFTIME(c.date_effet,'%Y%m%d')::INTEGER AS date_effet_key,
       STRFTIME(c.date_resiliation,'%Y%m%d')::INTEGER AS date_resiliation_key,
       (c.date_resiliation IS NOT NULL) AS est_resilie
FROM core._ctr c
JOIN core.dim_segment_risque s USING (produit, zone_risque, formule, canal_distribution, tranche_age);
DROP TABLE core._ctr;

CREATE OR REPLACE TABLE core.dim_garantie AS
SELECT ROW_NUMBER() OVER (ORDER BY produit, garantie) AS garantie_sk, produit, garantie AS garantie_code,
       CASE garantie WHEN 'RC' THEN 'Responsabilité civile' WHEN 'COLLISION' THEN 'Collision'
            WHEN 'VOL' THEN 'Vol' WHEN 'BRIS_GLACE' THEN 'Bris de glace' WHEN 'DEGAT_EAUX' THEN 'Dégâts des eaux'
            WHEN 'INCENDIE' THEN 'Incendie' WHEN 'TEMPETE' THEN 'Tempête' ELSE garantie END AS libelle
FROM (SELECT DISTINCT c.produit, s.garantie FROM prep.sinistres_ok s JOIN prep.contrats_ok c USING (contrat_id));

-- FAIT EXPOSITION. Grain : 1 contrat x 1 année civile avec couverture (> 0 jour).
-- Convention : date d'effet incluse, date de résiliation exclue, observation jusqu'au 30/06/2025 inclus.
-- exposition_annee_police = jours couverts / jours de l'année civile (1,0 = une année complète).
CREATE OR REPLACE TABLE core.fact_exposition AS
WITH b AS (
  SELECT c.contrat_id, c.client_id, c.segment_sk, c.prime_annuelle, y.annee,
         GREATEST(c.date_effet, MAKE_DATE(y.annee,1,1)) AS d0,
         LEAST(COALESCE(c.date_resiliation, DATE '${OBS_END}'), DATE '${OBS_END}', MAKE_DATE(y.annee+1,1,1)) AS d1,
         (MAKE_DATE(y.annee+1,1,1) - MAKE_DATE(y.annee,1,1)) AS jours_annee
  FROM core.dim_contrat c CROSS JOIN (SELECT UNNEST(RANGE(2020,2026)) AS annee) y)
SELECT contrat_id, annee, client_id, segment_sk, d0 AS date_debut, d1 AS date_fin_exclue,
       (d1 - d0) AS jours_couverture, jours_annee,
       (d1 - d0)::DOUBLE / jours_annee AS exposition_annee_police,
       prime_annuelle * (d1 - d0)::DOUBLE / jours_annee AS prime_acquise
FROM b WHERE d1 > d0;

-- FAIT RÈGLEMENT (incrémental). Grain : 1 paiement.
CREATE TABLE IF NOT EXISTS core.fact_reglement (
  paiement_id INTEGER, sinistre_id INTEGER, contrat_id INTEGER, date_key INTEGER, date_paiement DATE,
  montant DECIMAL(14,2), source_file VARCHAR, loaded_at TIMESTAMP);

INSERT INTO core.fact_reglement
SELECT r.paiement_id, r.sinistre_id, s.contrat_id, STRFTIME(r.date_paiement,'%Y%m%d')::INTEGER, r.date_paiement,
       r.montant::DECIMAL(14,2), r._source_file, CURRENT_TIMESTAMP
FROM prep.reglements_ok r JOIN prep.sinistres_ok s ON s.sinistre_id = r.sinistre_id
WHERE NOT EXISTS (SELECT 1 FROM core.fact_reglement f WHERE f.paiement_id = r.paiement_id);

-- FAIT SINISTRE. Grain : 1 sinistre déclaré (rejetés et sans suite inclus, distingués par statut).
CREATE OR REPLACE TABLE core.fact_sinistre AS
WITH r AS (SELECT sinistre_id, COUNT(*) AS nb, SUM(montant) AS total, MIN(date_paiement) AS premier,
                  MAX(date_paiement) AS dernier FROM core.fact_reglement GROUP BY sinistre_id)
SELECT s.sinistre_id, s.contrat_id, c.client_id, c.segment_sk, g.garantie_sk,
       STRFTIME(s.date_survenance,'%Y%m%d')::INTEGER AS date_survenance_key,
       STRFTIME(s.date_declaration,'%Y%m%d')::INTEGER AS date_declaration_key,
       s.date_survenance, s.date_declaration, YEAR(s.date_survenance) AS annee_survenance,
       s.statut, s.reserve_initiale::DECIMAL(14,2) AS reserve_initiale,
       CASE WHEN s.date_declaration >= s.date_survenance THEN (s.date_declaration - s.date_survenance) END AS delai_declaration_j,
       (s.date_declaration < s.date_survenance) AS anomalie_declaration_avant_survenance,
       (s.date_survenance < c.date_effet OR (c.date_resiliation IS NOT NULL AND s.date_survenance >= c.date_resiliation)) AS anomalie_hors_couverture,
       COALESCE(r.nb,0) AS nb_reglements, COALESCE(r.total,0)::DECIMAL(14,2) AS montant_regle,
       r.premier AS date_premier_reglement, r.dernier AS date_dernier_reglement
FROM prep.sinistres_ok s
JOIN core.dim_contrat c USING (contrat_id)
JOIN core.dim_garantie g ON g.produit = c.produit AND g.garantie_code = s.garantie
LEFT JOIN r USING (sinistre_id);

-- FAIT AUDIT. Grain : 1 audit (population auditée uniquement : ne pas extrapoler au portefeuille).
CREATE OR REPLACE TABLE core.fact_audit AS
SELECT sinistre_id, date_audit, STRFTIME(date_audit,'%Y%m%d')::INTEGER AS date_audit_key,
       (fraude_confirmee = 1) AS fraude_confirmee
FROM prep.audits_ok;
