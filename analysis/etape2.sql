WITH seg AS (
  SELECT segment_sk, produit, 'zone' AS axe, CAST(zone_risque AS VARCHAR) AS modalite FROM core.dim_segment_risque
  UNION ALL SELECT segment_sk, produit, 'formule', formule FROM core.dim_segment_risque
  UNION ALL SELECT segment_sk, produit, 'canal', canal_distribution FROM core.dim_segment_risque
  UNION ALL SELECT segment_sk, produit, 'age', tranche_age FROM core.dim_segment_risque),
e AS (SELECT s.produit, s.axe, s.modalite, SUM(f.exposition_annee_police) AS expo, SUM(f.prime_acquise) AS prime
      FROM core.fact_exposition f JOIN seg s USING (segment_sk) GROUP BY ALL),
x AS (SELECT s.produit, s.axe, s.modalite,
             COUNT(*) FILTER (WHERE f.statut IN ('CLOTURE','OUVERT')) AS n_suite,
             COUNT(*) FILTER (WHERE f.statut = 'SANS_SUITE') AS n_sans_suite,
             COUNT(*) FILTER (WHERE f.statut = 'REJETE') AS n_rejetes,
             SUM(f.montant_regle) AS paye
      FROM core.fact_sinistre f JOIN seg s USING (segment_sk) GROUP BY ALL),
r AS (SELECT s.produit, s.axe, s.modalite, COUNT(*) FILTER (WHERE c.est_resilie) AS nb_resilies
      FROM core.dim_contrat c JOIN seg s USING (segment_sk) GROUP BY ALL)
SELECT axe, produit, modalite, ROUND(expo) AS annees_police, ROUND(prime) AS prime_acquise,
       n_suite, ROUND(n_suite / expo, 4) AS frequence, ROUND(paye / NULLIF(n_suite, 0)) AS cout_moyen,
       ROUND(prime / expo) AS prime_moyenne, ROUND(paye / prime, 3) AS ratio_SP,
       ROUND(nb_resilies / expo, 4) AS resil_par_annee_police
FROM e JOIN x USING (produit, axe, modalite) JOIN r USING (produit, axe, modalite)
ORDER BY axe, produit, modalite;
