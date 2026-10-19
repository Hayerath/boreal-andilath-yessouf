"""Dashboard Boréal Assurances : 3 pages + définitions. Lit UNIQUEMENT le schéma marts de l'entrepôt.
Lancement : streamlit run app/dashboard.py   (variable BOREAL_DB pour changer le fichier DuckDB)."""
import os
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DB = os.environ.get("BOREAL_DB", str(Path(__file__).resolve().parent.parent / "data" / "boreal.duckdb"))
BLUE, AQUA, ORANGE, GRAY = "#2a78d6", "#1baf7a", "#eb6834", "#8a8a85"
SEUIL_DEFAUT = 0.65

st.set_page_config(page_title="Boréal Assurances · Pilotage technique", layout="wide")


# ------------------------------------------------------------------ accès aux données (marts uniquement)
@st.cache_data(ttl=300, show_spinner=False)
def mart(name: str) -> pd.DataFrame:
    con = duckdb.connect(DB, read_only=True)
    try:
        return con.execute(f"SELECT * FROM marts.{name}").df()
    finally:
        con.close()


def eur(x):
    return "n.d." if x is None or pd.isna(x) else f"{x:,.0f} €".replace(",", " ")


def num(x):
    return "n.d." if x is None or pd.isna(x) else f"{x:,.0f}".replace(",", " ")


def pct(x, d=1):
    return "n.d." if x is None or pd.isna(x) else f"{100 * x:.{d}f} %".replace(".", ",")


def r2(x):
    return "n.d." if x is None or pd.isna(x) else f"{x:.2f}".replace(".", ",")


def style(fig, h=380, **kw):
    fig.update_layout(height=h, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", legend=dict(orientation="h", y=1.12, x=0), hovermode="closest", **kw)
    fig.update_xaxes(showgrid=False, linecolor=GRAY)
    fig.update_yaxes(gridcolor="rgba(138,138,133,0.25)", zeroline=False)
    return fig


def table_view(df, label="Voir les données du graphique"):
    with st.expander(label):
        st.dataframe(df, width="stretch", hide_index=True)


# ------------------------------------------------------------------ barre latérale : page et filtres croisés
pm = mart("portefeuille_mois")
mois_opts = sorted(pm.mois.astype(str).str[:7].unique())
st.sidebar.title("Boréal Assurances")
page = st.sidebar.radio("Page", ["Portefeuille", "Technique et clients", "Exploitation", "Définitions"])
st.sidebar.markdown("### Filtres")
periode = st.sidebar.select_slider("Période (mois)", options=mois_opts, value=("2024-07", "2025-06"))
produits = st.sidebar.multiselect("Produit", ["AUTO", "HABITATION"], default=["AUTO", "HABITATION"])
regions = st.sidebar.multiselect("Région", sorted(pm.region.unique()), default=[])
canaux = st.sidebar.multiselect("Canal", sorted(pm.canal.unique()), default=[])
zones = st.sidebar.multiselect("Zone de risque", sorted(pm.zone_risque.unique()), default=[])
hors_extreme = st.sidebar.toggle("Exclure le sinistre extrême (n° 1129, 2,48 M€)", value=False,
                                 help="Un seul sinistre auto de 2023 pèse autant que 2 ans de sinistres. Par défaut il est inclus pour réconcilier avec l'entrepôt.")
seuil = st.sidebar.slider("Seuil d'alerte du ratio sinistres/primes", 0.40, 1.00, SEUIL_DEFAUT, 0.05,
                          help="Hypothèse de travail : au-delà de 65 %, il reste moins de 35 % de la prime pour les frais et la marge. Les frais ne sont pas dans les données : à confirmer avec la direction.")
PAYE = "paye_hors_extreme" if hors_extreme else "paye"


def sel(df, region=True, canal="canal", zone="zone_risque"):
    if produits:
        df = df[df.produit.isin(produits)]
    if region and regions and "region" in df:
        df = df[df.region.isin(regions)]
    if canaux:
        df = df[df[canal].isin(canaux)]
    if zones:
        df = df[df[zone].isin(zones)]
    return df


def n_eff(df):
    return df.sinistres_avec_suite - (df.sinistres_extremes if hors_extreme else 0)


def kpis(df, last_month=None):
    expo, prime, paye = df.exposition.sum(), df.prime_acquise.sum(), df[PAYE].sum()
    n = n_eff(df).sum()
    actifs = df[df.mois.astype(str).str[:7] == last_month].contrats_actifs_fin_mois.sum() if last_month else np.nan
    return dict(prime=prime, actifs=actifs, freq=n / expo if expo else np.nan, cout=paye / n if n else np.nan,
                ratio=paye / prime if prime else np.nan, resil=df.resiliations.sum() / expo if expo else np.nan, expo=expo)


def shift_year(m):
    return f"{int(m[:4]) - 1}{m[4:]}"


# ================================================================== PAGE 1 : PORTEFEUILLE
if page == "Portefeuille":
    st.title("Portefeuille : où gagne-t-on, où perd-on de l'argent ?")
    base = sel(pm)
    m0, m1 = periode
    cur = base[(base.mois.astype(str).str[:7] >= m0) & (base.mois.astype(str).str[:7] <= m1)]
    prv = base[(base.mois.astype(str).str[:7] >= shift_year(m0)) & (base.mois.astype(str).str[:7] <= shift_year(m1))]
    k, kp = kpis(cur, m1), kpis(prv, shift_year(m1))
    if cur.empty:
        st.warning("Aucune donnée pour cette combinaison de filtres.")
        st.stop()
    if hors_extreme:
        st.info("Les indicateurs excluent le sinistre n° 1129. Les montants ne se réconcilient plus avec l'entrepôt complet.")
    elif cur.sinistres_extremes.sum() > 0:
        st.warning("La période contient le sinistre n° 1129 (2,48 M€ payés) : il pèse sur le coût moyen et le ratio. Activez le filtre « Exclure » pour voir le portefeuille courant.")
    c = st.columns(6)
    has_prev = prv.prime_acquise.sum() > 0

    def card(col, label, v, fmt, vp, inverse=False):
        delta = None
        if has_prev and pd.notna(v) and pd.notna(vp) and vp:
            delta = f"{(v / vp - 1) * 100:+.1f} % vs N-1".replace(".", ",")
        col.metric(label, fmt(v), delta, delta_color="inverse" if inverse else "normal")

    card(c[0], "Primes acquises", k["prime"], eur, kp["prime"])
    card(c[1], f"Contrats actifs fin {m1}", k["actifs"], num, kp["actifs"])
    card(c[2], "Fréquence (sinistres / année-police)", k["freq"], lambda x: pct(x, 2), kp["freq"], True)
    card(c[3], "Coût moyen", k["cout"], eur, kp["cout"], True)
    card(c[4], "Ratio sinistres / primes", k["ratio"], lambda x: pct(x, 1), kp["ratio"], True)
    card(c[5], "Résiliations / année-police", k["resil"], lambda x: pct(x, 1), kp["resil"], True)
    st.caption(f"Période {m0} → {m1}, comparée à la même période un an plus tôt. Les derniers mois sont incomplets : des sinistres sont encore en cours de règlement.")

    # --- ratio glissant 12 mois et alerte
    s = base.groupby("mois").agg(prime=("prime_acquise", "sum"), paye=(PAYE, "sum")).sort_index()
    s["ratio12"] = s.paye.rolling(12).sum() / s.prime.rolling(12).sum()
    s.index = s.index.astype(str).str[:7]
    w = s.loc[(s.index >= m0) & (s.index <= m1)].dropna()
    st.markdown("#### " + (
        f"Alerte : le ratio glissant sur 12 mois dépasse le seuil de {pct(seuil, 0)} en {w.index[-1]} ({pct(w.ratio12.iloc[-1], 1)})"
        if len(w) and w.ratio12.iloc[-1] > seuil else
        (f"Le ratio glissant sur 12 mois reste sous le seuil de {pct(seuil, 0)} ({pct(w.ratio12.iloc[-1], 1)} en {w.index[-1]})"
         if len(w) else "Ratio glissant sur 12 mois : période trop courte (12 mois d'historique requis)")))
    if len(w):
        over = w[w.ratio12 > seuil]
        if len(over):
            st.error(f"{len(over)} mois sur {len(w)} au-dessus du seuil de {pct(seuil, 0)} (pic : {pct(over.ratio12.max(), 0)} en {over.ratio12.idxmax()}).")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=w.index, y=w.ratio12, mode="lines", name="Ratio glissant 12 mois", line=dict(color=BLUE, width=2),
                                 hovertemplate="%{x}<br>Ratio : %{y:.1%}<extra></extra>"))
        if len(over):
            fig.add_trace(go.Scatter(x=over.index, y=over.ratio12, mode="markers", name="Au-dessus du seuil",
                                     marker=dict(color=ORANGE, size=9, line=dict(color="white", width=2)),
                                     hovertemplate="%{x}<br>Ratio : %{y:.1%} (alerte)<extra></extra>"))
        fig.add_hline(y=seuil, line=dict(color=ORANGE, dash="dash", width=1.5), annotation_text=f"Seuil {pct(seuil, 0)}")
        fig.update_yaxes(tickformat=".0%", title="Sinistres payés / primes acquises")
        st.plotly_chart(style(fig), width="stretch")
        table_view(w.reset_index().rename(columns={"mois": "mois", "ratio12": "ratio_12_mois"}))

    # --- évolution mensuelle comparée à l'année précédente
    annees = sorted(base.annee.unique())
    cc = st.columns([1, 1, 3])
    an = cc[0].selectbox("Année affichée", annees, index=annees.index(2024) if 2024 in annees else len(annees) - 1)
    ind = cc[1].selectbox("Indicateur", ["Primes acquises", "Sinistres avec suite", "Ratio sinistres / primes", "Résiliations"])
    g = base.groupby(["annee", "mois_num"]).agg(prime=("prime_acquise", "sum"), n=("sinistres_avec_suite", "sum"), n_ext=("sinistres_extremes", "sum"),
                                                paye=(PAYE, "sum"), resil=("resiliations", "sum")).reset_index()
    g["n"] = g["n"] - (g["n_ext"] if hors_extreme else 0)
    g["valeur"] = {"Primes acquises": g.prime, "Sinistres avec suite": g.n, "Ratio sinistres / primes": g.paye / g.prime.where(g.prime > 0),
                   "Résiliations": g.resil}[ind]
    a, b = g[g.annee == an].set_index("mois_num").valeur, g[g.annee == an - 1].set_index("mois_num").valeur
    tot_a, tot_b = a.sum() if ind != "Ratio sinistres / primes" else np.nan, b.sum() if ind != "Ratio sinistres / primes" else np.nan
    titre = f"{ind} : {an} comparé à {an - 1}"
    if pd.notna(tot_a) and pd.notna(tot_b) and tot_b:
        titre += f" ({(tot_a / tot_b - 1) * 100:+.0f} % sur les mois disponibles)".replace(".", ",")
    st.markdown("#### " + titre)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=b.index, y=b.values, name=str(an - 1), mode="lines+markers", line=dict(color=GRAY, width=2, dash="dot"), marker=dict(size=7),
                             hovertemplate="Mois %{x}<br>" + str(an - 1) + " : %{y:,.2f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=a.index, y=a.values, name=str(an), mode="lines+markers", line=dict(color=BLUE, width=2), marker=dict(size=7),
                             hovertemplate="Mois %{x}<br>" + str(an) + " : %{y:,.2f}<extra></extra>"))
    fig.update_xaxes(tickmode="linear", dtick=1, title="Mois de l'année")
    if ind == "Ratio sinistres / primes":
        fig.update_yaxes(tickformat=".0%")
    st.plotly_chart(style(fig, 340), width="stretch")
    if an == 2025:
        st.caption("2025 : six mois seulement, et des dossiers encore ouverts : le ratio est sous-estimé.")
    table_view(pd.DataFrame({str(an): a, str(an - 1): b}).reset_index().rename(columns={"mois_num": "mois"}))

# ================================================================== PAGE 2 : TECHNIQUE ET CLIENTS
elif page == "Technique et clients":
    st.title("Technique et clients : qui coûte, qui rapporte, qui reste ?")
    ts = mart("technique_segment")
    a0, a1 = int(periode[0][:4]), int(periode[1][:4])
    t = sel(ts, region=False, canal="canal", zone="zone_risque")
    t = t[(t.annee >= a0) & (t.annee <= a1)]
    st.caption("Années civiles couvrant la période choisie. Le filtre Région ne s'applique pas à ce mart (pas de région dans le grain technique). "
               "Sinistres rattachés à l'année de survenance ; les années récentes sont incomplètes.")
    if t.empty:
        st.warning("Aucune donnée pour cette combinaison de filtres.")
        st.stop()
    t = t.assign(paye_x=t[PAYE], n_x=t.sinistres_avec_suite - (t.sinistres_extremes if hors_extreme else 0))
    axe = st.radio("Axe d'analyse", ["zone_risque", "formule", "canal", "tranche_age"], horizontal=True,
                   format_func=lambda x: {"zone_risque": "Zone", "formule": "Formule", "canal": "Canal", "tranche_age": "Âge à la souscription"}[x])
    g = t.groupby(["produit", axe]).agg(prime=("prime_acquise", "sum"), paye=("paye_x", "sum"), n=("n_x", "sum"), expo=("exposition", "sum"),
                                        resil=("resiliations", "sum")).reset_index()
    g["ratio"], g["freq"], g["cout"], g["resil_an"] = g.paye / g.prime, g.n / g.expo, g.paye / g.n.where(g.n > 0), g.resil / g.expo
    g[axe] = g[axe].astype(str)
    worst = g.loc[g.ratio.idxmax()]
    st.markdown(f"#### Le ratio le plus élevé est {worst.produit.lower()} / {worst[axe]} ({pct(worst.ratio, 0)}) : "
                + ("c'est le coût moyen qui l'explique, pas la fréquence" if worst.cout > 2 * g.cout.median() else "à comparer à la fréquence et au coût moyen ci-dessous"))
    fig = go.Figure()
    for prod, col in (("AUTO", BLUE), ("HABITATION", AQUA)):
        d = g[g.produit == prod].sort_values(axe)
        fig.add_trace(go.Bar(x=d[axe], y=d.ratio, name=prod.capitalize(), marker_color=col, text=[pct(v, 0) for v in d.ratio], textposition="outside",
                             customdata=np.c_[d.freq, d.cout, d.resil_an], hovertemplate="%{x}<br>Ratio : %{y:.1%}<br>Fréquence : %{customdata[0]:.2%}<br>"
                             "Coût moyen : %{customdata[1]:,.0f} €<br>Résiliations / année-police : %{customdata[2]:.1%}<extra></extra>"))
    fig.add_hline(y=seuil, line=dict(color=ORANGE, dash="dash"), annotation_text=f"Seuil {pct(seuil, 0)}")
    fig.update_layout(barmode="group", bargap=0.35)
    fig.update_yaxes(tickformat=".0%", title="Sinistres payés / primes acquises")
    st.plotly_chart(style(fig), width="stretch")
    table_view(g.round(4))

    # --- décomposition
    dec = mart("decomposition_annuelle")
    per = "hors_extreme" if hors_extreme else "tous"
    d = dec[(dec.perimetre == per) & dec.var_ratio_log.notna()].copy()
    d["label"] = d.annee.astype(str) + np.where(d.annee == 2025, " (partielle)", "")
    top = d.loc[d.var_ratio_log.abs().idxmax()]
    eff = {"effet_frequence": "de la fréquence", "effet_cout": "du coût moyen", "effet_prime": "de la prime moyenne"}
    main = max(eff, key=lambda c_: abs(top[c_]))
    st.markdown(f"#### {int(top.annee)} : le ratio varie de {top.var_ratio_log:+.0%} (en log), surtout à cause {eff[main]}".replace(".", ","))
    st.caption("Ratio = fréquence × coût moyen ÷ prime moyenne. En logarithme, les trois effets s'additionnent. Le volume de contrats s'annule dans le ratio : "
               "il agit sur les montants et sur le poids des segments. 2020 est le démarrage du portefeuille, 2025 est partielle.")
    fig = go.Figure()
    for col, nom, couleur in (("effet_frequence", "Fréquence", BLUE), ("effet_cout", "Coût moyen", ORANGE), ("effet_prime", "Prime moyenne", AQUA)):
        fig.add_trace(go.Bar(x=d.label, y=d[col], name=nom, marker_color=couleur, hovertemplate="%{x}<br>" + nom + " : %{y:+.2f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=d.label, y=d.var_ratio_log, mode="markers", name="Variation totale du ratio",
                             marker=dict(color="black", size=10, symbol="diamond", line=dict(color="white", width=2)),
                             hovertemplate="%{x}<br>Variation totale : %{y:+.2f}<extra></extra>"))
    fig.update_layout(barmode="relative")
    fig.update_yaxes(title="Variation en logarithme (positif = dégradation)")
    st.plotly_chart(style(fig), width="stretch")
    table_view(d.drop(columns="label").round(4))

    ct = mart("contribution_segment")
    ct = ct[ct.perimetre == per]
    an = st.selectbox("Année de la contribution des segments", sorted(ct.annee.unique()), index=2)
    c1 = ct[ct.annee == an].assign(segment=lambda x: x.produit.str.capitalize() + " · zone " + x.zone_risque.astype(str)).sort_values("contribution")
    pire, mieux = c1.iloc[-1], c1.iloc[0]
    st.markdown(f"#### {an} : {pire.segment.lower()} contribue le plus à la dégradation ({pire.contribution:+.2f} pt de ratio) ; {mieux.segment.lower()} le plus à l'amélioration ({mieux.contribution:+.2f})".replace(".", ","))
    fig = go.Figure(go.Bar(x=c1.contribution, y=c1.segment, orientation="h", marker_color=np.where(c1.contribution > 0, ORANGE, BLUE),
                           customdata=np.c_[c1.ratio_avant, c1.ratio_apres, c1.poids_apres],
                           hovertemplate="%{y}<br>Contribution : %{x:+.3f}<br>Ratio : %{customdata[0]:.0%} → %{customdata[1]:.0%}<br>Poids dans les primes : %{customdata[2]:.1%}<extra></extra>"))
    fig.update_xaxes(title="Contribution à la variation du ratio global (orange : dégrade, bleu : améliore)")
    st.plotly_chart(style(fig, 360), width="stretch")
    table_view(c1.round(4))

    # --- rétention
    st.divider()
    ret = mart("retention_cohorte")
    pr = st.radio("Produit (rétention)", ["AUTO", "HABITATION"], horizontal=True)
    rr = ret[ret.produit == pr]
    piv, eli = rr.pivot(index="cohorte", columns="annee_anniversaire", values="retention"), rr.pivot(index="cohorte", columns="annee_anniversaire", values="contrats_eligibles")
    st.markdown(f"#### Rétention {pr.lower()} : environ {pct(rr[rr.annee_anniversaire == 1].contrats_retenus.sum() / rr[rr.annee_anniversaire == 1].contrats_eligibles.sum(), 0)} des contrats sont encore là au 1er anniversaire, quelle que soit la cohorte")
    st.caption("Chaque case ne porte que sur les contrats dont l'anniversaire est déjà passé (30/06/2025) : la cohorte 2024 à 1 an ne couvre que les souscriptions antérieures à juillet 2024. "
               "Une rétention « au k-ième anniversaire » ne dit rien des contrats récents.")
    fig = go.Figure(go.Heatmap(z=piv.values * 100, x=[f"an {c_}" for c_ in piv.columns], y=piv.index.astype(str), colorscale=[[0, "#cfe1f7"], [1, "#0f3f7a"]],
                               text=np.where(np.isnan(piv.values), "", np.round(piv.values * 100, 0).astype("float").astype(str)), texttemplate="%{text} %",
                               customdata=eli.values, hovertemplate="Cohorte %{y}, %{x}<br>Rétention : %{z:.1f} %<br>Contrats observables : %{customdata:,.0f}<extra></extra>",
                               colorbar=dict(title="%"), zmin=40, zmax=90))
    fig.update_yaxes(autorange="reversed", title="Cohorte de souscription")
    st.plotly_chart(style(fig, 330), width="stretch")
    table_view(rr.round(4))

    # --- valeur client
    st.divider()
    vc, par, prof = mart("valeur_client"), mart("pareto_valeur"), mart("profil_decile")
    p1 = par[par.perimetre == per].sort_values("pct_clients")
    top10 = p1[p1.pct_clients == 10].part_cumulee_valeur.iloc[0]
    st.markdown(f"#### Les 10 % de clients les plus rentables apportent {pct(top10, 0)} de la valeur nette ; 6,7 % des clients sont déficitaires")
    st.caption("Valeur observée = primes acquises − sinistres payés au 30/06/2025 (pas une valeur future). Les pourcentages cumulés dépassent 100 % avant de redescendre : "
               "les clients déficitaires retranchent de la valeur. La valeur dépend beaucoup de l'ancienneté : voir la valeur par année-police ci-dessous.")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[0, 100], y=[0, 1], mode="lines", name="Répartition égale", line=dict(color=GRAY, dash="dot", width=1.5), hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=p1.pct_clients, y=p1.part_cumulee_valeur, mode="lines", name="Valeur nette cumulée" + (" (hors n° 1129)" if hors_extreme else ""),
                             line=dict(color=BLUE, width=2), hovertemplate="%{x} % des clients<br>%{y:.0%} de la valeur nette<extra></extra>"))
    fig.update_xaxes(title="% de clients, du plus au moins rentable")
    fig.update_yaxes(tickformat=".0%", title="Part cumulée de la valeur nette")
    st.plotly_chart(style(fig, 340), width="stretch")
    c2 = st.columns(2)
    vv = vc[~vc.client_sinistre_extreme] if hors_extreme else vc
    if regions:
        vv = vv[vv.region.isin(regions)]
    c2[0].metric("Clients (filtrés)", num(len(vv)))
    c2[1].metric("Valeur nette (filtrée)", eur(vv.valeur.sum()))
    table_view(prof.round(2), "Profil par décile de valeur (hors sinistre extrême)")

# ================================================================== PAGE 3 : EXPLOITATION
elif page == "Exploitation":
    st.title("Exploitation : la chaîne de données est-elle fiable, les sinistres sont-ils traités à temps ?")
    runs, tests, chg, fr, rej, reg = (mart(n) for n in ("ops_runs", "ops_tests", "ops_chargement_source", "ops_fraicheur", "ops_rejets_regle", "ops_regles_qualite"))
    last = runs.sort_values("started_at").iloc[-1]
    ok = int((tests.status == "OK").sum())
    c = st.columns(4)
    c[0].metric("Dernier lancement", str(last.started_at)[:16], last.status)
    c[1].metric("Tests bloquants réussis", f"{ok} / {len(tests)}")
    c[2].metric("Lignes en quarantaine", num(rej[rej.rule_id != "LECTURE"].lignes.sum()))
    c[3].metric("Règles de qualité avec anomalie", f"{int((reg.volume > 0).sum())} / {len(reg)}")
    if ok < len(tests) or last.status != "SUCCES":
        st.error("Le dernier lancement est en échec : le cœur est resté dans son dernier état valide. Voir les tests ci-dessous.")
    st.markdown("#### Dernier chargement par source")
    fr2 = fr.assign(retard_jours=(pd.to_datetime(fr.date_extraction) - pd.to_datetime(fr.derniere_date_metier)).dt.days)
    st.dataframe(chg.merge(fr2, on="source").rename(columns={"derniere_date_metier": "dernière_date_métier"}), width="stretch", hide_index=True)
    st.caption("Fraîcheur : écart entre la date d'extraction (30/06/2025) et la dernière date métier de la source (les contrats ne sont souscrits que jusqu'au 30/03/2025).")
    c = st.columns(2)
    with c[0]:
        r = rej[rej.rule_id != "LECTURE"].sort_values("lignes")
        r = r.assign(regle=r.rule_id + " · " + r.entity)
        st.markdown(f"#### {num(r.lignes.sum())} lignes écartées du cœur, retrouvables avec leur motif")
        fig = go.Figure(go.Bar(x=r.lignes, y=r.regle, orientation="h", marker_color=BLUE, text=r.lignes, textposition="outside",
                               customdata=r.exemple_motif, hovertemplate="%{y}<br>%{x} lignes<br>%{customdata}<extra></extra>"))
        st.plotly_chart(style(fig, 330), width="stretch")
    with c[1]:
        st.markdown(f"#### {ok} tests sur {len(tests)} réussis au dernier lancement")
        st.dataframe(tests[["test_id", "status", "violations", "description"]], width="stretch", hide_index=True, height=330)
    table_view(reg, "Règles de qualité (volume constaté, gravité, traitement)")

    st.divider()
    dl = mart("delais_garantie")
    etapes = {"declaration": "Survenance → déclaration", "premier_reglement": "Déclaration → premier règlement", "cloture_approx": "Déclaration → dernier règlement (clôture approximée)"}
    et = st.radio("Délai", list(etapes), format_func=etapes.get, horizontal=True)
    d = dl[dl.etape == et].assign(g=lambda x: x.produit.str.capitalize() + " · " + x.libelle).sort_values("mediane")
    if hors_extreme or produits != ["AUTO", "HABITATION"]:
        d = d[d.produit.isin(produits)] if produits else d
    pire = d.loc[d.q90.idxmax()]
    st.markdown(f"#### Premier règlement : la moitié des dossiers est payée en moins de {d.mediane.median():.0f} jours, mais 1 dossier sur 10 dépasse {d.q90.median():.0f} jours".replace("Premier règlement", etapes[et].split(" → ")[-1].capitalize())
                if et != "declaration" else f"#### Déclaration : médiane de {d.mediane.median():.0f} jours, 1 sinistre sur 10 déclaré après plus de {d.q90.median():.0f} jours")
    fig = go.Figure()
    fig.add_trace(go.Bar(y=d.g, x=d.mediane, orientation="h", name="Médiane", marker_color=BLUE, text=d.mediane.round(0).astype(int), textposition="outside"))
    fig.add_trace(go.Bar(y=d.g, x=d.q90, orientation="h", name="90e percentile", marker_color=GRAY, text=d.q90.round(0).astype(int), textposition="outside",
                         customdata=np.c_[d.n, d.q75, d.q95, d.maximum], hovertemplate="%{y}<br>90e percentile : %{x:.0f} j<br>n = %{customdata[0]}<br>75e : %{customdata[1]:.0f} j · 95e : %{customdata[2]:.0f} j · max : %{customdata[3]:.0f} j<extra></extra>"))
    fig.update_layout(barmode="group")
    fig.update_xaxes(title="Jours")
    st.plotly_chart(style(fig, 360), width="stretch")
    if et == "cloture_approx":
        st.caption("La source ne fournit pas de date de clôture : approximée par la date du dernier règlement, sur les sinistres clôturés avec règlement. Les dossiers ouverts sont exclus.")
    if et == "premier_reglement":
        st.caption("Sinistres ayant reçu au moins un règlement. 98 des 154 dossiers ouverts de 2025 n'en ont pas encore reçu : ils ne sont pas dans ces quantiles.")
    table_view(d.drop(columns="g").round(1))

    st.divider()
    au = mart("audit_critere")
    gl = au[au.critere == "global"].iloc[0]
    st.markdown(f"#### Audits antifraude : {pct(gl.taux_confirmation, 1)} de fraudes confirmées, mais seulement parmi les {num(gl.audites)} dossiers audités ({pct(gl.couverture_audit, 0)} des sinistres)")
    st.caption("Ce taux ne vaut que pour la population auditée, qui n'est pas tirée au hasard : il ne mesure pas la fraude du portefeuille.")
    crit = st.radio("Critère d'audit", ["garantie", "tranche_reserve", "statut", "produit"], horizontal=True)
    a = au[au.critere == crit].sort_values("modalite")
    fig = go.Figure()
    fig.add_trace(go.Bar(x=a.modalite, y=a.taux_confirmation, name="Taux de confirmation (audités)", marker_color=BLUE, text=[pct(v, 0) for v in a.taux_confirmation], textposition="outside",
                         customdata=np.c_[a.audites, a.fraudes_confirmees, a.couverture_audit], hovertemplate="%{x}<br>Confirmation : %{y:.1%}<br>%{customdata[1]} fraudes sur %{customdata[0]} audités<br>Part des sinistres audités : %{customdata[2]:.0%}<extra></extra>"))
    fig.add_trace(go.Bar(x=a.modalite, y=a.couverture_audit, name="Part des sinistres audités", marker_color=GRAY, text=[pct(v, 0) for v in a.couverture_audit], textposition="outside", hoverinfo="skip"))
    fig.update_layout(barmode="group")
    fig.update_yaxes(tickformat=".0%")
    st.plotly_chart(style(fig, 340), width="stretch")
    table_view(a.round(3))

# ================================================================== PAGE 4 : DÉFINITIONS
else:
    st.title("Définitions des indicateurs")
    st.caption("Chaque chiffre du tableau de bord vient de l'entrepôt (schéma marts). Période d'observation : 01/01/2020 → 30/06/2025.")
    DEFS = [
        ("Année-police (exposition)", "Durée pendant laquelle un contrat est couvert, en années. 1,0 = une année complète. Date d'effet incluse, résiliation exclue. C'est le dénominateur de toute fréquence : un contrat observé 3 mois pèse 0,25."),
        ("Prime acquise", "Part de la prime annuelle correspondant à la période de couverture écoulée : prime annuelle × jours couverts ÷ jours de l'année."),
        ("Contrats actifs", "Contrats en vigueur le dernier jour du mois (effet passé, pas encore résiliés)."),
        ("Sinistre avec suite", "Sinistre au statut CLOTURE ou OUVERT. Les sinistres SANS_SUITE et REJETE sont comptés à part : ils n'ont aucun effet financier."),
        ("Fréquence", "Sinistres avec suite ÷ années-police, par année de survenance. Jamais divisée par le nombre de contrats."),
        ("Coût moyen", "Montant payé ÷ nombre de sinistres avec suite. Les dossiers ouverts ne sont pas soldés : le coût est légèrement sous-estimé. Très sensible aux sinistres extrêmes."),
        ("Ratio sinistres / primes (S/P)", "Sinistres payés ÷ primes acquises. Sans les réserves ni les frais de gestion. Les années récentes sont sous-estimées (dossiers en cours)."),
        ("Ratio glissant 12 mois", "Somme des sinistres payés des 12 derniers mois ÷ somme des primes acquises des 12 derniers mois. Lisse la saisonnalité."),
        ("Seuil d'alerte", "Hypothèse de travail à 65 % : il resterait 35 % de la prime pour les frais et la marge. Les frais ne figurent pas dans les données : à valider avec la direction. Réglable dans la barre latérale."),
        ("Taux de résiliation", "Résiliations de la période ÷ années-police de la période. Ce n'est pas la part de contrats perdus."),
        ("Sinistre extrême", "Sinistre dont le cumul payé dépasse 500 000 € : un seul dossier (n° 1129, 2,48 M€). Il peut être exclu avec le filtre de la barre latérale."),
        ("Décomposition du ratio", "Ratio = fréquence × coût moyen ÷ prime moyenne. En logarithme, la variation du ratio est la somme de l'effet fréquence, de l'effet coût et de l'effet prime. Le volume s'annule dans le ratio."),
        ("Contribution d'un segment", "Variation, d'une année à l'autre, de (payé du segment ÷ primes totales). La somme des contributions est égale à la variation du ratio global."),
        ("Rétention par cohorte", "Parmi les contrats souscrits une année donnée, part encore en vigueur au k-ième anniversaire. Calculée seulement quand l'anniversaire est observable (au plus tard le 30/06/2025)."),
        ("Valeur observée d'un client", "Primes acquises − sinistres payés, tous contrats confondus, au 30/06/2025. Ce n'est pas une valeur future et elle croît avec l'ancienneté."),
        ("Courbe de Pareto", "Clients triés du plus au moins rentable ; part cumulée de la valeur nette. Dépasse 100 % car les clients déficitaires retranchent de la valeur."),
        ("Délais de gestion", "Déclaration : survenance → déclaration. Premier règlement : déclaration → premier paiement. Clôture approximée : déclaration → dernier paiement, sur les sinistres clôturés (la source n'a pas de date de clôture)."),
        ("Taux de confirmation de fraude", "Fraudes confirmées ÷ dossiers audités. Ne vaut que pour la population auditée, non représentative du portefeuille."),
        ("Quarantaine", "Lignes écartées du cœur avec la règle et le motif. Rien n'est supprimé : tout écart de total reste explicable."),
    ]
    for nom, txt in DEFS:
        st.markdown(f"**{nom}** : {txt}")
