SELECT rule_id, entity, COUNT(*) AS lignes FROM quarantine.rows GROUP BY ALL ORDER BY rule_id;

SELECT rule_id, record_key, motif FROM quarantine.rows WHERE rule_id IN ('V03', 'T01') ORDER BY rule_id, record_key LIMIT 8;