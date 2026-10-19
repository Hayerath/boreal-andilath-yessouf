"""Étape 4 : incertitude (IC 95 %), deux tests, queue de distribution des coûts. Lit uniquement l'entrepôt."""
import duckdb, numpy as np, pandas as pd
from scipy import stats

pd.set_option("display.width", 200)
con = duckdb.connect("data/boreal.duckdb", read_only=True)
rng = np.random.default_rng(42)          # graine fixe : résultats reproductibles


def poisson_ci(n, expo, alpha=0.05):
    """IC exact (Garwood) d'un taux = n événements / expo années-police."""
    lo = stats.chi2.ppf(alpha / 2, 2 * n) / 2 / expo if n > 0 else 0.0
    hi = stats.chi2.ppf(1 - alpha / 2, 2 * n + 2) / 2 / expo
    return lo, hi


expo = con.sql("""SELECT c.produit, SUM(f.exposition_annee_police) AS expo
                  FROM core.fact_exposition f JOIN core.dim_contrat c USING (contrat_id) GROUP BY 1""").df().set_index("produit")["expo"]
sin = con.sql("""SELECT c.produit, s.sinistre_id, s.statut, s.montant_regle::DOUBLE AS paye
                 FROM core.fact_sinistre s JOIN core.dim_contrat c USING (contrat_id)""").df()
avec = sin[sin.statut.isin(["CLOTURE", "OUVERT"])]
resil = con.sql("SELECT produit, COUNT(*) FILTER (WHERE est_resilie) AS n FROM core.dim_contrat GROUP BY 1").df().set_index("produit")["n"]
ctr = con.sql("""SELECT c.contrat_id, c.produit, COALESCE(e.prime, 0) AS prime, COALESCE(s.paye, 0) AS paye
                 FROM core.dim_contrat c
                 LEFT JOIN (SELECT contrat_id, SUM(prime_acquise) AS prime FROM core.fact_exposition GROUP BY 1) e USING (contrat_id)
                 LEFT JOIN (SELECT contrat_id, SUM(montant_regle)::DOUBLE AS paye FROM core.fact_sinistre GROUP BY 1) s USING (contrat_id)""").df()

rows = []
for p in ["AUTO", "HABITATION"]:
    n, E = len(avec[avec.produit == p]), expo[p]
    lo, hi = poisson_ci(n, E)
    rows.append((p, "Fréquence (sinistres avec suite / année-police)", n / E, lo, hi, "Poisson exact"))
    x = avec[avec.produit == p].paye.values
    boot = [rng.choice(x, len(x)).mean() for _ in range(3000)]
    rows.append((p, "Coût moyen (EUR, 1129 inclus)", x.mean(), *np.percentile(boot, [2.5, 97.5]), "bootstrap 3000"))
    x2 = avec[(avec.produit == p) & (avec.sinistre_id != 1129)].paye.values
    boot = [rng.choice(x2, len(x2)).mean() for _ in range(3000)]
    rows.append((p, "Coût moyen (EUR, hors 1129)", x2.mean(), *np.percentile(boot, [2.5, 97.5]), "bootstrap 3000"))
    c = ctr[ctr.produit == p]
    pr, pa = c.prime.values, c.paye.values
    idx = rng.integers(0, len(c), (2000, len(c)))
    ratios = pa[idx].sum(1) / pr[idx].sum(1)
    rows.append((p, "Ratio sinistres / primes", pa.sum() / pr.sum(), *np.percentile(ratios, [2.5, 97.5]), "bootstrap sur contrats"))
    lo, hi = poisson_ci(int(resil[p]), expo[p])
    rows.append((p, "Résiliations par année-police", resil[p] / expo[p], lo, hi, "Poisson exact"))
ic = pd.DataFrame(rows, columns=["produit", "indicateur", "valeur", "ic95_bas", "ic95_haut", "méthode"])
print("=== 1. INTERVALLES DE CONFIANCE À 95 % ===")
print(ic.round(4).to_string(index=False))


def test_taux(n1, e1, n2, e2):
    """Deux taux de Poisson égaux ? Sous H0, n1 ~ Binomiale(n1+n2, e1/(e1+e2)) (test exact conditionnel)."""
    return stats.binomtest(n1, n1 + n2, e1 / (e1 + e2)).pvalue


fz = con.sql("""SELECT c.produit, c.zone_risque, c.canal_distribution, SUM(f.exposition_annee_police) AS expo
                FROM core.fact_exposition f JOIN core.dim_contrat c USING (contrat_id) GROUP BY ALL""").df()
sz = con.sql("""SELECT c.produit, c.zone_risque, c.canal_distribution, s.statut, s.sinistre_id, s.montant_regle::DOUBLE AS paye
                FROM core.fact_sinistre s JOIN core.dim_contrat c USING (contrat_id)""").df()
sz = sz[sz.statut.isin(["CLOTURE", "OUVERT"])]
print("\n=== 2. TESTS ===")
h = "HABITATION"
e5, e1 = fz[(fz.produit == h) & (fz.zone_risque == 5)].expo.sum(), fz[(fz.produit == h) & (fz.zone_risque == 1)].expo.sum()
n5, n1 = len(sz[(sz.produit == h) & (sz.zone_risque == 5)]), len(sz[(sz.produit == h) & (sz.zone_risque == 1)])
print(f"Test 1 - Fréquence habitation zone 5 vs zone 1 : {n5/e5:.4f} vs {n1/e1:.4f}  rapport {n5/e5/(n1/e1):.2f}  p = {test_taux(n5, e5, n1, e1):.2g}")
a = sz[(sz.produit == "AUTO") & (sz.canal_distribution == "AGENT")]
w = sz[(sz.produit == "AUTO") & (sz.canal_distribution == "WEB")]
print(f"Test 2 - Coût auto AGENT vs WEB : moyennes {a.paye.mean():.0f} vs {w.paye.mean():.0f}, médianes {a.paye.median():.0f} vs {w.paye.median():.0f}")
print(f"         Mann-Whitney p = {stats.mannwhitneyu(a.paye, w.paye).pvalue:.3g}   |  t de Welch (trompé par le sinistre 1129) p = {stats.ttest_ind(a.paye, w.paye, equal_var=False).pvalue:.3g}")
a2 = a[a.sinistre_id != 1129]
print(f"         hors 1129 : Mann-Whitney p = {stats.mannwhitneyu(a2.paye, w.paye).pvalue:.3g}")
rs = con.sql("""SELECT c.canal_distribution AS canal, COUNT(*) FILTER (WHERE c.est_resilie) AS n,
                (SELECT SUM(f.exposition_annee_police) FROM core.fact_exposition f JOIN core.dim_contrat d USING (contrat_id)
                 WHERE d.canal_distribution = c.canal_distribution) AS expo
                FROM core.dim_contrat c GROUP BY 1""").df().set_index("canal")
print(f"Bonus  - Résiliations WEB vs AGENT : {rs.n['WEB']/rs.expo['WEB']:.4f} vs {rs.n['AGENT']/rs.expo['AGENT']:.4f}  p = {test_taux(int(rs.n['WEB']), rs.expo['WEB'], int(rs.n['AGENT']), rs.expo['AGENT']):.2g}")

print("\n=== 3. QUEUE DE DISTRIBUTION DES COÛTS ===")
def queue(x):
    x = np.sort(x)[::-1]; tot = x.sum()
    d = {"n": len(x), "médiane": np.median(x), "moyenne": x.mean(), "q75": np.percentile(x, 75), "q90": np.percentile(x, 90),
         "q95": np.percentile(x, 95), "q99": np.percentile(x, 99), "max": x[0]}
    for k in (0.01, 0.05, 0.10):
        d[f"part du total payé par les {int(k*100)} % les plus chers"] = x[: max(1, int(len(x) * k))].sum() / tot
    return d
q = pd.DataFrame({"tous (1129 inclus)": queue(avec.paye.values),
                  "hors 1129": queue(avec[avec.sinistre_id != 1129].paye.values)})
print(q.round(3).to_string())
