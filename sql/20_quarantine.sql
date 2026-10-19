-- QUARANTAINE : chaque ligne écartée du cœur reste retrouvable avec sa règle et son motif.
-- Ordre : contrats -> sinistres (parent) -> règlements -> audits (cascade volontaire).
CREATE OR REPLACE TABLE quarantine.rows (
  rule_id VARCHAR, entity VARCHAR, record_key VARCHAR, source_file VARCHAR, motif VARCHAR, payload VARCHAR);

-- Clients : doublons (non-survivants), fusionnés via core.client_alias
INSERT INTO quarantine.rows
SELECT 'U02','client', client_id::VARCHAR, _source_file,
       'Doublon de client (même email_hash) ; survivant = ' || client_id_survivant, TO_JSON(c)::VARCHAR
FROM prep.clients c WHERE rang_email > 1;

-- Contrats
INSERT INTO quarantine.rows
SELECT 'V03','contrat', contrat_id::VARCHAR, _source_file, 'Prime annuelle <= 0 (' || prime_annuelle || ')', TO_JSON(c)::VARCHAR
FROM prep.contrats c WHERE prime_annuelle <= 0 OR prime_annuelle IS NULL;

INSERT INTO quarantine.rows
SELECT 'T01','contrat', contrat_id::VARCHAR, _source_file, 'Date de résiliation antérieure à la date d''effet', TO_JSON(c)::VARCHAR
FROM prep.contrats c WHERE date_resiliation < date_effet;

INSERT INTO quarantine.rows
SELECT 'R01','contrat', contrat_id::VARCHAR, _source_file, 'Client référencé absent du CRM', TO_JSON(c)::VARCHAR
FROM prep.contrats c WHERE client_id NOT IN (SELECT client_id FROM prep.clients);

CREATE OR REPLACE VIEW prep.contrats_ok AS
SELECT * FROM prep.contrats c
WHERE NOT EXISTS (SELECT 1 FROM quarantine.rows q WHERE q.entity='contrat' AND q.record_key = c.contrat_id::VARCHAR);

-- Sinistres : contrat parent absent ou en quarantaine
INSERT INTO quarantine.rows
SELECT 'P01','sinistre', sinistre_id::VARCHAR, _source_file,
       'Contrat parent ' || contrat_id || ' absent ou en quarantaine', TO_JSON(s)::VARCHAR
FROM prep.sinistres s WHERE contrat_id NOT IN (SELECT contrat_id FROM prep.contrats_ok);

CREATE OR REPLACE VIEW prep.sinistres_ok AS
SELECT * FROM prep.sinistres s
WHERE NOT EXISTS (SELECT 1 FROM quarantine.rows q WHERE q.entity='sinistre' AND q.record_key = s.sinistre_id::VARCHAR);

-- Règlements : re-livraisons, montants invalides, sinistre parent absent ou en quarantaine
INSERT INTO quarantine.rows
SELECT 'U04','reglement', paiement_id::VARCHAR, _source_file,
       'Doublon exact : paiement déjà livré dans ' || (SELECT MIN(_source_file) FROM prep.reglements x WHERE x.paiement_id = r.paiement_id),
       TO_JSON(r)::VARCHAR
FROM prep.reglements r WHERE rang_occ > 1;

INSERT INTO quarantine.rows
SELECT 'V04','reglement', paiement_id::VARCHAR, _source_file, 'Montant nul, négatif ou illisible', TO_JSON(r)::VARCHAR
FROM prep.reglements r WHERE rang_occ = 1 AND (montant IS NULL OR montant <= 0);

INSERT INTO quarantine.rows
SELECT 'P02','reglement', paiement_id::VARCHAR, _source_file,
       'Sinistre parent ' || sinistre_id || ' absent ou en quarantaine', TO_JSON(r)::VARCHAR
FROM prep.reglements r
WHERE rang_occ = 1 AND montant > 0 AND sinistre_id NOT IN (SELECT sinistre_id FROM prep.sinistres_ok);

CREATE OR REPLACE VIEW prep.reglements_ok AS
SELECT * FROM prep.reglements r
WHERE NOT EXISTS (SELECT 1 FROM quarantine.rows q WHERE q.entity='reglement'
                  AND q.record_key = r.paiement_id::VARCHAR AND q.source_file = r._source_file);

-- Audits
INSERT INTO quarantine.rows
SELECT 'P03','audit', sinistre_id::VARCHAR, _source_file,
       'Sinistre audité absent ou en quarantaine', TO_JSON(a)::VARCHAR
FROM prep.audits a WHERE sinistre_id NOT IN (SELECT sinistre_id FROM prep.sinistres_ok);

CREATE OR REPLACE VIEW prep.audits_ok AS
SELECT * FROM prep.audits a
WHERE NOT EXISTS (SELECT 1 FROM quarantine.rows q WHERE q.entity='audit' AND q.record_key = a.sinistre_id::VARCHAR);
