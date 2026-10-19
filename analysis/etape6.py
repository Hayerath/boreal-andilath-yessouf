"""Étape 6 (L4) : valeur observée des clients = primes acquises - sinistres payés (jusqu'au 30/06/2025).
Lit uniquement l'entrepôt. Ce n'est PAS une valeur future : aucune projection."""
import duckdb, numpy as np, pandas as pd

pd.set_option("display.width", 200)
con = duckdb.connect("data/boreal.duckdb", read_only=True)

v = con.sql("""
WITH p AS (SELECT client_id, SUM(prime_acquise) AS prime, SUM(exposition_annee_police) AS expo FROM core.fact_exposition GROUP BY 1),
s AS (SELECT client_id, SUM(montant_regle)::DOUBLE AS paye, COUNT(*) FILTER (WHERE statut IN ('CLOTURE','OUVERT')) AS n_sin FROM core.fact_sinistre GROUP BY 1),
k AS (SELECT client_id, COUNT(*) AS nb_contrats, COUNT(DISTINCT produit) AS nb_produits,
             MIN(date_effet) AS premiere_souscription FROM core.dim_contrat GROUP BY 1)
SELECT c.client_id, c.region, c.csp, k.nb_contrats, k.nb_produits, YEAR(k.premiere_souscription) AS cohorte,
       COALESCE(p.prime, 0) AS prime, COALESCE(p.expo, 0) AS expo, COALESCE(s.paye, 0) AS paye, COALESCE(s.n_sin, 0) AS n_sin
FROM core.dim_client c JOIN k USING (client_id) LEFT JOIN p USING (client_id) LEFT JOIN s USING (client_id)""").df()
v["valeur"] = v.prime - v.paye
print(f"Clients avec contrat : {len(v)} | primes acquises {v.prime.sum():,.0f} | payé {v.paye.sum():,.0f} | valeur nette {v.valeur.sum():,.0f}")
print(f"Clients sans sinistre payé : {(v.paye == 0).mean():.1%} | clients à valeur négative : {(v.valeur < 0).sum()} ({(v.valeur < 0).mean():.1%})\n")


def pareto(d, col, titre):
    total = d[col].sum()
    """Part du résultat positif/négatif cumulée par les x % de clients les plus (resp. moins) rentables."""
    x = np.sort(d[col].values)[::-1]
    pos, neg = x[x > 0].sum(), x[x < 0].sum()
    print(titre)
    for q in (0.01, 0.05, 0.10, 0.20):
        top = x[: int(len(x) * q)].sum()
        bot = x[::-1][: int(len(x) * q)].sum()
        print(f"  les {q:.0%} de clients les plus rentables : {top:>12,.0f} EUR = {top / total:6.1%} de la valeur nette ; "
              f"les {q:.0%} les moins rentables : {bot:>12,.0f} EUR")
    print(f"  valeur positive totale {pos:,.0f} | valeur négative totale {neg:,.0f}\n")


pareto(v, "valeur", "=== A. Concentration (tous clients, 1129 inclus) ===")
v2 = v[v.paye < 2_000_000]   # exclut le client du sinistre 1129
pareto(v2, "valeur", "=== A bis. Même calcul sans le client du sinistre 1129 ===")
x = np.sort(v.valeur.values)[::-1]; cum = np.cumsum(x)
print("Courbe de Pareto (part cumulée de la valeur nette) :")
for q in (0.1, 0.25, 0.5, 0.75, 1.0):
    print(f"  {q:.0%} des clients (du plus au moins rentable) -> {cum[int(len(x) * q) - 1] / v.valeur.sum():6.1%}")
print()

# Profils : déciles de valeur
v2 = v2.copy()
v2["decile"] = pd.qcut(v2.valeur.rank(method="first", ascending=False), 10, labels=range(1, 11))
v2["valeur_par_an"] = v2.valeur / v2.expo.where(v2.expo > 0)
prof = v2.groupby("decile", observed=True).agg(clients=("client_id", "count"), expo_moy=("expo", "mean"), valeur_par_an_moy=("valeur_par_an", "mean"), valeur_moy=("valeur", "mean"), prime_moy=("prime", "mean"),
        paye_moy=("paye", "mean"), sinistres_moy=("n_sin", "mean"), contrats_moy=("nb_contrats", "mean"), part_multi=("nb_produits", lambda s: (s == 2).mean()))
print("=== B. Profils par décile de valeur (1 = plus rentable) ===")
print(prof.round(2).to_string(), "\n")

print("=== C. Profil des clients à valeur négative vs positive (sans 1129) ===")
v2["groupe"] = np.where(v2.valeur < 0, "valeur négative", "valeur positive")
print(v2.groupby("groupe").agg(clients=("client_id", "count"), prime_moy=("prime", "mean"), paye_moy=("paye", "mean"),
      sin_moy=("n_sin", "mean"), expo_moy=("expo", "mean"), part_multi=("nb_produits", lambda s: (s == 2).mean())).round(2).to_string(), "\n")
for col in ("region", "csp"):
    t = v2.groupby(col).agg(clients=("client_id", "count"), valeur_moy=("valeur", "mean"), part_negatifs=("valeur", lambda s: (s < 0).mean()))
    print(f"--- par {col} ---"); print(t.round(2).sort_values("valeur_moy").to_string(), "\n")
print("--- par détention ---")
print(v2.groupby("nb_produits").agg(clients=("client_id", "count"), valeur_par_an_moy=("valeur_par_an", "mean"), valeur_moy=("valeur", "mean"), prime_moy=("prime", "mean"), paye_moy=("paye", "mean")).round(1).to_string())
print("\n--- par cohorte ---")
print(v2.groupby("cohorte").agg(clients=("client_id", "count"), valeur_moy=("valeur", "mean"), expo_moy=("expo", "mean")).round(2).to_string())
