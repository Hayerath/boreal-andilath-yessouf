"""Génère docs/regles_qualite.md à partir de dq.rule_results (les volumes viennent de l'entrepôt)."""
import duckdb
from .config import DEFAULT_DB, ROOT

con = duckdb.connect(str(DEFAULT_DB), read_only=True)
rows = con.execute("""SELECT rule_id, dimension, entity, description, severity, treatment, volume, query
                      FROM dq.rule_results ORDER BY rule_id""").fetchall()
q = con.execute("SELECT rule_id, entity, COUNT(*) FROM quarantine.rows GROUP BY ALL ORDER BY 1").fetchall()
t = con.execute("SELECT test_id, description, status FROM ops.test_results WHERE run_id=(SELECT run_id FROM ops.pipeline_runs WHERE status='SUCCES' ORDER BY started_at DESC LIMIT 1) ORDER BY 1").fetchall()
out = ["# Règles de qualité et tests (généré depuis l'entrepôt)\n",
       f"{len(rows)} règles mesurées, dont {sum(r[6] > 0 for r in rows)} avec au moins une anomalie.\n",
       "| Règle | Dimension | Table | Contrôle | Gravité | Volume | Traitement |", "|---|---|---|---|---|---:|---|"]
out += [f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[6]} | {r[5]} |" for r in rows]
out += ["\n## Requêtes\n"] + [f"**{r[0]}**\n```sql\n{r[7]}\n```" for r in rows]
out += ["\n## Contenu de la quarantaine\n", "| Règle | Entité | Lignes |", "|---|---|---:|"] + [f"| {a} | {b} | {c} |" for a, b, c in q]
out += ["\n## Tests bloquants (dernier run réussi)\n", "| Test | Description | Résultat |", "|---|---|---|"] + [f"| {a} | {b} | {c} |" for a, b, c in t]
(ROOT / "docs" / "regles_qualite.md").write_text("\n".join(out), encoding="utf-8")
print("docs/regles_qualite.md généré")
