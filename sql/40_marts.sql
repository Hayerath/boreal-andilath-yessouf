-- MARTS : tables prêtes pour le dashboard. Sinistres rattachés à l'année de SURVENANCE.
CREATE OR REPLACE TABLE marts.portefeuille_annee_produit AS
WITH e AS (
  SELECT f.annee, c.produit, SUM(f.exposition_annee_police) AS exposition, SUM(f.prime_acquise) AS prime_acquise,
         COUNT(DISTINCT f.contrat_id) AS contrats_exposes
  FROM core.fact_exposition f JOIN core.dim_contrat c USING (contrat_id) GROUP BY ALL),
s AS (
  SELECT f.annee_survenance AS annee, c.produit, COUNT(*) AS sinistres_declares,
         COUNT(*) FILTER (WHERE f.statut IN ('CLOTURE','OUVERT')) AS sinistres_avec_suite,
         COUNT(*) FILTER (WHERE f.statut = 'SANS_SUITE') AS sinistres_sans_suite,
         COUNT(*) FILTER (WHERE f.statut = 'REJETE') AS sinistres_rejetes,
         SUM(f.montant_regle)::DOUBLE AS montant_regle
  FROM core.fact_sinistre f JOIN core.dim_contrat c USING (contrat_id) GROUP BY ALL)
SELECT COALESCE(e.annee, s.annee) AS annee, COALESCE(e.produit, s.produit) AS produit,
       e.contrats_exposes, e.exposition, e.prime_acquise, s.sinistres_declares, s.sinistres_avec_suite,
       s.sinistres_sans_suite, s.sinistres_rejetes, s.montant_regle,
       s.sinistres_avec_suite / e.exposition AS frequence_par_annee_police,
       s.montant_regle / NULLIF(s.sinistres_avec_suite,0) AS cout_moyen_par_sinistre,
       s.montant_regle / NULLIF(e.prime_acquise,0) AS ratio_sinistres_primes
FROM e FULL JOIN s ON e.annee = s.annee AND e.produit = s.produit;

-- ===================================================================================================
-- MARTS DASHBOARD (le dashboard ne lit QUE marts.*). Mesures additives : on somme, puis on divise.
-- Seuil de "sinistre extrême" : cumul payé > 500 000 EUR (règle qualité V07) -> 1 sinistre (n°1129).
-- ===================================================================================================

-- Page Portefeuille. Grain : mois x produit x zone x canal x région.
CREATE OR REPLACE TABLE marts.portefeuille_mois AS
WITH mois AS (SELECT DISTINCT debut_mois AS m, (debut_mois + INTERVAL 1 MONTH)::DATE AS fin_excl
              FROM core.dim_date WHERE debut_mois <= DATE '${EXTRACT_DATE}'),
c AS (SELECT c.contrat_id, c.produit, c.zone_risque, c.canal_distribution AS canal, COALESCE(cl.region, 'INCONNU') AS region,
             c.prime_annuelle, c.date_effet, c.date_resiliation
      FROM core.dim_contrat c LEFT JOIN core.dim_client cl USING (client_id)),
x AS (SELECT m.m, m.fin_excl, c.*,
             GREATEST(c.date_effet, m.m) AS d0,
             LEAST(COALESCE(c.date_resiliation, DATE '${OBS_END}'), DATE '${OBS_END}', m.fin_excl) AS d1,
             (MAKE_DATE(YEAR(m.m) + 1, 1, 1) - MAKE_DATE(YEAR(m.m), 1, 1)) AS jours_annee,
             LEAST(m.fin_excl, DATE '${OBS_END}') - 1 AS dernier_jour
      FROM mois m CROSS JOIN c WHERE c.date_effet < m.fin_excl),
e AS (SELECT m AS mois, produit, zone_risque, canal, region,
             SUM(CASE WHEN d1 > d0 THEN (d1 - d0)::DOUBLE / jours_annee ELSE 0 END) AS exposition,
             SUM(CASE WHEN d1 > d0 THEN prime_annuelle * (d1 - d0)::DOUBLE / jours_annee ELSE 0 END) AS prime_acquise,
             COUNT(*) FILTER (WHERE date_effet <= dernier_jour AND (date_resiliation IS NULL OR date_resiliation > dernier_jour)) AS contrats_actifs_fin_mois,
             COUNT(*) FILTER (WHERE date_effet >= m) AS nouveaux_contrats,
             COUNT(*) FILTER (WHERE date_resiliation >= m AND date_resiliation < fin_excl) AS resiliations
      FROM x GROUP BY ALL),
s AS (SELECT DATE_TRUNC('month', f.date_survenance)::DATE AS mois, c.produit, c.zone_risque, c.canal_distribution AS canal,
             COALESCE(cl.region, 'INCONNU') AS region,
             COUNT(*) AS sinistres_declares,
             COUNT(*) FILTER (WHERE f.statut IN ('CLOTURE','OUVERT')) AS sinistres_avec_suite,
             COUNT(*) FILTER (WHERE f.statut IN ('CLOTURE','OUVERT') AND f.montant_regle > 500000) AS sinistres_extremes,
             COALESCE(SUM(f.montant_regle), 0)::DOUBLE AS paye,
             COALESCE(SUM(f.montant_regle) FILTER (WHERE f.montant_regle <= 500000), 0)::DOUBLE AS paye_hors_extreme
      FROM core.fact_sinistre f JOIN core.dim_contrat c USING (contrat_id) LEFT JOIN core.dim_client cl ON cl.client_id = c.client_id
      GROUP BY ALL)
SELECT COALESCE(e.mois, s.mois) AS mois, YEAR(COALESCE(e.mois, s.mois)) AS annee, MONTH(COALESCE(e.mois, s.mois)) AS mois_num,
       COALESCE(e.produit, s.produit) AS produit, COALESCE(e.zone_risque, s.zone_risque) AS zone_risque,
       COALESCE(e.canal, s.canal) AS canal, COALESCE(e.region, s.region) AS region,
       COALESCE(e.exposition, 0) AS exposition, COALESCE(e.prime_acquise, 0) AS prime_acquise,
       COALESCE(e.contrats_actifs_fin_mois, 0) AS contrats_actifs_fin_mois, COALESCE(e.nouveaux_contrats, 0) AS nouveaux_contrats,
       COALESCE(e.resiliations, 0) AS resiliations,
       COALESCE(s.sinistres_declares, 0) AS sinistres_declares, COALESCE(s.sinistres_avec_suite, 0) AS sinistres_avec_suite,
       COALESCE(s.sinistres_extremes, 0) AS sinistres_extremes,
       COALESCE(s.paye, 0) AS paye, COALESCE(s.paye_hors_extreme, 0) AS paye_hors_extreme
FROM e FULL JOIN s ON e.mois = s.mois AND e.produit = s.produit AND e.zone_risque = s.zone_risque
                  AND e.canal = s.canal AND e.region = s.region;

-- Page Technique. Grain : année x produit x zone x formule x canal x tranche d'âge.
CREATE OR REPLACE TABLE marts.technique_segment AS
WITH e AS (SELECT f.annee, g.produit, g.zone_risque, g.formule, g.canal_distribution AS canal, g.tranche_age,
                  SUM(f.exposition_annee_police) AS exposition, SUM(f.prime_acquise) AS prime_acquise
           FROM core.fact_exposition f JOIN core.dim_segment_risque g USING (segment_sk) GROUP BY ALL),
s AS (SELECT f.annee_survenance AS annee, g.produit, g.zone_risque, g.formule, g.canal_distribution AS canal, g.tranche_age,
             COUNT(*) FILTER (WHERE f.statut IN ('CLOTURE','OUVERT')) AS sinistres_avec_suite,
             COUNT(*) FILTER (WHERE f.statut = 'SANS_SUITE') AS sinistres_sans_suite,
             COUNT(*) FILTER (WHERE f.statut = 'REJETE') AS sinistres_rejetes,
             COUNT(*) FILTER (WHERE f.statut IN ('CLOTURE','OUVERT') AND f.montant_regle > 500000) AS sinistres_extremes,
             COALESCE(SUM(f.montant_regle), 0)::DOUBLE AS paye,
             COALESCE(SUM(f.montant_regle) FILTER (WHERE f.montant_regle <= 500000), 0)::DOUBLE AS paye_hors_extreme,
             COALESCE(SUM(GREATEST(f.reserve_initiale - f.montant_regle, 0)) FILTER (WHERE f.statut = 'OUVERT'), 0)::DOUBLE AS reserve_residuelle_ouverts
      FROM core.fact_sinistre f JOIN core.dim_segment_risque g USING (segment_sk) GROUP BY ALL),
r AS (SELECT YEAR(c.date_resiliation) AS annee, g.produit, g.zone_risque, g.formule, g.canal_distribution AS canal, g.tranche_age,
             COUNT(*) AS resiliations
      FROM core.dim_contrat c JOIN core.dim_segment_risque g USING (segment_sk) WHERE c.date_resiliation IS NOT NULL GROUP BY ALL)
SELECT COALESCE(e.annee, s.annee, r.annee) AS annee, COALESCE(e.produit, s.produit, r.produit) AS produit,
       COALESCE(e.zone_risque, s.zone_risque, r.zone_risque) AS zone_risque, COALESCE(e.formule, s.formule, r.formule) AS formule,
       COALESCE(e.canal, s.canal, r.canal) AS canal, COALESCE(e.tranche_age, s.tranche_age, r.tranche_age) AS tranche_age,
       COALESCE(e.exposition, 0) AS exposition, COALESCE(e.prime_acquise, 0) AS prime_acquise,
       COALESCE(s.sinistres_avec_suite, 0) AS sinistres_avec_suite, COALESCE(s.sinistres_sans_suite, 0) AS sinistres_sans_suite,
       COALESCE(s.sinistres_rejetes, 0) AS sinistres_rejetes, COALESCE(s.sinistres_extremes, 0) AS sinistres_extremes,
       COALESCE(s.paye, 0) AS paye, COALESCE(s.paye_hors_extreme, 0) AS paye_hors_extreme,
       COALESCE(s.reserve_residuelle_ouverts, 0) AS reserve_residuelle_ouverts, COALESCE(r.resiliations, 0) AS resiliations
FROM e FULL JOIN s ON e.annee = s.annee AND e.produit = s.produit AND e.zone_risque = s.zone_risque AND e.formule = s.formule AND e.canal = s.canal AND e.tranche_age = s.tranche_age
       FULL JOIN r ON COALESCE(e.annee, s.annee) = r.annee AND COALESCE(e.produit, s.produit) = r.produit AND COALESCE(e.zone_risque, s.zone_risque) = r.zone_risque
                  AND COALESCE(e.formule, s.formule) = r.formule AND COALESCE(e.canal, s.canal) = r.canal AND COALESCE(e.tranche_age, s.tranche_age) = r.tranche_age;

-- Décomposition annuelle : ratio = (fréquence x coût moyen) / prime moyenne -> effets additifs en logarithme.
-- Le volume s'annule dans le ratio ; il agit sur les montants et sur le poids des segments (mix).
CREATE OR REPLACE TABLE marts.decomposition_annuelle AS
WITH g AS (SELECT annee, SUM(exposition) AS expo, SUM(prime_acquise) AS prime, SUM(sinistres_avec_suite) AS n,
                  SUM(sinistres_extremes) AS ne, SUM(paye) AS paye, SUM(paye_hors_extreme) AS paye_h
           FROM marts.technique_segment GROUP BY 1),
t AS (SELECT annee, 'tous' AS perimetre, expo, prime, n, paye FROM g
      UNION ALL SELECT annee, 'hors_extreme', expo, prime, n - ne, paye_h FROM g),
k AS (SELECT annee, perimetre, expo AS exposition, prime AS prime_acquise, n AS sinistres_avec_suite, paye,
             n / expo AS frequence, paye / NULLIF(n, 0) AS cout_moyen, prime / expo AS prime_moyenne, paye / prime AS ratio FROM t)
SELECT annee, perimetre, exposition, prime_acquise, sinistres_avec_suite, paye, frequence, cout_moyen, prime_moyenne, ratio,
       LN(ratio / LAG(ratio) OVER w) AS var_ratio_log, LN(frequence / LAG(frequence) OVER w) AS effet_frequence,
       LN(cout_moyen / LAG(cout_moyen) OVER w) AS effet_cout, -LN(prime_moyenne / LAG(prime_moyenne) OVER w) AS effet_prime,
       LN(exposition / LAG(exposition) OVER w) AS variation_volume_log,
       CASE annee WHEN 2020 THEN 'démarrage du portefeuille' WHEN 2025 THEN 'partielle : 6 mois, dossiers en cours' ELSE 'complète' END AS statut_annee
FROM k WINDOW w AS (PARTITION BY perimetre ORDER BY annee);

-- Contribution de chaque segment (produit x zone) à la variation du ratio global d'une année à l'autre.
CREATE OR REPLACE TABLE marts.contribution_segment AS
WITH s AS (SELECT annee, produit, zone_risque, SUM(prime_acquise) AS prime, SUM(paye) AS paye, SUM(paye_hors_extreme) AS paye_h
           FROM marts.technique_segment GROUP BY ALL),
u AS (SELECT annee, produit, zone_risque, 'tous' AS perimetre, prime, paye AS p, SUM(prime) OVER (PARTITION BY annee) AS prime_tot FROM s
      UNION ALL SELECT annee, produit, zone_risque, 'hors_extreme', prime, paye_h, SUM(prime) OVER (PARTITION BY annee) FROM s)
SELECT n.annee, n.perimetre, n.produit, n.zone_risque, p.prime / p.prime_tot AS poids_avant, n.prime / n.prime_tot AS poids_apres,
       p.p / NULLIF(p.prime, 0) AS ratio_avant, n.p / NULLIF(n.prime, 0) AS ratio_apres,
       n.p / n.prime_tot - p.p / p.prime_tot AS contribution
FROM u n JOIN u p ON p.produit = n.produit AND p.zone_risque = n.zone_risque AND p.perimetre = n.perimetre AND p.annee = n.annee - 1;

-- Rétention : part des contrats encore en vigueur au k-ième anniversaire (cellule calculée seulement si l'anniversaire est observé).
CREATE OR REPLACE TABLE marts.retention_cohorte AS
WITH x AS (SELECT c.produit, YEAR(c.date_effet) AS cohorte, k.k, (c.date_effet + INTERVAL (k.k * 12) MONTH)::DATE AS anniv, c.date_resiliation
           FROM core.dim_contrat c CROSS JOIN (SELECT UNNEST(RANGE(1, 6)) AS k) k)
SELECT produit, cohorte, k AS annee_anniversaire, COUNT(*) AS contrats_eligibles,
       COUNT(*) FILTER (WHERE date_resiliation IS NULL OR date_resiliation > anniv) AS contrats_retenus,
       COUNT(*) FILTER (WHERE date_resiliation IS NULL OR date_resiliation > anniv)::DOUBLE / COUNT(*) AS retention
FROM x WHERE anniv <= DATE '${EXTRACT_DATE}' GROUP BY ALL;

-- Valeur observée par client (pseudonymisé) = primes acquises - sinistres payés, au 30/06/2025. Aucune projection.
CREATE OR REPLACE TABLE marts.valeur_client AS
WITH p AS (SELECT client_id, SUM(prime_acquise) AS prime, SUM(exposition_annee_police) AS expo FROM core.fact_exposition GROUP BY 1),
s AS (SELECT client_id, SUM(montant_regle)::DOUBLE AS paye, COUNT(*) FILTER (WHERE statut IN ('CLOTURE','OUVERT')) AS nb_sinistres,
             BOOL_OR(montant_regle > 500000) AS a_sinistre_extreme FROM core.fact_sinistre GROUP BY 1),
k AS (SELECT client_id, COUNT(*) AS nb_contrats, COUNT(DISTINCT produit) AS nb_produits, YEAR(MIN(date_effet)) AS cohorte FROM core.dim_contrat GROUP BY 1)
SELECT c.client_id, c.region, c.csp, k.nb_contrats, k.nb_produits, k.cohorte,
       COALESCE(p.prime, 0) AS prime_acquise, COALESCE(p.expo, 0) AS exposition, COALESCE(s.paye, 0) AS paye,
       COALESCE(s.nb_sinistres, 0) AS nb_sinistres, COALESCE(s.a_sinistre_extreme, FALSE) AS client_sinistre_extreme,
       COALESCE(p.prime, 0) - COALESCE(s.paye, 0) AS valeur
FROM core.dim_client c JOIN k USING (client_id) LEFT JOIN p USING (client_id) LEFT JOIN s USING (client_id);

CREATE OR REPLACE TABLE marts.pareto_valeur AS
WITH d AS (SELECT 'tous' AS perimetre, client_id, valeur FROM marts.valeur_client
           UNION ALL SELECT 'hors_extreme', client_id, valeur FROM marts.valeur_client WHERE NOT client_sinistre_extreme),
r AS (SELECT *, ROW_NUMBER() OVER (PARTITION BY perimetre ORDER BY valeur DESC, client_id) AS rn,
             COUNT(*) OVER (PARTITION BY perimetre) AS n, SUM(valeur) OVER (PARTITION BY perimetre) AS tot FROM d),
c AS (SELECT perimetre, rn, n, tot, SUM(valeur) OVER (PARTITION BY perimetre ORDER BY rn) AS cum FROM r)
SELECT perimetre, CEIL(100.0 * rn / n)::INTEGER AS pct_clients, ARG_MAX(cum, rn) AS valeur_cumulee,
       ARG_MAX(cum, rn) / MAX(tot) AS part_cumulee_valeur FROM c GROUP BY perimetre, CEIL(100.0 * rn / n)::INTEGER;

CREATE OR REPLACE TABLE marts.profil_decile AS
WITH d AS (SELECT *, NTILE(10) OVER (ORDER BY valeur DESC, client_id) AS decile FROM marts.valeur_client WHERE NOT client_sinistre_extreme)
SELECT decile, COUNT(*) AS clients, AVG(exposition) AS exposition_moy, AVG(valeur / NULLIF(exposition, 0)) AS valeur_par_annee_police_moy,
       AVG(valeur) AS valeur_moy, AVG(prime_acquise) AS prime_moy, AVG(paye) AS paye_moy, AVG(nb_sinistres) AS sinistres_moy,
       AVG(nb_contrats) AS contrats_moy, AVG((nb_produits = 2)::INTEGER) AS part_multi_detenteurs
FROM d GROUP BY decile;

-- Délais de gestion par garantie (jours). Clôture = date du dernier règlement (la source ne fournit pas de date de clôture).
CREATE OR REPLACE TABLE marts.delais_garantie AS
WITH b AS (SELECT c.produit, g.garantie_code AS garantie, g.libelle, f.delai_declaration_j AS d1,
                  (f.date_premier_reglement - f.date_declaration) AS d2,
                  CASE WHEN f.statut = 'CLOTURE' AND f.nb_reglements > 0 THEN f.date_dernier_reglement - f.date_declaration END AS d3
           FROM core.fact_sinistre f JOIN core.dim_contrat c USING (contrat_id) JOIN core.dim_garantie g USING (garantie_sk)),
u AS (SELECT produit, garantie, libelle, 'declaration' AS etape, d1 AS delai FROM b
      UNION ALL SELECT produit, garantie, libelle, 'premier_reglement', d2 FROM b
      UNION ALL SELECT produit, garantie, libelle, 'cloture_approx', d3 FROM b)
SELECT produit, garantie, libelle, etape, COUNT(delai) AS n, QUANTILE_CONT(delai, 0.5) AS mediane, QUANTILE_CONT(delai, 0.75) AS q75,
       QUANTILE_CONT(delai, 0.90) AS q90, QUANTILE_CONT(delai, 0.95) AS q95, MAX(delai) AS maximum
FROM u WHERE delai IS NOT NULL GROUP BY produit, garantie, libelle, etape;

-- Audits : taux de confirmation = population AUDITÉE uniquement (pas le portefeuille).
CREATE OR REPLACE TABLE marts.audit_critere AS
WITH b AS (SELECT f.sinistre_id, c.produit, g.garantie_code AS garantie, f.statut,
                  CASE WHEN f.reserve_initiale < 1000 THEN '1. < 1 k' WHEN f.reserve_initiale < 5000 THEN '2. 1-5 k'
                       WHEN f.reserve_initiale < 20000 THEN '3. 5-20 k' ELSE '4. > 20 k' END AS tranche_reserve,
                  a.sinistre_id IS NOT NULL AS audite, COALESCE(a.fraude_confirmee, FALSE) AS fraude
           FROM core.fact_sinistre f JOIN core.dim_contrat c USING (contrat_id) JOIN core.dim_garantie g USING (garantie_sk)
           LEFT JOIN core.fact_audit a USING (sinistre_id)),
u AS (SELECT 'global' AS critere, 'tous' AS modalite, * FROM b
      UNION ALL SELECT 'produit', produit, * FROM b UNION ALL SELECT 'garantie', garantie, * FROM b
      UNION ALL SELECT 'statut', statut, * FROM b UNION ALL SELECT 'tranche_reserve', tranche_reserve, * FROM b)
SELECT critere, modalite, COUNT(*) AS sinistres, COUNT(*) FILTER (WHERE audite) AS audites, COUNT(*) FILTER (WHERE fraude) AS fraudes_confirmees,
       COUNT(*) FILTER (WHERE fraude)::DOUBLE / NULLIF(COUNT(*) FILTER (WHERE audite), 0) AS taux_confirmation,
       COUNT(*) FILTER (WHERE audite)::DOUBLE / COUNT(*) AS couverture_audit
FROM u GROUP BY critere, modalite;

-- ---- Exploitation : état de la chaîne (vues sur les tables d'exploitation) ----
CREATE OR REPLACE VIEW marts.ops_chargement_source AS
WITH l AS (SELECT source, file, MAX(logged_at) FILTER (WHERE status = 'LOADED') AS dernier_chargement,
                  ARG_MAX(rows_read, logged_at) FILTER (WHERE status = 'LOADED') AS lues,
                  ARG_MAX(rows_loaded, logged_at) FILTER (WHERE status = 'LOADED') AS chargees,
                  ARG_MAX(rows_rejected, logged_at) FILTER (WHERE status = 'LOADED') AS rejetees,
                  ARG_MAX(status, logged_at) AS dernier_statut
           FROM ops.ingestion_log GROUP BY source, file)
SELECT source, COUNT(*) AS fichiers, SUM(lues) AS lignes_lues, SUM(chargees) AS lignes_chargees, SUM(rejetees) AS lignes_rejetees_lecture,
       MAX(dernier_chargement) AS dernier_chargement, COUNT(*) FILTER (WHERE dernier_statut = 'FAILED') AS fichiers_en_echec
FROM l GROUP BY source;

CREATE OR REPLACE VIEW marts.ops_fraicheur AS
SELECT 'clients' AS source, NULL::DATE AS derniere_date_metier, DATE '${EXTRACT_DATE}' AS date_extraction
UNION ALL SELECT 'contrats', MAX(date_effet), DATE '${EXTRACT_DATE}' FROM core.dim_contrat
UNION ALL SELECT 'sinistres', MAX(date_declaration), DATE '${EXTRACT_DATE}' FROM core.fact_sinistre
UNION ALL SELECT 'reglements', MAX(date_paiement), DATE '${EXTRACT_DATE}' FROM core.fact_reglement
UNION ALL SELECT 'audits', MAX(date_audit), DATE '${EXTRACT_DATE}' FROM core.fact_audit;

CREATE OR REPLACE VIEW marts.ops_rejets_regle AS
SELECT rule_id, entity, COUNT(*) AS lignes, ANY_VALUE(SUBSTR(motif, 1, 90)) AS exemple_motif FROM quarantine.rows GROUP BY rule_id, entity
UNION ALL SELECT 'LECTURE', source, COUNT(*), ANY_VALUE(SUBSTR(motif, 1, 90)) FROM quarantine.raw_rejects GROUP BY source;

CREATE OR REPLACE VIEW marts.ops_regles_qualite AS
SELECT rule_id, dimension, entity, description, severity, treatment, volume FROM dq.rule_results;

CREATE OR REPLACE VIEW marts.ops_tests AS
SELECT test_id, description, violations, status, executed_at FROM ops.test_results
WHERE run_id = (SELECT run_id FROM ops.test_results ORDER BY executed_at DESC LIMIT 1);

CREATE OR REPLACE VIEW marts.ops_runs AS
SELECT run_id, started_at, finished_at, status, n_tests, n_tests_failed, message FROM ops.pipeline_runs;
