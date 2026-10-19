-- Sinistre 1129 : identité, puis ratio auto par zone avec et sans ce dossier
SELECT s.sinistre_id, c.produit, c.zone_risque, c.formule, c.canal_distribution, c.tranche_age, g.garantie_code AS garantie, s.statut,
       s.montant_regle, s.reserve_initiale
FROM core.fact_sinistre s JOIN core.dim_contrat c USING (contrat_id) JOIN core.dim_garantie g USING (garantie_sk) WHERE s.sinistre_id = 1129;

WITH p AS (SELECT c.zone_risque, SUM(f.prime_acquise) AS prime
           FROM core.fact_exposition f JOIN core.dim_contrat c USING (contrat_id)
           WHERE c.produit = 'AUTO' GROUP BY 1),
s AS (SELECT c.zone_risque, SUM(f.montant_regle) AS paye,
             SUM(f.montant_regle) FILTER (WHERE f.sinistre_id <> 1129) AS paye_hors_1129
      FROM core.fact_sinistre f JOIN core.dim_contrat c USING (contrat_id)
      WHERE c.produit = 'AUTO' GROUP BY 1)
SELECT zone_risque, ROUND(paye / prime, 3) AS ratio_avec_1129, ROUND(paye_hors_1129 / prime, 3) AS ratio_hors_1129
FROM p JOIN s USING (zone_risque) ORDER BY 1;
