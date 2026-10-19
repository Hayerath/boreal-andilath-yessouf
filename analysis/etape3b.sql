-- Ratio S/P annuel avec et sans le sinistre 1129 (grande collision auto de 2023, 2,48 M EUR payés)
WITH p AS (SELECT annee, SUM(prime_acquise) AS prime FROM core.fact_exposition GROUP BY 1),
s AS (SELECT annee_survenance AS annee, SUM(montant_regle)::DOUBLE AS paye,
             SUM(montant_regle) FILTER (WHERE sinistre_id <> 1129)::DOUBLE AS paye_hors_1129
      FROM core.fact_sinistre GROUP BY 1)
SELECT annee, ROUND(paye / prime, 3) AS ratio_avec_1129, ROUND(paye_hors_1129 / prime, 3) AS ratio_hors_1129
FROM s JOIN p USING (annee) ORDER BY annee;
