# Règles de qualité et tests (généré depuis l'entrepôt)

36 règles mesurées, dont 14 avec au moins une anomalie.

| Règle | Dimension | Table | Contrôle | Gravité | Volume | Traitement |
|---|---|---|---|---|---:|---|
| C01 | Complétude | clients | Date de naissance manquante | MINEURE | 226 | Signaler (âge inconnu, tranche 'INCONNU') |
| C02 | Complétude | contrats | Champ obligatoire manquant (produit, date d'effet, prime) | BLOQUANTE | 0 | Exclure (quarantaine) |
| C03 | Complétude | contrats | Champ propre au produit manquant (AUTO sans bonus-malus/puissance, HABITATION sans surface) | MAJEURE | 0 | Signaler |
| C04 | Complétude | sinistres | Champ obligatoire manquant (dates, garantie, statut) | BLOQUANTE | 0 | Exclure (quarantaine) |
| K01 | Cohérence métier | reglements | Paiement sur un sinistre REJETE ou SANS_SUITE | MAJEURE | 0 | Signaler |
| K02 | Cohérence métier | sinistres | Réserve incohérente avec le statut (CLOTURE/OUVERT à 0, REJETE/SANS_SUITE > 0) | MAJEURE | 0 | Signaler |
| K03 | Cohérence métier | audits | Audit sur un sinistre OUVERT ou SANS_SUITE | MINEURE | 36 | Signaler (conservé, population précisée dans l'analyse) |
| K04 | Cohérence métier | sinistres | Sinistre CLOTURE sans aucun règlement | MAJEURE | 0 | Signaler |
| R01 | Cohérence inter-tables | contrats | Client référencé absent du CRM | BLOQUANTE | 0 | Exclure (quarantaine) |
| R02 | Cohérence inter-tables | sinistres | Contrat référencé absent | BLOQUANTE | 0 | Exclure (quarantaine, règle P01) |
| R03 | Cohérence inter-tables | reglements | Sinistre référencé absent | BLOQUANTE | 0 | Exclure (quarantaine, règle P02) |
| R04 | Cohérence inter-tables | audits | Sinistre audité absent | BLOQUANTE | 0 | Exclure (quarantaine, règle P03) |
| T01 | Cohérence temporelle | contrats | Résiliation antérieure à la date d'effet | BLOQUANTE | 20 | Exclure (quarantaine) + sinistres rattachés |
| T02 | Cohérence temporelle | contrats | Résiliation le jour de l'effet (couverture nulle) | MINEURE | 6 | Signaler (aucune ligne d'exposition générée) |
| T03 | Cohérence temporelle | sinistres | Déclaration antérieure à la survenance | MAJEURE | 15 | Signaler ; délai de déclaration non calculé |
| T04 | Cohérence temporelle | sinistres | Survenance avant la date d'effet du contrat | MAJEURE | 17 | Signaler (drapeau anomalie_hors_couverture) |
| T05 | Cohérence temporelle | sinistres | Survenance après la résiliation du contrat | MAJEURE | 1 | Signaler (drapeau anomalie_hors_couverture) |
| T06 | Cohérence temporelle | reglements | Paiement antérieur à la déclaration du sinistre | MAJEURE | 0 | Signaler |
| T07 | Cohérence temporelle | toutes | Date postérieure à l'extraction du 30/06/2025 | MAJEURE | 0 | Signaler |
| T08 | Cohérence temporelle | reglements | Fichier mensuel contenant un paiement d'un autre mois (livraison tardive ou re-livraison) | MINEURE | 32 | Signaler |
| T09 | Cohérence temporelle | audits | Audit antérieur à la déclaration du sinistre | MAJEURE | 0 | Signaler |
| U01 | Unicité | clients | client_id dupliqué | BLOQUANTE | 0 | Exclure |
| U02 | Unicité | clients | Même client présent plusieurs fois (email_hash identique) | MAJEURE | 200 | Fusionner : garder le plus petit client_id, alias dans core.client_alias |
| U03 | Unicité | contrats | contrat_id dupliqué | BLOQUANTE | 0 | Exclure |
| U04 | Unicité | reglements | Paiement livré plusieurs fois (paiement_id identique) | MAJEURE | 32 | Exclure la re-livraison (quarantaine), garder la première |
| U05 | Unicité | sinistres | sinistre_id dupliqué | BLOQUANTE | 0 | Exclure |
| U06 | Unicité | clients | Paire de doublons dont la date de naissance ou la région diffère (valide la clé email_hash) | MAJEURE | 0 | Signaler |
| V01 | Validité | clients | Date de naissance factice 01/01/1890 | MINEURE | 18 | Corriger : mise à NULL |
| V02 | Validité | clients | Titulaire mineur à la date d'extraction | MINEURE | 22 | Signaler |
| V03 | Validité | contrats | Prime annuelle nulle ou négative | BLOQUANTE | 25 | Exclure (quarantaine) + sinistres rattachés |
| V04 | Validité | reglements | Montant nul, négatif ou illisible | BLOQUANTE | 0 | Exclure (quarantaine) |
| V05 | Validité | contrats | Champs incohérents avec le produit (AUTO avec surface, HABITATION avec puissance/bonus-malus) | MAJEURE | 0 | Signaler |
| V06 | Validité | contrats | Bonus-malus hors de [0,50 ; 3,50] | MINEURE | 0 | Signaler |
| V07 | Validité | reglements | Sinistre dont le cumul payé dépasse 500 000 EUR (valeur extrême) | MAJEURE | 1 | Signaler ; analysé à part (queue de distribution) |
| V08 | Validité | sinistres | Garantie incompatible avec le produit du contrat | MAJEURE | 0 | Signaler |
| V09 | Validité | toutes | Valeur hors référentiel (statut, produit, zone 1-5, formule, canal) | MAJEURE | 0 | Signaler |

## Requêtes

**C01**
```sql
SELECT COUNT(*) FROM prep.clients WHERE date_naissance_raw IS NULL
```
**C02**
```sql
SELECT COUNT(*) FROM prep.contrats WHERE produit IS NULL OR date_effet IS NULL OR prime_annuelle IS NULL
```
**C03**
```sql
SELECT COUNT(*) FROM prep.contrats WHERE (produit='AUTO' AND (bonus_malus IS NULL OR puissance_cv IS NULL)) OR (produit='HABITATION' AND surface_m2 IS NULL)
```
**C04**
```sql
SELECT COUNT(*) FROM prep.sinistres WHERE date_survenance IS NULL OR date_declaration IS NULL OR garantie IS NULL OR statut IS NULL
```
**K01**
```sql
SELECT COUNT(*) FROM prep.reglements r JOIN prep.sinistres s USING (sinistre_id) WHERE r.rang_occ=1 AND s.statut IN ('REJETE','SANS_SUITE')
```
**K02**
```sql
SELECT COUNT(*) FROM prep.sinistres WHERE (statut IN ('CLOTURE','OUVERT') AND reserve_initiale = 0) OR (statut IN ('REJETE','SANS_SUITE') AND reserve_initiale > 0)
```
**K03**
```sql
SELECT COUNT(*) FROM prep.audits a JOIN prep.sinistres s USING (sinistre_id) WHERE s.statut IN ('OUVERT','SANS_SUITE')
```
**K04**
```sql
SELECT COUNT(*) FROM prep.sinistres s WHERE statut='CLOTURE' AND NOT EXISTS (SELECT 1 FROM prep.reglements r WHERE r.sinistre_id=s.sinistre_id)
```
**R01**
```sql
SELECT COUNT(*) FROM prep.contrats WHERE client_id NOT IN (SELECT client_id FROM prep.clients)
```
**R02**
```sql
SELECT COUNT(*) FROM prep.sinistres WHERE contrat_id NOT IN (SELECT contrat_id FROM prep.contrats)
```
**R03**
```sql
SELECT COUNT(*) FROM prep.reglements WHERE rang_occ=1 AND sinistre_id NOT IN (SELECT sinistre_id FROM prep.sinistres)
```
**R04**
```sql
SELECT COUNT(*) FROM prep.audits WHERE sinistre_id NOT IN (SELECT sinistre_id FROM prep.sinistres)
```
**T01**
```sql
SELECT COUNT(*) FROM prep.contrats WHERE date_resiliation < date_effet
```
**T02**
```sql
SELECT COUNT(*) FROM prep.contrats WHERE date_resiliation = date_effet
```
**T03**
```sql
SELECT COUNT(*) FROM prep.sinistres WHERE date_declaration < date_survenance
```
**T04**
```sql
SELECT COUNT(*) FROM prep.sinistres s JOIN prep.contrats c USING (contrat_id) WHERE s.date_survenance < c.date_effet
```
**T05**
```sql
SELECT COUNT(*) FROM prep.sinistres s JOIN prep.contrats c USING (contrat_id) WHERE c.date_resiliation IS NOT NULL AND s.date_survenance >= c.date_resiliation
```
**T06**
```sql
SELECT COUNT(*) FROM prep.reglements r JOIN prep.sinistres s USING (sinistre_id) WHERE r.rang_occ=1 AND r.date_paiement < s.date_declaration
```
**T07**
```sql
SELECT (SELECT COUNT(*) FROM prep.reglements WHERE date_paiement > DATE '2025-06-30') + (SELECT COUNT(*) FROM prep.sinistres WHERE date_declaration > DATE '2025-06-30') + (SELECT COUNT(*) FROM prep.contrats WHERE date_effet > DATE '2025-06-30')
```
**T08**
```sql
SELECT COUNT(*) FROM prep.reglements WHERE mois_fichier <> mois_paiement
```
**T09**
```sql
SELECT COUNT(*) FROM prep.audits a JOIN prep.sinistres s USING (sinistre_id) WHERE a.date_audit < s.date_declaration
```
**U01**
```sql
SELECT COUNT(*) - COUNT(DISTINCT client_id) FROM prep.clients
```
**U02**
```sql
SELECT COUNT(*) FROM prep.clients WHERE rang_email > 1
```
**U03**
```sql
SELECT COUNT(*) - COUNT(DISTINCT contrat_id) FROM prep.contrats
```
**U04**
```sql
SELECT COUNT(*) FROM prep.reglements WHERE rang_occ > 1
```
**U05**
```sql
SELECT COUNT(*) - COUNT(DISTINCT sinistre_id) FROM prep.sinistres
```
**U06**
```sql
SELECT COUNT(*) FROM (SELECT email_hash FROM prep.clients GROUP BY 1 HAVING COUNT(*)>1 AND (COUNT(DISTINCT date_naissance_raw)>1 OR COUNT(DISTINCT region)>1))
```
**V01**
```sql
SELECT COUNT(*) FROM prep.clients WHERE date_naissance_raw = '01/01/1890'
```
**V02**
```sql
SELECT COUNT(*) FROM prep.clients WHERE date_naissance > DATE '2025-06-30' - INTERVAL 18 YEAR
```
**V03**
```sql
SELECT COUNT(*) FROM prep.contrats WHERE prime_annuelle <= 0 OR prime_annuelle IS NULL
```
**V04**
```sql
SELECT COUNT(*) FROM prep.reglements WHERE rang_occ = 1 AND (montant IS NULL OR montant <= 0)
```
**V05**
```sql
SELECT COUNT(*) FROM prep.contrats WHERE (produit='AUTO' AND surface_m2 IS NOT NULL) OR (produit='HABITATION' AND (puissance_cv IS NOT NULL OR bonus_malus IS NOT NULL))
```
**V06**
```sql
SELECT COUNT(*) FROM prep.contrats WHERE bonus_malus < 0.5 OR bonus_malus > 3.5
```
**V07**
```sql
SELECT COUNT(*) FROM (SELECT sinistre_id FROM prep.reglements WHERE rang_occ=1 GROUP BY 1 HAVING SUM(montant) > 500000)
```
**V08**
```sql
SELECT COUNT(*) FROM prep.sinistres s JOIN prep.contrats c USING (contrat_id) WHERE (c.produit='AUTO' AND s.garantie IN ('DEGAT_EAUX','INCENDIE','TEMPETE')) OR (c.produit='HABITATION' AND s.garantie IN ('COLLISION','RC','BRIS_GLACE'))
```
**V09**
```sql
SELECT (SELECT COUNT(*) FROM prep.sinistres WHERE statut NOT IN ('CLOTURE','OUVERT','REJETE','SANS_SUITE')) + (SELECT COUNT(*) FROM prep.contrats WHERE produit NOT IN ('AUTO','HABITATION') OR zone_risque NOT BETWEEN 1 AND 5 OR formule NOT IN ('ESSENTIELLE','CONFORT','PREMIUM') OR canal_distribution NOT IN ('WEB','AGENT','COURTIER'))
```

## Contenu de la quarantaine

| Règle | Entité | Lignes |
|---|---|---:|
| P01 | sinistre | 5 |
| P02 | reglement | 1 |
| T01 | contrat | 20 |
| U02 | client | 200 |
| U04 | reglement | 32 |
| V03 | contrat | 25 |

## Tests bloquants (dernier run réussi)

| Test | Description | Résultat |
|---|---|---|
| M01_mart_prime_mois | Mart portefeuille_mois : prime acquise et exposition = fact_exposition (écart < 1 EUR) | OK |
| M02_mart_paye_mois | Mart portefeuille_mois : sinistres payés = fact_sinistre | OK |
| M03_mart_technique | Mart technique_segment : primes, payé, exposition et résiliations = cœur | OK |
| M04_contributions_somme | Contributions des segments : somme = variation du ratio global (chaque année et périmètre) | OK |
| M05_pareto_ferme | Courbe de Pareto : le dernier point cumule 100 % de la valeur | OK |
| M06_retention_bornee | Rétention : 0 <= retenus <= éligibles | OK |
| M07_valeur_client | Valeur client : somme = primes acquises - sinistres payés du cœur | OK |
| T01_pk_contrat | Unicité de la clé dim_contrat.contrat_id | OK |
| T02_pk_client | Unicité de la clé dim_client.client_id | OK |
| T03_pk_sinistre | Unicité de fact_sinistre.sinistre_id | OK |
| T04_pk_reglement | Unicité de fact_reglement.paiement_id | OK |
| T05_pk_exposition | Unicité du grain fact_exposition (contrat, année) | OK |
| T06_fk_contrat_client | Intégrité : tout contrat pointe un client du cœur | OK |
| T07_fk_sinistre_contrat | Intégrité : tout sinistre pointe un contrat du cœur | OK |
| T08_fk_reglement_sinistre | Intégrité : tout règlement pointe un sinistre du cœur | OK |
| T09_fk_dates | Intégrité : toutes les clés de date existent dans dim_date | OK |
| T10_exposition_positive | Exposition strictement positive et <= 1 année-police par ligne | OK |
| T11_recon_reglements_lignes | Réconciliation règlements : lignes brutes = cœur + quarantaine | OK |
| T12_recon_reglements_montants | Réconciliation règlements : montant brut = montant cœur + montant en quarantaine (écart < 1 centime) | OK |
| T13_recon_contrats | Réconciliation contrats : brut = cœur + quarantaine (clés distinctes) | OK |
| T14_recon_clients | Réconciliation clients : brut = clients du cœur + alias fusionnés | OK |
| T15_recon_sinistres | Réconciliation sinistres : brut = cœur + quarantaine | OK |
| T16_alias_survivants | Tout alias client pointe un survivant présent dans dim_client | OK |
| T17_dedup_email | Aucun email_hash en double dans dim_client | OK |
| T18_quarantaine_motif | Toute ligne en quarantaine porte une règle et un motif | OK |
| T19_journal_vs_brut | Journal d'ingestion = contenu du brut (par fichier, dernier chargement) | OK |
| T20_prime_acquise_bornee | Prime acquise <= prime annuelle du contrat | OK |