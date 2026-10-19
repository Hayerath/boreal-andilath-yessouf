-- L3 : distinguer payés, réserves des dossiers ouverts, sans suite et rejetés, par année de survenance
WITH p AS (SELECT annee, SUM(prime_acquise) AS prime FROM core.fact_exposition GROUP BY 1),
s AS (SELECT annee_survenance AS annee,
        COUNT(*) AS declares,
        COUNT(*) FILTER (WHERE statut = 'CLOTURE') AS clotures,
        COUNT(*) FILTER (WHERE statut = 'OUVERT') AS ouverts,
        COUNT(*) FILTER (WHERE statut = 'SANS_SUITE') AS sans_suite,
        COUNT(*) FILTER (WHERE statut = 'REJETE') AS rejetes,
        SUM(montant_regle)::DOUBLE AS paye,
        SUM(GREATEST(reserve_initiale - montant_regle, 0)) FILTER (WHERE statut = 'OUVERT')::DOUBLE AS reserve_residuelle
      FROM core.fact_sinistre GROUP BY 1)
SELECT annee, declares, clotures, ouverts, sans_suite, rejetes,
       ROUND(100.0 * (sans_suite + rejetes) / declares, 1) AS pct_sans_effet,
       ROUND(paye) AS paye, ROUND(COALESCE(reserve_residuelle, 0)) AS reserve_residuelle,
       ROUND(prime) AS prime_acquise,
       ROUND(paye / prime, 3) AS ratio_paye,
       ROUND((paye + COALESCE(reserve_residuelle, 0)) / prime, 3) AS ratio_paye_plus_reserve
FROM s JOIN p USING (annee) ORDER BY annee;
