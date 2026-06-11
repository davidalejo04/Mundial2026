import streamlit as st
import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import Normalize
import matplotlib.cm as cm
import os

# ─────────────────────────────────────────────
# CONFIGURACIÓN DE PÁGINA
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Mundial 2026 — Simulación Dixon-Coles",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# CSS PERSONALIZADO
# ─────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #0f172a; }
    .stApp { background-color: #0f172a; }
    
    .metric-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 16px 20px;
        text-align: center;
    }
    .metric-label { color: #94a3b8; font-size: 13px; margin-bottom: 4px; }
    .metric-value { color: #f8fafc; font-size: 28px; font-weight: 700; }
    .metric-sub   { color: #64748b; font-size: 12px; margin-top: 4px; }

    .match-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 12px 16px;
        margin-bottom: 8px;
    }
    .match-teams { font-size: 15px; color: #f8fafc; font-weight: 600; }
    .match-score { font-size: 22px; font-weight: 700; }
    .score-win   { color: #34d399; }
    .score-draw  { color: #fbbf24; }
    .score-lose  { color: #94a3b8; }
    .match-meta  { font-size: 11px; color: #64748b; margin-top: 4px; }

    .section-header {
        background: linear-gradient(90deg, #0f766e, #1e293b);
        border-left: 4px solid #2dd4bf;
        padding: 10px 16px;
        border-radius: 6px;
        margin: 16px 0 12px 0;
        color: #f8fafc;
        font-weight: 700;
        font-size: 16px;
    }

    .rival-row {
        display: flex;
        align-items: center;
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 6px;
        gap: 12px;
    }
    .prob-bar-bg {
        background: #334155;
        border-radius: 4px;
        height: 6px;
        width: 100%;
    }
    .prob-bar-fill {
        background: #2dd4bf;
        border-radius: 4px;
        height: 6px;
    }

    div[data-testid="stSelectbox"] label { color: #94a3b8 !important; }
    div[data-testid="stMultiSelect"] label { color: #94a3b8 !important; }
    h1, h2, h3 { color: #f8fafc !important; }
    p { color: #cbd5e1; }
    
    .stTabs [data-baseweb="tab-list"] { background-color: #1e293b; border-radius: 8px; }
    .stTabs [data-baseweb="tab"] { color: #94a3b8; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { color: #2dd4bf; background-color: #0f766e22; }

    .badge-win  { background: #064e3b; color: #34d399; padding: 2px 8px; border-radius: 999px; font-size: 11px; font-weight: 600; }
    .badge-draw { background: #451a03; color: #fbbf24; padding: 2px 8px; border-radius: 999px; font-size: 11px; font-weight: 600; }
    .badge-lose { background: #1e1b4b; color: #818cf8; padding: 2px 8px; border-radius: 999px; font-size: 11px; font-weight: 600; }
    
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# CARGA DE DATOS
# ─────────────────────────────────────────────
@st.cache_data
def load_data():
    base = os.path.dirname(os.path.abspath(__file__))
    
    res_path    = os.path.join(base, "RESDEF3.xlsx")
    pri_path    = os.path.join(base, "PRIDEF3.xlsx")
    estudio_path= os.path.join(base, "EstudioEstadisticoMundial.xlsx")

    df_res = pd.read_excel(res_path)
    df_pri = pd.read_excel(pri_path)
    df_est = pd.read_excel(estudio_path)

    for df in [df_res, df_pri, df_est]:
        df.columns = [c.strip() for c in df.columns]

    df_est_sel = df_est[df_est.get("Escogido", df_est.iloc[:, 0]) == "Y"].copy() if "Escogido" in df_est.columns else df_est.copy()

    df_res["Fase"]      = df_res["Fase"].str.strip()
    df_res["Local"]     = df_res["Local"].str.strip()
    df_res["Visitante"] = df_res["Visitante"].str.strip()
    df_res["Indicador"] = df_res["Indicador"].str.strip()

    df_pri["Fase"]      = df_pri["Fase"].str.strip()
    df_pri["Local"]     = df_pri["Local"].str.strip()
    df_pri["Visitante"] = df_pri["Visitante"].str.strip()
    df_pri["Indicador"] = df_pri["Indicador"].str.strip()

    team_group = {}
    if "Selección" in df_est_sel.columns and "Grupo" in df_est_sel.columns:
        team_group = dict(zip(df_est_sel["Selección"].str.strip(), df_est_sel["Grupo"].str.strip()))

    return df_res, df_pri, df_est_sel, team_group

df_res, df_pri, df_est, team_group = load_data()

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
FASES_ORDEN = ["Grupos", "16vos", "8vos", "4tos", "semi", "3ros", "Final"]

def indicador_to_badge(ind, equipo, local, visitante):
    if ind == "GanaLocal":
        return '<span class="badge-win">Victoria</span>' if equipo == local else '<span class="badge-lose">Derrota</span>'
    elif ind == "GanaVisitante":
        return '<span class="badge-win">Victoria</span>' if equipo == visitante else '<span class="badge-lose">Derrota</span>'
    else:
        return '<span class="badge-draw">Empate</span>'

def get_score_html(gl, gv, ind):
    if ind == "GanaLocal":
        return f'<span class="score-win">{gl}</span> - <span class="score-lose">{gv}</span>'
    elif ind == "GanaVisitante":
        return f'<span class="score-lose">{gl}</span> - <span class="score-win">{gv}</span>'
    else:
        return f'<span class="score-draw">{gl} - {gv}</span>'

def partidos_del_equipo(df, equipo):
    mask = (df["Local"] == equipo) | (df["Visitante"] == equipo)
    return df[mask].copy()

def calc_esperanza(df_mc, equipo, rival=None, fase=None):
    mask = (df_mc["Local"] == equipo) | (df_mc["Visitante"] == equipo)
    if rival:
        mask &= (df_mc["Local"] == rival) | (df_mc["Visitante"] == rival)
    if fase:
        mask &= df_mc["Fase"] == fase
    sub = df_mc[mask]
    if len(sub) == 0:
        return None, None, None

    total = len(sub)
    wins = ((sub["Local"] == equipo) & (sub["Indicador"] == "GanaLocal")).sum() + \
           ((sub["Visitante"] == equipo) & (sub["Indicador"] == "GanaVisitante")).sum()
    draws = (sub["Indicador"] == "Empate").sum()
    losses = total - wins - draws

    return wins / total, draws / total, losses / total


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚽ Mundial 2026")
    st.markdown("**Simulación Dixon-Coles**")
    st.divider()

    todos_los_equipos = sorted(set(df_res["Local"].tolist() + df_res["Visitante"].tolist()))
    equipo_sel = st.selectbox("🔍 Seleccionar equipo", ["— Todos —"] + todos_los_equipos)

    fases_disp = [f for f in FASES_ORDEN if f in df_res["Fase"].unique()]
    fase_sel   = st.selectbox("📅 Fase del torneo", ["— Todas —"] + fases_disp)

    st.divider()
    st.markdown("#### 🔗 Fuente de datos")
    fuente = st.radio("", ["Archivos locales (Excel)", "MS Fabric / OneLake"], index=0)
    if fuente == "MS Fabric / OneLake":
        st.text_input("SQL Endpoint", placeholder="servidor.database.fabric.microsoft.com")
        st.text_input("Base de datos", placeholder="nombre_lakehouse")
        st.info("Configura la cadena de conexión en `load_data()` usando `pyodbc` con el driver de Azure SQL.")

    st.divider()
    st.caption("Modelo: Dixon-Coles con corrección τ  \nMétodo: Monte Carlo — CDF inversa")


# ─────────────────────────────────────────────
# FILTROS ACTIVOS
# ─────────────────────────────────────────────
df_filtrado = df_res.copy()
if fase_sel != "— Todas —":
    df_filtrado = df_filtrado[df_filtrado["Fase"] == fase_sel]
if equipo_sel != "— Todos —":
    df_filtrado = df_filtrado[(df_filtrado["Local"] == equipo_sel) | (df_filtrado["Visitante"] == equipo_sel)]


# ─────────────────────────────────────────────
# CABECERA
# ─────────────────────────────────────────────
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    titulo = f"🌍 Mundial 2026"
    if equipo_sel != "— Todos —":
        titulo += f" — {equipo_sel}"
    if fase_sel != "— Todas —":
        titulo += f" ({fase_sel})"
    st.title(titulo)
    grupo_equipo = team_group.get(equipo_sel, "")
    if grupo_equipo:
        st.caption(f"Grupo {grupo_equipo} · Simulación Dixon-Coles")

with col_h2:
    if equipo_sel != "— Todos —":
        pw, pd_, pl = calc_esperanza(df_pri, equipo_sel, fase=fase_sel if fase_sel != "— Todas —" else None)
        if pw is not None:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Esperanza de triunfo</div>
                <div class="metric-value">{pw:.0%}</div>
                <div class="metric-sub">E:{pd_:.0%} · D:{pl:.0%}</div>
            </div>
            """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# MÉTRICAS GLOBALES
# ─────────────────────────────────────────────
st.divider()
total_p = len(df_filtrado)
total_goles = df_filtrado["Goles_L"].sum() + df_filtrado["Goles_V"].sum()
pct_local = (df_filtrado["Indicador"] == "GanaLocal").sum() / max(total_p, 1)
pct_emp   = (df_filtrado["Indicador"] == "Empate").sum()  / max(total_p, 1)
pct_visit = (df_filtrado["Indicador"] == "GanaVisitante").sum() / max(total_p, 1)

c1, c2, c3, c4, c5 = st.columns(5)
for col, label, val, sub in [
    (c1, "Partidos",     total_p,              "en selección"),
    (c2, "Goles totales",total_goles,           f"{total_goles/max(total_p,1):.1f} por partido"),
    (c3, "Victoria local",f"{pct_local:.0%}",   f"{int(pct_local*total_p)} partidos"),
    (c4, "Empates",       f"{pct_emp:.0%}",     f"{int(pct_emp*total_p)} partidos"),
    (c5, "Victoria visit.",f"{pct_visit:.0%}",  f"{int(pct_visit*total_p)} partidos"),
]:
    col.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{val}</div>
        <div class="metric-sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# TABS PRINCIPALES
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Partidos", "🏆 Rivales & Esperanzas", "📊 Tabla de Grupos", "🕸️ Grafo de Correlaciones", "🏟️ Cuadrangulares"])


# ══════════════════════════════════════════════
# TAB 1 — PARTIDOS
# ══════════════════════════════════════════════
with tab1:
    st.markdown(f'<div class="section-header">📋 Resultados más probables — {len(df_filtrado)} partidos</div>', unsafe_allow_html=True)

    fases_en_filtro = [f for f in FASES_ORDEN if f in df_filtrado["Fase"].unique()]
    for fase in fases_en_filtro:
        df_fase = df_filtrado[df_filtrado["Fase"] == fase]
        st.markdown(f"**{fase}** &nbsp;·&nbsp; <span style='color:#64748b'>{len(df_fase)} partidos</span>", unsafe_allow_html=True)
        
        cols_per_row = 3
        rows = [df_fase.iloc[i:i+cols_per_row] for i in range(0, len(df_fase), cols_per_row)]
        for row_df in rows:
            cols = st.columns(cols_per_row)
            for ci, (_, m) in enumerate(row_df.iterrows()):
                score_html = get_score_html(int(m["Goles_L"]), int(m["Goles_V"]), m["Indicador"])
                badge = indicador_to_badge(m["Indicador"], equipo_sel, m["Local"], m["Visitante"]) if equipo_sel != "— Todos —" else ""
                with cols[ci]:
                    st.markdown(f"""
                    <div class="match-card">
                        <div class="match-teams">{m["Local"]} vs {m["Visitante"]} {badge}</div>
                        <div class="match-score">{score_html}</div>
                        <div class="match-meta">P{int(m["Partido"])} · {m["Lugar"]} · {m["Fase"]}</div>
                    </div>
                    """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)


# ══════════════════════════════════════════════
# TAB 2 — RIVALES & ESPERANZAS
# ══════════════════════════════════════════════
with tab2:
    if equipo_sel == "— Todos —":
        st.info("Selecciona un equipo en el panel lateral para ver sus rivales y esperanzas de triunfo.")
    else:
        fase_filtro = fase_sel if fase_sel != "— Todas —" else None
        df_eq = partidos_del_equipo(df_filtrado, equipo_sel)

        st.markdown(f'<div class="section-header">🏆 Rivales de {equipo_sel}</div>', unsafe_allow_html=True)

        if len(df_eq) == 0:
            st.warning("No hay partidos registrados para este equipo en la fase seleccionada.")
        else:
            for _, m in df_eq.iterrows():
                rival = m["Visitante"] if m["Local"] == equipo_sel else m["Local"]
                es_local = m["Local"] == equipo_sel

                pw, pd_, pl = calc_esperanza(df_pri, equipo_sel, rival=rival, fase=m["Fase"])
                
                goles_eq   = int(m["Goles_L"]) if es_local else int(m["Goles_V"])
                goles_rival= int(m["Goles_V"]) if es_local else int(m["Goles_L"])

                if m["Indicador"] == "Empate":
                    res_label = "Empate"; res_color = "#fbbf24"
                elif (m["Indicador"] == "GanaLocal" and es_local) or (m["Indicador"] == "GanaVisitante" and not es_local):
                    res_label = "Victoria"; res_color = "#34d399"
                else:
                    res_label = "Derrota"; res_color = "#f87171"

                cond_str = f"{'Local' if es_local else 'Visitante'} · {m['Fase']} · P{int(m['Partido'])}"
                bar_w   = int((pw or 0) * 100)

                st.markdown(f"""
                <div class="match-card" style="border-left: 3px solid {res_color};">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <div class="match-teams">{equipo_sel} <span style="color:#64748b">vs</span> {rival}</div>
                            <div class="match-meta">{cond_str}</div>
                        </div>
                        <div style="text-align:right;">
                            <div class="match-score" style="color:{res_color}">{goles_eq} - {goles_rival}</div>
                            <div style="font-size:11px;color:{res_color};font-weight:600;">{res_label}</div>
                        </div>
                    </div>
                    <div style="margin-top:10px; display:grid; grid-template-columns:1fr 1fr 1fr; gap:8px; text-align:center;">
                        <div>
                            <div style="font-size:11px;color:#94a3b8;">Victoria</div>
                            <div style="font-size:18px;font-weight:700;color:#34d399;">{f"{pw:.0%}" if pw is not None else "—"}</div>
                        </div>
                        <div>
                            <div style="font-size:11px;color:#94a3b8;">Empate</div>
                            <div style="font-size:18px;font-weight:700;color:#fbbf24;">{f"{pd_:.0%}" if pd_ is not None else "—"}</div>
                        </div>
                        <div>
                            <div style="font-size:11px;color:#94a3b8;">Derrota</div>
                            <div style="font-size:18px;font-weight:700;color:#f87171;">{f"{pl:.0%}" if pl is not None else "—"}</div>
                        </div>
                    </div>
                    <div style="margin-top:8px;">
                        <div class="prob-bar-bg">
                            <div class="prob-bar-fill" style="width:{bar_w}%;"></div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown(f'<div class="section-header">📈 Resumen estadístico — {equipo_sel}</div>', unsafe_allow_html=True)
        pw_t, pd_t, pl_t = calc_esperanza(df_pri, equipo_sel, fase=fase_filtro)
        if pw_t is not None:
            gf = df_eq.apply(lambda r: r["Goles_L"] if r["Local"] == equipo_sel else r["Goles_V"], axis=1).sum()
            gc = df_eq.apply(lambda r: r["Goles_V"] if r["Local"] == equipo_sel else r["Goles_L"], axis=1).sum()
            c1, c2, c3, c4 = st.columns(4)
            for col, label, val in [(c1,"Goles a favor",gf),(c2,"Goles en contra",gc),
                                    (c3,"Diferencia",gf-gc),(c4,"Partidos jugados",len(df_eq))]:
                col.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">{label}</div>
                    <div class="metric-value">{val}</div>
                </div>
                """, unsafe_allow_html=True)


# ══════════════════════════════════════════════
# TAB 3 — TABLA DE GRUPOS
# ══════════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-header">🏅 Tablas de posiciones — Fase de Grupos</div>', unsafe_allow_html=True)

    standings = {}
    for team, grupo in team_group.items():
        standings[team] = {"grupo": grupo, "pj": 0, "gf": 0, "gc": 0, "pts": 0}

    for _, row in df_res[df_res["Fase"] == "Grupos"].iterrows():
        loc, vis = row["Local"], row["Visitante"]
        gl, gv = int(row["Goles_L"]), int(row["Goles_V"])
        for t in [loc, vis]:
            if t not in standings:
                standings[t] = {"grupo": team_group.get(t, "?"), "pj": 0, "gf": 0, "gc": 0, "pts": 0}
        standings[loc]["pj"] += 1; standings[vis]["pj"] += 1
        standings[loc]["gf"] += gl; standings[loc]["gc"] += gv
        standings[vis]["gf"] += gv; standings[vis]["gc"] += gl
        if gl > gv:   standings[loc]["pts"] += 3
        elif gv > gl: standings[vis]["pts"] += 3
        else:         standings[loc]["pts"] += 1; standings[vis]["pts"] += 1

    grupos_letras = sorted(set(v["grupo"] for v in standings.values()))
    
    col_fg1, col_fg2 = st.columns([1, 3])
    with col_fg1:
        grupo_filtro = st.selectbox("Filtrar grupo", ["Todos"] + grupos_letras)

    grupos_a_mostrar = grupos_letras if grupo_filtro == "Todos" else [grupo_filtro]
    cols_por_fila = 4
    grupos_rows = [grupos_a_mostrar[i:i+cols_por_fila] for i in range(0, len(grupos_a_mostrar), cols_por_fila)]

    for fila in grupos_rows:
        cols = st.columns(len(fila))
        for ci, letra in enumerate(fila):
            equipos = [{"team": t, **v} for t, v in standings.items() if v["grupo"] == letra]
            equipos.sort(key=lambda x: (x["pts"], x["gf"] - x["gc"], x["gf"]), reverse=True)

            with cols[ci]:
                st.markdown(
                    f"<div style='background:#0f766e;padding:8px 12px;border-radius:8px 8px 0 0;"
                    f"font-weight:700;color:#f8fafc;font-size:14px;margin-bottom:0;'>"
                    f"GRUPO {letra}</div>",
                    unsafe_allow_html=True
                )

                rows_df = []
                for i, eq in enumerate(equipos):
                    dg = eq["gf"] - eq["gc"]
                    pos_icons = ["🟢", "🟢", "🟡", "🔴"]
                    icon = pos_icons[min(i, 3)]
                    nombre = ("★ " if equipo_sel != "— Todos —" and eq["team"] == equipo_sel else "") + eq["team"]
                    rows_df.append({
                        "#": f"{icon} {i+1}",
                        "Selección": nombre,
                        "PJ": eq["pj"],
                        "GF": eq["gf"],
                        "DG": f"+{dg}" if dg > 0 else str(dg),
                        "PTS": eq["pts"],
                    })

                df_grupo = pd.DataFrame(rows_df)

                def color_pts(val):
                    return "color: #2dd4bf; font-weight: bold"

                def color_pos(val):
                    if "🟢" in str(val): return "color: #34d399; font-weight: bold"
                    if "🟡" in str(val): return "color: #fbbf24; font-weight: bold"
                    return "color: #f87171; font-weight: bold"

                styled = (
                    df_grupo.style
                    .map(color_pts, subset=["PTS"])
                    .map(color_pos, subset=["#"])
                    .set_properties(**{
                        "background-color": "#1e293b",
                        "color": "#f8fafc",
                        "border": "1px solid #334155",
                        "font-size": "12px",
                    })
                    .set_table_styles([{
                        "selector": "thead th",
                        "props": [("background-color", "#0f172a"), ("color", "#94a3b8"),
                                  ("font-size", "11px"), ("border", "1px solid #334155")]
                    }])
                    .hide(axis="index")
                )

                st.dataframe(styled, use_container_width=True, height=185)


# ══════════════════════════════════════════════
# TAB 4 — GRAFO DE CORRELACIONES
# ══════════════════════════════════════════════
with tab4:
    st.markdown('<div class="section-header">🕸️ Red de dependencias estocásticas (Monte Carlo)</div>', unsafe_allow_html=True)
    st.caption("Las aristas representan correlaciones de Pearson entre resultados de partidos. Rojo = correlación positiva · Azul = negativa.")

    mostrar_grafo = st.toggle("Mostrar grafo", value=True)

    col_g1, col_g2, col_g3 = st.columns(3)
    with col_g1:
        umbral = st.slider("Umbral mínimo |correlación|", 0.10, 0.60, 0.30, 0.05)
    with col_g2:
        fase_grafo = st.selectbox("Fase para el grafo", ["Todas"] + fases_disp)
    with col_g3:
        destacar_equipo = st.checkbox("Destacar equipo seleccionado", value=(equipo_sel != "— Todos —"))

    if not mostrar_grafo:
        st.info("Grafo desactivado. Actívalo con el toggle de arriba.")
    else:
        df_mc = df_pri.copy()
        if fase_grafo != "Todas":
            df_mc = df_mc[df_mc["Fase"] == fase_grafo]

        if len(df_mc) == 0:
            st.warning("No hay datos MC para esta fase.")
        else:
            df_mc["Winner_Loc"] = (df_mc["Indicador"] == "GanaLocal").astype(int)
            n_sims = df_mc["simulacion"].nunique()

            if n_sims < 2:
                st.info("Con una sola simulación no se puede calcular correlación de Pearson. Mostrando red de trayectorias compartidas.")
                G = nx.Graph()
                partidos_mc = df_mc[["Partido","Local","Visitante","Fase"]].drop_duplicates()
                for _, row in partidos_mc.iterrows():
                    G.add_node(row["Partido"], local=row["Local"], visitante=row["Visitante"], fase=row["Fase"])
                for i, r1 in partidos_mc.iterrows():
                    for j, r2 in partidos_mc.iterrows():
                        if r1["Partido"] >= r2["Partido"]: continue
                        if {r1["Local"], r1["Visitante"]} & {r2["Local"], r2["Visitante"]}:
                            G.add_edge(r1["Partido"], r2["Partido"])

                fig_g, ax_g = plt.subplots(figsize=(12, 7), facecolor="#0f172a")
                ax_g.set_facecolor("#0f172a")
                node_colors = []
                color_fases = {"Grupos":"#334155","16vos":"#0f766e","8vos":"#0891b2",
                               "4tos":"#7c3aed","semi":"#db2777","3ros":"#d97706","Final":"#dc2626"}
                for n in G.nodes():
                    nd = G.nodes[n]
                    if destacar_equipo and equipo_sel != "— Todos —":
                        if equipo_sel in [nd.get("local",""), nd.get("visitante","")]:
                            node_colors.append("#2dd4bf"); continue
                    node_colors.append(color_fases.get(nd.get("fase",""), "#334155"))

                pos = nx.spring_layout(G, seed=42, k=2)
                nx.draw_networkx_edges(G, pos, ax=ax_g, edge_color="#334155", alpha=0.5, width=0.8)
                nx.draw_networkx_nodes(G, pos, ax=ax_g, node_color=node_colors, node_size=200, alpha=0.9)
                nx.draw_networkx_labels(G, pos, {n: f"P{n}" for n in G.nodes()}, ax=ax_g, font_size=6, font_color="#94a3b8")
                ax_g.axis("off")
                plt.tight_layout()
                st.pyplot(fig_g)
                plt.close()
            else:
                pivot = df_mc.pivot_table(index="simulacion", columns="Partido", values="Winner_Loc", aggfunc="first").fillna(0)
                corr_matrix = pivot.corr()
                G = nx.Graph()
                partidos_ids = corr_matrix.columns.tolist()
                for p in partidos_ids:
                    G.add_node(p)
                for i in range(len(partidos_ids)):
                    for j in range(i+1, len(partidos_ids)):
                        p1, p2 = partidos_ids[i], partidos_ids[j]
                        val = corr_matrix.loc[p1, p2]
                        if not pd.isna(val) and abs(val) > umbral:
                            G.add_edge(p1, p2, weight=val)

                pos = nx.spring_layout(G, seed=42, k=1.5)
                fig_g, ax_g = plt.subplots(figsize=(12, 7), facecolor="#0f172a")
                ax_g.set_facecolor("#0f172a")

                fase_map = {}
                for _, row in df_pri[["Partido","Fase"]].drop_duplicates().iterrows():
                    fase_map[row["Partido"]] = row["Fase"]

                color_fases = {"Grupos":"#334155","16vos":"#0f766e","8vos":"#0891b2",
                               "4tos":"#7c3aed","semi":"#db2777","3ros":"#d97706","Final":"#dc2626"}
                node_colors = []
                for n in G.nodes():
                    if destacar_equipo and equipo_sel != "— Todos —":
                        row_n = df_pri[df_pri["Partido"]==n]
                        if len(row_n) > 0 and equipo_sel in [row_n.iloc[0]["Local"], row_n.iloc[0]["Visitante"]]:
                            node_colors.append("#2dd4bf"); continue
                    node_colors.append(color_fases.get(fase_map.get(n,""), "#334155"))

                edge_vals = [G[u][v]["weight"] for u,v in G.edges()]
                norm = Normalize(vmin=-0.4, vmax=0.4)
                cmap = cm.coolwarm
                edge_colors = [cmap(norm(v)) for v in edge_vals]
                widths = [abs(v)*8 for v in edge_vals]

                nx.draw_networkx_edges(G, pos, ax=ax_g, edge_color=edge_colors, width=widths, alpha=0.7)
                nx.draw_networkx_nodes(G, pos, ax=ax_g, node_color=node_colors, node_size=250, alpha=0.9)
                nx.draw_networkx_labels(G, pos, {n: f"P{n}" for n in G.nodes()}, ax=ax_g, font_size=6, font_color="#f8fafc")

                sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
                sm.set_array([])
                plt.colorbar(sm, ax=ax_g, orientation="horizontal", fraction=0.03, pad=0.04,
                             label="Correlación de Pearson").set_label("Correlación de Pearson", color="#94a3b8")
                ax_g.axis("off")
                patches = [mpatches.Patch(color=c, label=f) for f, c in color_fases.items() if f in fase_map.values()]
                if destacar_equipo and equipo_sel != "— Todos —":
                    patches.append(mpatches.Patch(color="#2dd4bf", label=equipo_sel))
                ax_g.legend(handles=patches, loc="upper left", facecolor="#1e293b", edgecolor="#334155",
                            labelcolor="#f8fafc", fontsize=8)
                plt.tight_layout()
                st.pyplot(fig_g)
                plt.close()
                st.markdown(f"**{G.number_of_edges()} conexiones** con |correlación| > {umbral} · **{G.number_of_nodes()} partidos** en el grafo")


# ══════════════════════════════════════════════
# TAB 5 — CUADRANGULARES (BRACKET)
# ══════════════════════════════════════════════
with tab5:
    st.markdown('<div class="section-header">🏟️ Cuadrangulares — Fase Final</div>', unsafe_allow_html=True)

    col_b1, col_b2 = st.columns([1, 1])
    with col_b1:
        mostrar_colores = st.toggle("Colorear casillas por probabilidad", value=True)
    with col_b2:
        mostrar_grafo_b = st.toggle("Mostrar grafo de trayectorias", value=False)

    fases_bracket = ["16vos", "8vos", "4tos", "semi", "Final"]
    n_sims_b = df_pri["simulacion"].nunique()

    def prob_llegar(df_mc_all, equipo, fase):
        mask_fase = df_mc_all["Fase"] == fase
        mask_eq   = (df_mc_all["Local"] == equipo) | (df_mc_all["Visitante"] == equipo)
        sims_llega = df_mc_all[mask_fase & mask_eq]["simulacion"].nunique()
        total_sims = max(df_mc_all["simulacion"].nunique(), 1)
        return sims_llega / total_sims

    def get_prob_color(p, active=True):
        if not active:
            return "#1e293b", "#f8fafc"
        if p >= 0.80:   return "#064e3b", "#34d399"
        elif p >= 0.60: return "#0f3460", "#60a5fa"
        elif p >= 0.40: return "#3b1f6e", "#a78bfa"
        elif p >= 0.20: return "#451a03", "#fbbf24"
        elif p > 0.0:   return "#3b0e0e", "#f87171"
        else:           return "#0f172a", "#475569"

    def indicador_winner(ind, local, visitante):
        if "Local" in ind or ind == "GanaLocal":
            return local
        return visitante

    ko = df_res[df_res["Fase"] != "Grupos"].copy()
    ko_dict = {}
    for _, r in ko.iterrows():
        pid = int(r["Partido"])
        ko_dict[pid] = {
            "local": r["Local"], "goles_l": int(r["Goles_L"]),
            "visitante": r["Visitante"], "goles_v": int(r["Goles_V"]),
            "ind": r["Indicador"], "fase": r["Fase"],  # <--- Cambiado aquí
            "winner": indicador_winner(r["Indicador"], r["Local"], r["Visitante"])  # <--- Cambiado aquí
        }

    bracket_structure = {
        "left": [
            {"label": "Cuadrante A", "16vos": [74, 77], "8vos": 89, "4tos": 97, "semi": 101},
            {"label": "Cuadrante B", "16vos": [73, 75], "8vos": 90, "4tos": 97, "semi": 101},
            {"label": "Cuadrante C", "16vos": [83, 84], "8vos": 91, "4tos": 98, "semi": 101},
            {"label": "Cuadrante D", "16vos": [81, 82], "8vos": 92, "4tos": 98, "semi": 101},
        ],
        "right": [
            {"label": "Cuadrante E", "16vos": [76, 78], "8vos": 93, "4tos": 99, "semi": 102},
            {"label": "Cuadrante F", "16vos": [80, 79], "8vos": 94, "4tos": 99, "semi": 102},
            {"label": "Cuadrante G", "16vos": [86, 88], "8vos": 95, "4tos": 100, "semi": 102},
            {"label": "Cuadrante H", "16vos": [85, 87], "8vos": 96, "4tos": 100, "semi": 102},
        ]
    }

    def render_match_card(pid, fase_label, use_color, width="100%"):
        if pid not in ko_dict:
            return f'<div style="background:#1e293b;border:1px solid #334155;border-radius:8px;padding:8px;margin:3px 0;min-height:72px;opacity:0.4;"><span style="color:#475569;font-size:11px;">Por definir</span></div>'
        m = ko_dict[pid]
        loc, vis = m["local"], m["visitante"]
        gl, gv = m["goles_l"], m["goles_v"]
        ind = m["ind"]

        if "Local" in ind or ind == "GanaLocal":
            cl, cv = "#34d399", "#64748b"
        else:
            cl, cv = "#64748b", "#34d399"

        penales = "🥅" if "Penales" in ind else ""
        equipo_activo = equipo_sel != "— Todos —"

        if use_color and equipo_activo:
            p_card = prob_llegar(df_pri, equipo_sel, fase_label)
            bg_card, tx_card = get_prob_color(p_card, True)
            bg_loc = bg_vis = bg_card
            tx_loc = tx_card if loc == equipo_sel else "#94a3b8"
            tx_vis = tx_card if vis == equipo_sel else "#94a3b8"
            border_color = tx_card if equipo_sel in [loc, vis] else "#334155"
        elif use_color and not equipo_activo:
            p_loc = prob_llegar(df_pri, loc, fase_label)
            p_vis = prob_llegar(df_pri, vis, fase_label)
            bg_loc, tx_loc = get_prob_color(p_loc, True)
            bg_vis, tx_vis = get_prob_color(p_vis, True)
            border_color = "#334155"
        else:
            bg_loc = bg_vis = "#1e293b"
            tx_loc = tx_vis = "#f8fafc"
            border_color = "#334155"

        return f"""
        <div style="border:1px solid {border_color};border-radius:8px;overflow:hidden;margin:3px 0;font-size:12px;">
            <div style="background:{bg_loc};padding:5px 8px;display:flex;justify-content:space-between;align-items:center;">
                <span style="color:{tx_loc};font-weight:600;">{loc[:16]}</span>
                <span style="color:{cl};font-weight:700;font-size:14px;">{gl} {penales}</span>
            </div>
            <div style="background:{bg_vis};padding:5px 8px;display:flex;justify-content:space-between;align-items:center;">
                <span style="color:{tx_vis};font-weight:600;">{vis[:16]}</span>
                <span style="color:{cv};font-weight:700;font-size:14px;">{gv}</span>
            </div>
            <div style="background:#0f172a;padding:2px 8px;font-size:10px;color:#475569;">P{pid} · {m["fase"]}</div>
        </div>"""

    if mostrar_colores:
        equipo_activo_leg = equipo_sel != "— Todos —"
        leyenda_titulo = (
            f"Probabilidad de <b>{equipo_sel}</b> de llegar a cada fase:"
            if equipo_activo_leg
            else "Probabilidad de cada equipo de llegar a esa fase:"
        )
        st.markdown(f"""
        <div style="margin-bottom:10px;">
            <div style="font-size:12px;color:#94a3b8;margin-bottom:6px;">{leyenda_titulo}</div>
            <div style="display:flex;gap:8px;flex-wrap:wrap;">
                <span style="background:#064e3b;color:#34d399;padding:3px 10px;border-radius:999px;font-size:11px;">≥80%</span>
                <span style="background:#0f3460;color:#60a5fa;padding:3px 10px;border-radius:999px;font-size:11px;">60–80%</span>
                <span style="background:#3b1f6e;color:#a78bfa;padding:3px 10px;border-radius:999px;font-size:11px;">40–60%</span>
                <span style="background:#451a03;color:#fbbf24;padding:3px 10px;border-radius:999px;font-size:11px;">20–40%</span>
                <span style="background:#3b0e0e;color:#f87171;padding:3px 10px;border-radius:999px;font-size:11px;">&lt;20%</span>
                <span style="background:#0f172a;color:#475569;padding:3px 10px;border-radius:999px;font-size:11px;border:1px solid #334155;">No llegó / 0%</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    col_left, col_center, col_right = st.columns([5, 2, 5])

    with col_left:
        st.markdown("**← Cuadrantes A·B·C·D**")
        for cuad in bracket_structure["left"]:
            st.markdown(f'<div style="font-size:11px;color:#0f766e;font-weight:700;margin:6px 0 2px 0;">▶ {cuad["label"]}</div>', unsafe_allow_html=True)
            sub_cols = st.columns([3, 3, 3, 3])
            with sub_cols[0]:
                for pid in cuad["16vos"]:
                    st.markdown(render_match_card(pid, "16vos", mostrar_colores), unsafe_allow_html=True)
            with sub_cols[1]:
                st.markdown("<div style='margin-top:36px'>", unsafe_allow_html=True)
                st.markdown(render_match_card(cuad["8vos"], "8vos", mostrar_colores), unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            with sub_cols[2]:
                if cuad["label"] in ["Cuadrante A", "Cuadrante C"]:
                    st.markdown("<div style='margin-top:72px'>", unsafe_allow_html=True)
                    st.markdown(render_match_card(cuad["4tos"], "4tos", mostrar_colores), unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
            with sub_cols[3]:
                if cuad["label"] == "Cuadrante A":
                    st.markdown("<div style='margin-top:144px'>", unsafe_allow_html=True)
                    st.markdown(render_match_card(cuad["semi"], "semi", mostrar_colores), unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

    with col_center:
        st.markdown("<div style='height:60px'></div>", unsafe_allow_html=True)
        st.markdown('<div style="text-align:center;color:#fbbf24;font-weight:700;font-size:13px;margin-bottom:6px;">🥇 FINAL</div>', unsafe_allow_html=True)
        st.markdown(render_match_card(104, "Final", mostrar_colores), unsafe_allow_html=True)
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        st.markdown('<div style="text-align:center;color:#94a3b8;font-weight:700;font-size:12px;margin-bottom:6px;">🥉 3er Puesto</div>', unsafe_allow_html=True)
        st.markdown(render_match_card(103, "3ros", mostrar_colores), unsafe_allow_html=True)

    with col_right:
        st.markdown("**Cuadrantes E·F·G·H →**", unsafe_allow_False)
        for cuad in bracket_structure["right"]:
            st.markdown(f'<div style="font-size:11px;color:#0f766e;font-weight:700;margin:6px 0 2px 0;">◀ {cuad["label"]}</div>', unsafe_allow_html=True)
            sub_cols = st.columns([3, 3, 3, 3])
            with sub_cols[3]:
                for pid in cuad["16vos"]:
                    st.markdown(render_match_card(pid, "16vos", mostrar_colores), unsafe_allow_html=True)
            with sub_cols[2]:
                st.markdown("<div style='margin-top:36px'>", unsafe_allow_html=True)
                st.markdown(render_match_card(cuad["8vos"], "8vos", mostrar_colores), unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            with sub_cols[1]:
                if cuad["label"] in ["Cuadrante E", "Cuadrante G"]:
                    st.markdown("<div style='margin-top:72px'>", unsafe_allow_html=True)
                    st.markdown(render_match_card(cuad["4tos"], "4tos", mostrar_colores), unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
            with sub_cols[0]:
                if cuad["label"] == "Cuadrante E":
                    st.markdown("<div style='margin-top:144px'>", unsafe_allow_html=True)
                    st.markdown(render_match_card(cuad["semi"], "semi", mostrar_colores), unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

    if mostrar_grafo_b:
        st.divider()
        st.markdown('<div class="section-header">🕸️ Grafo de trayectorias — Fase Final</div>', unsafe_allow_html=True)

        G_b = nx.DiGraph()
        for pid, m in ko_dict.items():
            G_b.add_node(pid, label=f"P{pid}\n{m['winner'][:8]}", fase=m["fase"],
                         winner=m["winner"])

        avance = {
            73: 90, 74: 89, 75: 90, 76: 93, 77: 89, 78: 93,
            79: 94, 80: 94, 81: 92, 82: 92, 83: 91, 84: 91,
            85: 96, 86: 95, 87: 96, 88: 95,
            89: 97, 90: 97, 91: 98, 92: 98,
            93: 99, 94: 99, 95: 100, 96: 100,
            97: 101, 98: 101, 99: 102, 100: 102,
            101: 104, 102: 104,
        }
        for src, dst in avance.items():
            if src in G_b and dst in G_b:
                G_b.add_edge(src, dst)

        color_fases_b = {"16vos": "#0f766e", "8vos": "#0891b2",
                         "4tos": "#7c3aed", "semi": "#db2777",
                         "3ros": "#d97706", "Final": "#dc2626"}

        def node_color_b(pid):
            m = ko_dict.get(pid, {})
            if equipo_sel != "— Todos —" and equipo_sel in [m.get("local",""), m.get("visitante",""), m.get("winner","")]:
                return "#2dd4bf"
            return color_fases_b.get(m.get("fase",""), "#334155")

        node_colors_b = [node_color_b(n) for n in G_b.nodes()]
        labels_b = {n: G_b.nodes[n].get("label", f"P{n}") for n in G_b.nodes()}

        pos_b = nx.spring_layout(G_b, seed=7, k=2.5)
        fig_b, ax_b = plt.subplots(figsize=(13, 6), facecolor="#0f172a")
        ax_b.set_facecolor("#0f172a")
        nx.draw_networkx_edges(G_b, pos_b, ax=ax_b, edge_color="#475569",
                               arrows=True, arrowsize=15, width=1.5, alpha=0.8,
                               connectionstyle="arc3,rad=0.1")
        nx.draw_networkx_nodes(G_b, pos_b, ax=ax_b, node_color=node_colors_b,
                               node_size=400, alpha=0.95)
        nx.draw_networkx_labels(G_b, pos_b, labels_b, ax=ax_b,
                                font_size=5.5, font_color="#f8fafc")
        patches_b = [mpatches.Patch(color=c, label=f) for f, c in color_fases_b.items()]
        if equipo_sel != "— Todos —":
            patches_b.append(mpatches.Patch(color="#2dd4bf", label=equipo_sel))
        ax_b.legend(handles=patches_b, loc="upper left", facecolor="#1e293b",
                    edgecolor="#334155", labelcolor="#f8fafc", fontsize=8)
        ax_b.axis("off")
        plt.tight_layout()
        st.pyplot(fig_b)
        plt.close()


# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.divider()
st.markdown(
    "<div style='text-align:center;color:#334155;font-size:12px;'>Mundial 2026 · Modelo Dixon-Coles · Monte Carlo · Simulación estocástica</div>",
    unsafe_allow_html=True
)
