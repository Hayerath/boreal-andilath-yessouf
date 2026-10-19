SELECT s.sinistre_id, c.produit, c.zone_risque, c.canal_distribution, c.formule,
       c.tranche_age, s.annee_survenance, s.montant_regle
FROM core.fact_sinistre s JOIN core.dim_contrat c USING (contrat_id)
WHERE s.sinistre_id = 1129;