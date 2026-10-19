"""Étape 5 (L4) : rétention par cohorte et multi-détention. Lit uniquement l'entrepôt."""
import duckdb, pandas as pd
from scipy import stats

pd.set_option("display.width", 200)
con = duckdb.connect("data/boreal.duckdb", read_only=True)
FIN = "2025-06-30"   # dernière date observée

# ---------- A. Matrice de rétention par cohorte annuelle de souscription et par produit ----------
# Un contrat n'entre dans la cellule (cohorte, k) que si son k-ième anniversaire est observable (<= 30/06/2025).
a = con.sql(f"""
WITH k AS (SELECT UNNEST(RANGE(1, 6)) AS k),
x AS (SELECT c.produit, YEAR(c.date_effet) AS cohorte, k.k, (c.date_effet + INTERVAL (k.k * 12) MONTH)::DATE AS anniv,
             c.date_resiliation
      FROM core.dim_contrat c CROSS JOIN k)
SELECT produit, cohorte, k, COUNT(*) AS eligibles,
       COUNT(*) FILTER (WHERE date_resiliation IS NULL OR date_resiliation > anniv) AS retenus
FROM x WHERE anniv <= DATE '{FIN}' GROUP BY ALL""").df()
a["retention"] = a.retenus / a.eligibles
for p in ["AUTO", "HABITATION"]:
    d = a[a.produit == p]
    print(f"=== A. Rétention {p} : part des contrats encore en vigueur au k-ième anniversaire ===")
    print((d.pivot(index="cohorte", columns="k", values="retention") * 100).round(1).rename(columns=lambda k: f"an {k} (%)").to_string())
    print("contrats observables dans chaque cellule :")
    print(d.pivot(index="cohorte", columns="k", values="eligibles").fillna(0).astype(int).rename(columns=lambda k: f"an {k}").to_string(), "\n")

# ---------- B. Multi-détention ----------
b = con.sql("""SELECT COUNT(*) AS clients_avec_contrat, COUNT(*) FILTER (WHERE np = 2) AS multi_detenteurs
               FROM (SELECT client_id, COUNT(DISTINCT produit) AS np FROM core.dim_contrat GROUP BY 1)""").df().iloc[0]
print("=== B. Multi-détention ===")
print(f"Clients avec au moins un contrat : {b.clients_avec_contrat} ; détenant auto ET habitation : {b.multi_detenteurs} "
      f"({b.multi_detenteurs / b.clients_avec_contrat:.1%})")
ecart = con.sql("""WITH a AS (SELECT client_id, MIN(date_effet) FILTER (WHERE produit='AUTO') da,
                                   MIN(date_effet) FILTER (WHERE produit='HABITATION') dh FROM core.dim_contrat GROUP BY 1)
                   SELECT MEDIAN(ABS(da - dh)) FROM a WHERE da IS NOT NULL AND dh IS NOT NULL""").fetchone()[0]
print(f"Écart médian entre les deux souscriptions : {ecart:.0f} jours (le 2e produit arrive tard : biais de survie)\n")

# Comparaison de rétention : on suit le PREMIER contrat de chaque client jusqu'à son 2e anniversaire.
base = f"""
WITH f AS (SELECT client_id, contrat_id, produit, date_effet AS fe, date_resiliation AS fr,
                  (date_effet + INTERVAL 12 MONTH)::DATE AS l1, (date_effet + INTERVAL 24 MONTH)::DATE AS l2
           FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY client_id ORDER BY date_effet, contrat_id) AS rn
                 FROM core.dim_contrat) WHERE rn = 1 AND (date_effet + INTERVAL 24 MONTH)::DATE <= DATE '{FIN}'),
m AS (SELECT f.client_id, f.fr, f.l1, f.l2,
             MAX(CASE WHEN c.contrat_id IS NOT NULL THEN 1 ELSE 0 END) AS multi_ever,
             MAX(CASE WHEN c.date_effet <= f.l1 AND (c.date_resiliation IS NULL OR c.date_resiliation > f.l1) THEN 1 ELSE 0 END) AS multi_a_12m
      FROM f LEFT JOIN core.dim_contrat c ON c.client_id = f.client_id AND c.produit <> f.produit
      GROUP BY ALL)
"""
naif = con.sql(base + """SELECT multi_ever AS multi, COUNT(*) AS n,
                 COUNT(*) FILTER (WHERE fr IS NULL OR fr > l2) AS retenus FROM m GROUP BY 1 ORDER BY 1""").df()
land = con.sql(base + """SELECT multi_a_12m AS multi, COUNT(*) AS n,
                 COUNT(*) FILTER (WHERE fr IS NULL OR fr > l2) AS retenus
                 FROM m WHERE fr IS NULL OR fr > l1 GROUP BY 1 ORDER BY 1""").df()


def show(titre, d):
    print(titre)
    for _, r in d.iterrows():
        ci = stats.binomtest(int(r.retenus), int(r.n)).proportion_ci(method="wilson")
        print(f"  {'multi-détenteurs' if r.multi else 'mono-détenteurs  '} : n={int(r.n):5d}  rétention {r.retenus / r.n:.1%}  IC95 [{ci.low:.1%} ; {ci.high:.1%}]")
    t = [[int(r.retenus), int(r.n - r.retenus)] for _, r in d.sort_values("multi").iterrows()]
    print(f"  test du khi-deux (écart entre les groupes) : p = {stats.chi2_contingency(t)[1]:.2g}\n")


show("B1. Comparaison NAÏVE : multi-détenteur = détient les deux produits à la date d'extraction (rétention du 1er contrat à 24 mois)", naif)
show("B2. Comparaison PRUDENTE (repère à 12 mois) : parmi les clients dont le 1er contrat est actif à 12 mois, "
     "multi = détient déjà l'autre produit à ce moment ; résultat = 1er contrat actif à 24 mois", land)
