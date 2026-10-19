-- Mauvaise méthode : sinistres avec suite / nombre de contrats (contre-exemple pour le dossier)
SELECT c.produit,
       COUNT(*) FILTER (WHERE s.statut IN ('CLOTURE','OUVERT')) AS sinistres_avec_suite,
       COUNT(DISTINCT c.contrat_id) AS contrats,
       ROUND(COUNT(*) FILTER (WHERE s.statut IN ('CLOTURE','OUVERT')) * 1.0 / COUNT(DISTINCT c.contrat_id), 3) AS freq_naive
FROM core.dim_contrat c LEFT JOIN core.fact_sinistre s USING (contrat_id)
GROUP BY 1;

-- Bonne méthode : sinistres avec suite / années-police
SELECT produit, ROUND(SUM(exposition), 1) AS annees_police, SUM(sinistres_avec_suite) AS sinistres_avec_suite,
       ROUND(SUM(sinistres_avec_suite) / SUM(exposition), 4) AS frequence
FROM marts.portefeuille_annee_produit GROUP BY 1;
