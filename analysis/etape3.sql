-- A. Évolution annuelle du ratio S/P et décomposition (sinistres rattachés à l'année de survenance)
WITH e AS (SELECT annee, SUM(exposition_annee_police) AS expo, SUM(prime_acquise) AS prime FROM core.fact_exposition GROUP BY 1),
s AS (SELECT annee_survenance AS annee, COUNT(*) FILTER (WHERE statut IN ('CLOTURE','OUVERT')) AS n,
             SUM(montant_regle)::DOUBLE AS paye FROM core.fact_sinistre GROUP BY 1),
t AS (SELECT annee, expo, prime, n, paye, n / expo AS f, paye / n AS c, prime / expo AS pi, paye / prime AS r FROM e JOIN s USING (annee))
SELECT annee, ROUND(expo) AS annees_police, n AS sinistres, ROUND(paye) AS paye, ROUND(prime) AS prime,
       ROUND(f, 4) AS frequence, ROUND(c) AS cout_moyen, ROUND(pi) AS prime_moyenne, ROUND(r, 3) AS ratio,
       ROUND(LN(r / LAG(r) OVER w), 3) AS var_ratio,
       ROUND(LN(f / LAG(f) OVER w), 3) AS effet_frequence,
       ROUND(LN(c / LAG(c) OVER w), 3) AS effet_cout,
       ROUND(-LN(pi / LAG(pi) OVER w), 3) AS effet_prime,
       ROUND(LN(expo / LAG(expo) OVER w), 3) AS info_variation_volume
FROM t WINDOW w AS (ORDER BY annee) ORDER BY annee;

-- B. Contribution de chaque segment (produit x zone) à la variation du ratio global, années 2023 et 2024
WITH e AS (SELECT f.annee, c.produit, c.zone_risque, SUM(f.prime_acquise) AS prime
           FROM core.fact_exposition f JOIN core.dim_contrat c USING (contrat_id) GROUP BY ALL),
s AS (SELECT f.annee_survenance AS annee, c.produit, c.zone_risque, SUM(f.montant_regle)::DOUBLE AS paye
      FROM core.fact_sinistre f JOIN core.dim_contrat c USING (contrat_id) GROUP BY ALL),
t AS (SELECT e.annee, e.produit, e.zone_risque, e.prime, COALESCE(s.paye, 0) AS paye,
             SUM(e.prime) OVER (PARTITION BY e.annee) AS prime_tot
      FROM e LEFT JOIN s USING (annee, produit, zone_risque)),
u AS (SELECT annee, produit, zone_risque, prime / prime_tot AS w, paye / prime AS r, paye / prime_tot AS contrib FROM t)
SELECT n.annee, n.produit, n.zone_risque, ROUND(p.w, 3) AS poids_avant, ROUND(n.w, 3) AS poids_apres,
       ROUND(p.r, 3) AS ratio_avant, ROUND(n.r, 3) AS ratio_apres,
       ROUND(n.contrib - p.contrib, 4) AS contribution_au_ratio_global
FROM u n JOIN u p ON p.produit = n.produit AND p.zone_risque = n.zone_risque AND p.annee = n.annee - 1
WHERE n.annee IN (2023, 2024) ORDER BY n.annee, contribution_au_ratio_global DESC;
