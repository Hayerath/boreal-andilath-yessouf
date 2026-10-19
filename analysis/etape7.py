"""Étape 7 (L4) : délais de gestion par garantie et audits antifraude. Lit uniquement l'entrepôt.
Date de clôture : absente de la source -> approximée par la date du DERNIER règlement (sinistres CLOTURE uniquement)."""
import duckdb, numpy as np, pandas as pd

pd.set_option("display.width", 220)
con = duckdb.connect("data/boreal.duckdb", read_only=True)

s = con.sql("""SELECT f.sinistre_id, c.produit, g.garantie_code AS garantie, f.statut, f.annee_survenance,
  f.delai_declaration_j, (f.date_premier_reglement - f.date_declaration) AS delai_premier_reglt_j,
  (f.date_dernier_reglement - f.date_declaration) AS delai_cloture_approx_j,
  f.nb_reglements, f.montant_regle::DOUBLE AS paye, f.reserve_initiale::DOUBLE AS reserve
  FROM core.fact_sinistre f JOIN core.dim_contrat c USING (contrat_id) JOIN core.dim_garantie g USING (garantie_sk)""").df()


def quant(d, col):
    x = d[col].dropna()
    return pd.Series({"n": len(x), "médiane": x.median(), "q75": x.quantile(.75), "q90": x.quantile(.90), "q95": x.quantile(.95), "max": x.max()})


print("=== A. Délai de déclaration (survenance -> déclaration), en jours, par garantie ===")
print("Population : sinistres dont la déclaration n'est pas antérieure à la survenance")
print(s.groupby(["produit", "garantie"]).apply(lambda d: quant(d, "delai_declaration_j"), include_groups=False).round(1).to_string(), "\n")
print("=== B. Délai de premier règlement (déclaration -> 1er paiement), jours ===")
print("Population : sinistres avec au moins un règlement")
print(s.groupby(["produit", "garantie"]).apply(lambda d: quant(d, "delai_premier_reglt_j"), include_groups=False).round(1).to_string(), "\n")
cl = s[(s.statut == "CLOTURE") & (s.nb_reglements > 0)]
print("=== C. Délai de clôture approximé (déclaration -> dernier règlement), jours ===")
print(f"Population : {len(cl)} sinistres CLOTURE avec règlement (les OUVERT sont exclus : délai non terminé)")
print(cl.groupby(["produit", "garantie"]).apply(lambda d: quant(d, "delai_cloture_approx_j"), include_groups=False).round(1).to_string(), "\n")
print("Sinistres OUVERT : nombre, avec/sans règlement, par année de survenance")
o = s[s.statut == "OUVERT"]
print(o.groupby("annee_survenance").agg(ouverts=("sinistre_id", "count"), sans_reglement=("nb_reglements", lambda x: (x == 0).sum())).to_string(), "\n")

# ---------- Audits ----------
a = con.sql("""SELECT a.sinistre_id, a.fraude_confirmee, a.date_audit FROM core.fact_audit a""").df().merge(s, on="sinistre_id")
print("=== D. Audits antifraude : à qui s'appliquent les chiffres ===")
print(f"Sinistres déclarés : {len(s)} | audités : {len(a)} ({len(a) / len(s):.1%}) | fraudes confirmées : {int(a.fraude_confirmee.sum())}")
print(f"Taux de confirmation GLOBAL (population AUDITÉE uniquement) : {a.fraude_confirmee.mean():.1%}")
print("Statut des sinistres audités :", a.statut.value_counts().to_dict(), "\n")
a["tranche_reserve"] = pd.cut(a.reserve, [-1, 1000, 5000, 20000, 1e9], labels=["<1k", "1-5k", "5-20k", ">20k"])
s["tranche_reserve"] = pd.cut(s.reserve, [-1, 1000, 5000, 20000, 1e9], labels=["<1k", "1-5k", "5-20k", ">20k"])
for crit in ["produit", "garantie", "statut", "tranche_reserve", "annee_survenance"]:
    t = a.groupby(crit, observed=True).agg(audites=("sinistre_id", "count"), fraudes=("fraude_confirmee", "sum"), taux_confirmation=("fraude_confirmee", "mean"))
    t["couverture_audit"] = t.audites / s.groupby(crit, observed=True).size().reindex(t.index)
    print(f"--- par {crit} ---"); print(t.round(3).to_string(), "\n")

print("=== E. Intérêt descriptif des audits au regard des montants (hors sinistre 1129, audité et non frauduleux : 2,48 M EUR) ===")
a = a[a.sinistre_id != 1129]
f = a[a.fraude_confirmee == 1]
nf = a[a.fraude_confirmee == 0]
non_aud = s[(~s.sinistre_id.isin(a.sinistre_id)) & (s.sinistre_id != 1129) & s.statut.isin(["CLOTURE", "OUVERT"])]
print(f"Audités : {len(a)} dossiers, payé {a.paye.sum():,.0f} EUR, réserve initiale {a.reserve.sum():,.0f} EUR")
print(f"Fraudes confirmées : {len(f)} dossiers, payé {f.paye.sum():,.0f} EUR (médiane {f.paye.median():,.0f}), réserve initiale {f.reserve.sum():,.0f} EUR")
print(f"Part du payé des audités portée par les fraudes confirmées : {f.paye.sum() / a.paye.sum():.1%}")
print(f"Médiane du payé : audités fraude {f.paye.median():,.0f} | audités non fraude {nf.paye.median():,.0f} | non audités avec suite {non_aud.paye.median():,.0f} EUR")
print("Lecture : les audits visent des dossiers beaucoup plus chers que la moyenne (ciblage), mais la fraude confirmée pèse peu en montant.")
print("Limite : les audits ne sont pas tirés au hasard ; on ne sait pas combien de fraudes se trouvent parmi les non audités.")
