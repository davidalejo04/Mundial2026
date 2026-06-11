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
    # Rutas — ajusta según donde estén los archivos en producción / Fabric
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

    # Mapa equipo → grupo
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
    """Retorna HTML badge con el resultado del equipo seleccionado."""
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
    """
    Calcula la esperanza de triunfo del equipo usando todas las simulaciones MC.
    Si rival se especifica, filtra solo partidos contra ese rival.
    """
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
tab1, tab2, tab3, tab4 = st.tabs(["📋 Partidos", "🏆 Rivales & Esperanzas", "📊 Tabla de Grupos", "🕸️ Grafo de Correlaciones"])


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

                # Calcular esperanza contra este rival en esta fase
                pw, pd_, pl = calc_esperanza(df_pri, equipo_sel, rival=rival, fase=m["Fase"])
                
                goles_eq   = int(m["Goles_L"]) if es_local else int(m["Goles_V"])
                goles_rival= int(m["Goles_V"]) if es_local else int(m["Goles_L"])

                # Determinar resultado del equipo
                if m["Indicador"] == "Empate":
                    res_label = "Empate"; res_color = "#fbbf24"
                elif (m["Indicador"] == "GanaLocal" and es_local) or (m["Indicador"] == "GanaVisitante" and not es_local):
                    res_label = "Victoria"; res_color = "#34d399"
                else:
                    res_label = "Derrota"; res_color = "#f87171"

                cond_str = f"{'Local' if es_local else 'Visitante'} · {m['Fase']} · P{int(m['Partido'])}"
                
                # Barra de probabilidad
                pw_pct = f"{pw:.0%}" if pw is not None else "N/A"
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

        # Estadísticas consolidadas del equipo
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

    # Calcular standings
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
    
    # Filtro de grupo
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
            
            tabla_html = f"""
            <div style="background:#1e293b;border:1px solid #334155;border-radius:10px;padding:0;overflow:hidden;margin-bottom:12px;">
                <div style="background:#0f766e;padding:10px 14px;font-weight:700;color:#f8fafc;font-size:14px;">GRUPO {letra}</div>
                <div style="padding:8px 14px;">
                    <div style="display:grid;grid-template-columns:20px 1fr 30px 30px 36px;gap:4px;font-size:11px;color:#64748b;padding:4px 0;border-bottom:1px solid #334155;">
                        <span>#</span><span>Equipo</span><span style="text-align:center">GF</span><span style="text-align:center">DG</span><span style="text-align:center;color:#2dd4bf">PTS</span>
                    </div>
            """
            for i, eq in enumerate(equipos):
                dg = eq["gf"] - eq["gc"]
                dg_str = f"+{dg}" if dg > 0 else str(dg)
                pos_colors = ["#34d399","#34d399","#fbbf24","#f87171"]
                pos_color = pos_colors[min(i, 3)]
                hl = "background:#0f172a;" if i % 2 == 0 else ""
                bold = "font-weight:700;" if equipo_sel != "— Todos —" and eq["team"] == equipo_sel else ""
                tabla_html += f"""
                    <div style="display:grid;grid-template-columns:20px 1fr 30px 30px 36px;gap:4px;padding:6px 0;{hl}">
                        <span style="color:{pos_color};font-weight:700;font-size:12px;">{i+1}</span>
                        <span style="color:#f8fafc;font-size:12px;{bold}">{eq["team"][:14]}</span>
                        <span style="text-align:center;color:#94a3b8;font-size:12px">{eq["gf"]}</span>
                        <span style="text-align:center;color:#94a3b8;font-size:12px">{dg_str}</span>
                        <span style="text-align:center;color:#2dd4bf;font-weight:700;font-size:13px">{eq["pts"]}</span>
                    </div>
                """
            tabla_html += "</div></div>"
            with cols[ci]:
                st.markdown(tabla_html, unsafe_allow_html=True)


# ══════════════════════════════════════════════
# TAB 4 — GRAFO DE CORRELACIONES
# ══════════════════════════════════════════════
with tab4:
    st.markdown('<div class="section-header">🕸️ Red de dependencias estocásticas (Monte Carlo)</div>', unsafe_allow_html=True)
    st.caption("Las aristas representan correlaciones de Pearson entre resultados de partidos. Rojo = correlación positiva · Azul = negativa.")

    col_g1, col_g2, col_g3 = st.columns(3)
    with col_g1:
        umbral = st.slider("Umbral mínimo |correlación|", 0.10, 0.60, 0.30, 0.05)
    with col_g2:
        fase_grafo = st.selectbox("Fase para el grafo", ["Todas"] + fases_disp)
    with col_g3:
        destacar_equipo = st.checkbox("Destacar equipo seleccionado", value=(equipo_sel != "— Todos —"))

    # Construir matriz de correlación desde PRIDEF3
    df_mc = df_pri.copy()
    if fase_grafo != "Todas":
        df_mc = df_mc[df_mc["Fase"] == fase_grafo]

    if len(df_mc) == 0:
        st.warning("No hay datos MC para esta fase.")
    else:
        df_mc["Winner_Loc"] = (df_mc["Indicador"] == "GanaLocal").astype(int)

        # Si solo hay una simulación, generamos correlaciones por partido/equipo
        n_sims = df_mc["simulacion"].nunique()

        if n_sims < 2:
            st.info("Con una sola simulación no se puede calcular correlación de Pearson entre partidos. Mostrando red de partidos del equipo seleccionado.")
            
            # Mostrar grafo simple de partidos del torneo
            G = nx.Graph()
            partidos_mc = df_mc[["Partido","Local","Visitante","Fase"]].drop_duplicates()
            
            for _, row in partidos_mc.iterrows():
                G.add_node(row["Partido"], local=row["Local"], visitante=row["Visitante"], fase=row["Fase"])

            # Conectar partidos que comparten equipo (trayectoria)
            for i, r1 in partidos_mc.iterrows():
                for j, r2 in partidos_mc.iterrows():
                    if r1["Partido"] >= r2["Partido"]: continue
                    equipos1 = {r1["Local"], r1["Visitante"]}
                    equipos2 = {r2["Local"], r2["Visitante"]}
                    if equipos1 & equipos2:
                        G.add_edge(r1["Partido"], r2["Partido"])

            fig_g, ax_g = plt.subplots(figsize=(12, 7), facecolor="#0f172a")
            ax_g.set_facecolor("#0f172a")

            node_colors = []
            for n in G.nodes():
                nd = G.nodes[n]
                if destacar_equipo and equipo_sel != "— Todos —":
                    if equipo_sel in [nd.get("local",""), nd.get("visitante","")]:
                        node_colors.append("#2dd4bf")
                    else:
                        node_colors.append("#334155")
                else:
                    fase_n = nd.get("fase","")
                    color_map = {"Grupos":"#334155","16vos":"#0f766e","8vos":"#0891b2",
                                 "4tos":"#7c3aed","semi":"#db2777","3ros":"#d97706","Final":"#dc2626"}
                    node_colors.append(color_map.get(fase_n, "#334155"))

            pos = nx.spring_layout(G, seed=42, k=2)
            nx.draw_networkx_edges(G, pos, ax=ax_g, edge_color="#334155", alpha=0.5, width=0.8)
            nx.draw_networkx_nodes(G, pos, ax=ax_g, node_color=node_colors, node_size=200, alpha=0.9)
            
            labels = {n: f"P{n}" for n in G.nodes()}
            nx.draw_networkx_labels(G, pos, labels=labels, ax=ax_g, font_size=6, font_color="#94a3b8")
            
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

            # Layout
            pos = nx.spring_layout(G, seed=42, k=1.5)

            fig_g, ax_g = plt.subplots(figsize=(12, 7), facecolor="#0f172a")
            ax_g.set_facecolor("#0f172a")

            # Color nodos por fase
            fase_map = {}
            for _, row in df_pri[["Partido","Fase"]].drop_duplicates().iterrows():
                fase_map[row["Partido"]] = row["Fase"]

            color_fases = {"Grupos":"#334155","16vos":"#0f766e","8vos":"#0891b2",
                           "4tos":"#7c3aed","semi":"#db2777","3ros":"#d97706","Final":"#dc2626"}
            node_colors = []
            for n in G.nodes():
                if destacar_equipo and equipo_sel != "— Todos —":
                    row_n = df_pri[df_pri["Partido"]==n].iloc[0] if len(df_pri[df_pri["Partido"]==n])>0 else None
                    if row_n is not None and equipo_sel in [row_n["Local"], row_n["Visitante"]]:
                        node_colors.append("#2dd4bf")
                        continue
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

            # Leyenda de fases
            patches = [mpatches.Patch(color=c, label=f) for f, c in color_fases.items() if f in fase_map.values()]
            if destacar_equipo and equipo_sel != "— Todos —":
                patches.append(mpatches.Patch(color="#2dd4bf", label=equipo_sel))
            ax_g.legend(handles=patches, loc="upper left", facecolor="#1e293b", edgecolor="#334155",
                        labelcolor="#f8fafc", fontsize=8)

            plt.tight_layout()
            st.pyplot(fig_g)
            plt.close()

            st.markdown(f"**{G.number_of_edges()} conexiones** con |correlación| > {umbral} · **{G.number_of_nodes()} partidos** en el grafo")


# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.divider()
st.markdown(
    "<div style='text-align:center;color:#334155;font-size:12px;'>Mundial 2026 · Modelo Dixon-Coles · Monte Carlo · Simulación estocástica</div>",
    unsafe_allow_html=True
)
