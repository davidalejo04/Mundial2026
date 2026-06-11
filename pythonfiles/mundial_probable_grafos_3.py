import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
from PIL import Image, ImageDraw, ImageFont

# 1. CARGAR DATOS
pride_path = "C:/Users/david/2026/v2/PRIDEF3.xlsx"
resdef_path = "C:/Users/david/2026/v2/RESDEF3.xlsx"
estudio_path = "C:/Users/david/2026/v2/EstudioEstadisticoMundial.xlsx"

if not os.path.exists(pride_path) or not os.path.exists(resdef_path) or not os.path.exists(estudio_path):
    raise FileNotFoundError(
        f"Asegúrate de tener los archivos necesarios en el directorio:\n"
        f"- {pride_path}\n- {resdef_path}\n- {estudio_path}"
    )

print("Cargando base de datos de selecciones y grupos...")
df_teams = pd.read_excel(estudio_path)
df_teams.columns = [c.strip() for c in df_teams.columns]

# Crear un diccionario para buscar el grupo de cada selección rápidamente
team_to_group = dict(zip(df_teams['Selección'].str.strip(), df_teams['Grupo'].str.strip()))

print("Analizando acervo Montecarlo (PRIDEF3) y cargando simulación probable (RESDEF3)...")
df_pride = pd.read_excel(pride_path)
df_res = pd.read_excel(resdef_path)

df_pride.columns = [c.strip() for c in df_pride.columns]
df_res.columns = [c.strip() for c in df_res.columns]

# --- PROCESAMIENTO RESDEF3 (Diseño Base y Marcadores) ---
df_res['Partido'] = df_res['Partido'].astype(int)
df_res['Goles_L'] = df_res['Goles_L'].fillna(0).astype(int)
df_res['Goles_V'] = df_res['Goles_V'].fillna(0).astype(int)
df_res['Lugar'] = df_res['Lugar'].fillna('Desconocido')
df_res_clean = df_res.drop_duplicates(subset=['Partido'], keep='first')

matches_db = {}
for _, row in df_res_clean.iterrows():
    fase = str(row['Fase']).strip()
    matches_db[row['Partido']] = {
        'local': str(row['Local']).strip(),
        'goles_l': int(row['Goles_L']),
        'visitante': str(row['Visitante']).strip(),
        'goles_v': int(row['Goles_V']),
        'lugar': str(row['Lugar']).strip()[:15],
        'fase': fase,
        'marcador': f"{row['Goles_L']} - {row['Goles_V']}" if fase == 'Grupos' else None
    }

# --- CLASIFICACIÓN DINÁMICA DE PARTIDOS POR GRUPO ---
letras_grupos = "ABCDEFGHIJKL"
group_matches = {letra: [] for letra in letras_grupos}
unassigned_matches = []

# Clasificamos solo los partidos correspondientes a la fase de grupos (1 al 72)
for p_id in range(1, 73):
    if p_id in matches_db:
        m = matches_db[p_id]
        # Buscamos el grupo usando el equipo local o el visitante como respaldo
        grupo = team_to_group.get(m['local']) or team_to_group.get(m['visitante'])
        
        if grupo in group_matches:
            group_matches[grupo].append(p_id)
        else:
            unassigned_matches.append(p_id)
    else:
        unassigned_matches.append(p_id)

# Ordenamos cronológicamente los partidos asignados a cada grupo
for letra in group_matches:
    group_matches[letra].sort()

# Safe-check / Fallback: Si un partido no se pudo mapear por strings, lo ubica en el primer espacio libre
for p_id in unassigned_matches:
    for letra in letras_grupos:
        if len(group_matches[letra]) < 6:
            group_matches[letra].append(p_id)
            break

# --- PROCESAMIENTO PRIDEF3 (Correlaciones) ---
df_full = df_pride.copy()
df_full['Winner_Loc'] = (df_full['Indicador'].str.strip() == 'GanaLocal').astype(int)
pivot_sim = df_full.pivot(index='simulacion', columns='Partido', values='Winner_Loc').fillna(0)
matrix_correlacion_total = pivot_sim.corr()


# 2. CONFIGURACIÓN DEL LIENZO GRÁFICO (PILLOW)
WIDTH, HEIGHT = 3800, 3200 
BG_COLOR = (15, 23, 42)      
BOX_BG = (30, 41, 59)        
BOX_BORDER = (71, 85, 105)   
TEXT_COLOR = (248, 250, 252) 
SCORE_WIN = (52, 211, 153)   
SCORE_LOSE = (148, 163, 184)
GROUP_SCORE_HL = (251, 191, 36) 
LINE_COLOR_STRUCT = (51, 65, 85) 

try:
    font_path = "arial.ttf"
    font_title = ImageFont.truetype(font_path, 70)
    font_phase_title = ImageFont.truetype(font_path, 45)
    font_group_name = ImageFont.truetype(font_path, 30)
    font_main = ImageFont.truetype(font_path, 22)
    font_score = ImageFont.truetype(font_path, 28)
    font_gscore_hl = ImageFont.truetype(font_path, 24)
    font_info = ImageFont.truetype(font_path, 16)
except IOError:
    font_title = font_phase_title = font_group_name = font_main = font_score = font_gscore_hl = font_info = ImageFont.load_default()

img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
draw = ImageDraw.Draw(img)
draw.text((WIDTH // 2, 80), "MUNDIAL 2026: DIAGRAMA DE INTERACCIONES TOTALES (MONTECARLO)", fill=TEXT_COLOR, font=font_title, anchor="mm")


# 3. MAQUETACIÓN VISUAL DE LA FASE DE GRUPOS DINÁMICA
print("Maquetando Fase de Grupos corregida y dibujando marcadores...")
Y_GRUPOS_START = 180
draw.text((WIDTH // 2, Y_GRUPOS_START + 25), "FASE DE GRUPOS - MARCADORES PROBABLES (ORGANIZADOS POR GRUPO REAL)", fill=TEXT_COLOR, font=font_phase_title, anchor="mm")

BOX_W_G, BOX_H_G = 280, 80
GAP_X_G, GAP_Y_G = 30, 20
MARGIN_X_G = 100

match_positions_groups = {}

for g_idx, letra in enumerate(letras_grupos):
    group_name = f"GRUPO {letra}"
    x_col = MARGIN_X_G + (g_idx * (BOX_W_G + GAP_X_G))
    draw.text((x_col + BOX_W_G // 2, Y_GRUPOS_START + 80), group_name, fill=TEXT_COLOR, font=font_group_name, anchor="mm")
    
    # IMPORTANTE: Tomamos los partidos reales pertenecientes a este grupo específico
    partidos_este_grupo = group_matches[letra]
    
    for row_idx, p_id in enumerate(partidos_este_grupo):
        y_row = Y_GRUPOS_START + 120 + (row_idx * (BOX_H_G + GAP_Y_G))
        match_positions_groups[p_id] = (x_col, y_row)
        
        draw.rounded_rectangle([x_col, y_row, x_col + BOX_W_G, y_row + BOX_H_G], radius=8, fill=BOX_BG, outline=BOX_BORDER, width=1)
        if p_id in matches_db:
            m = matches_db[p_id]
            draw.text((x_col + 15, y_row + 20), m['local'][:16], fill=TEXT_COLOR, font=font_main, anchor="lm")
            draw.text((x_col + 15, y_row + 46), m['visitante'][:16], fill=TEXT_COLOR, font=font_main, anchor="lm")
            if m['marcador']:
                draw.text((x_col + BOX_W_G - 15, y_row + 33), m['marcador'], fill=GROUP_SCORE_HL, font=font_gscore_hl, anchor="rm")
            draw.text((x_col + 15, y_row + 70), f"P{p_id} - {m['lugar']}", fill=(148, 163, 184), font=font_info, anchor="lm")
        else:
            draw.text((x_col + BOX_W_G // 2, y_row + BOX_H_G // 2), f"P{p_id} - Grupos", fill=(148, 163, 184), font=font_main, anchor="mm")

Y_GRUPOS_END = Y_GRUPOS_START + 120 + (6 * (BOX_H_G + GAP_Y_G)) + 50


# 4. MAQUETACIÓN VISUAL DE LOS CUADRANGULARES (Partidos 73-104)
print("Maquetando Cuadrangulares (Bracket Base)...")
Y_BRACKET_START = Y_GRUPOS_END + 100
draw.text((WIDTH // 2, Y_BRACKET_START + 25), "CUADRANGULARES - FASE FINAL", fill=TEXT_COLOR, font=font_phase_title, anchor="mm")

BOX_W_F, BOX_H_F = 320, 90
Y_F_OFFSET = Y_BRACKET_START + 120

match_positions_final = {
    74: (80, 150 + Y_F_OFFSET),   77: (80, 275 + Y_F_OFFSET),
    73: (80, 400 + Y_F_OFFSET),   75: (80, 525 + Y_F_OFFSET),
    83: (80, 650 + Y_F_OFFSET),   84: (80, 775 + Y_F_OFFSET),
    81: (80, 900 + Y_F_OFFSET),   82: (80, 1025 + Y_F_OFFSET),
    89: (460, 212 + Y_F_OFFSET),  90: (460, 462 + Y_F_OFFSET),
    91: (460, 712 + Y_F_OFFSET),  92: (460, 962 + Y_F_OFFSET),
    97: (840, 337 + Y_F_OFFSET),  98: (840, 837 + Y_F_OFFSET),
    101: (1220, 587 + Y_F_OFFSET),
    104: (1620, 480 + Y_F_OFFSET), 103: (1620, 720 + Y_F_OFFSET),
    102: (2020, 587 + Y_F_OFFSET),
    99: (2400, 337 + Y_F_OFFSET),  100: (2400, 837 + Y_F_OFFSET),
    93: (2780, 212 + Y_F_OFFSET),  94: (2780, 462 + Y_F_OFFSET),
    95: (2780, 712 + Y_F_OFFSET),  96: (2780, 962 + Y_F_OFFSET),
    76: (3160, 150 + Y_F_OFFSET),  78: (3160, 275 + Y_F_OFFSET),
    79: (3160, 400 + Y_F_OFFSET),  80: (3160, 525 + Y_F_OFFSET),
    86: (3160, 650 + Y_F_OFFSET),  88: (3160, 775 + Y_F_OFFSET),
    85: (3160, 900 + Y_F_OFFSET),  87: (3160, 1025 + Y_F_OFFSET)
}

bracket_connections = [
    ((74, 77), 89, 'left'),   ((73, 75), 90, 'left'),   ((83, 84), 91, 'left'),   ((81, 82), 92, 'left'),
    ((89, 90), 97, 'left'),   ((91, 92), 98, 'left'),   ((97, 98), 101, 'left'),
    ((76, 78), 93, 'right'),  ((79, 80), 94, 'right'),  ((86, 88), 95, 'right'),  ((85, 87), 96, 'right'),
    ((93, 94), 99, 'right'),  ((95, 96), 100, 'right'), ((99, 100), 102, 'right')
]

def draw_match_card_final(draw, p_id):
    if p_id not in matches_db: return
    x, y = match_positions_final[p_id]
    m = matches_db[p_id]
    draw.rounded_rectangle([x, y, x + BOX_W_F, y + BOX_H_F], radius=8, fill=BOX_BG, outline=BOX_BORDER, width=1)
    draw.line([(x + 230, y + 8), (x + 230, y + BOX_H_F - 8)], fill=(71, 85, 105), width=1)
    draw.text((x + 115, y + 74), f"P{p_id} - {m['lugar']}", fill=(148, 163, 184), font=font_info, anchor="mm")
    
    c_l, c_v = SCORE_LOSE, SCORE_LOSE
    if m['goles_l'] > m['goles_v']: c_l = SCORE_WIN
    elif m['goles_v'] > m['goles_l']: c_v = SCORE_WIN
    
    draw.text((x + 20, y + 24), m['local'][:16], fill=TEXT_COLOR, font=font_main, anchor="lm")
    draw.text((x + 20, y + 50), m['visitante'][:16], fill=TEXT_COLOR, font=font_main, anchor="lm")
    draw.text((x + 275, y + 24), str(m['goles_l']), fill=c_l, font=font_score, anchor="mm")
    draw.text((x + 275, y + 50), str(m['goles_v']), fill=c_v, font=font_score, anchor="mm")

def draw_bracket_lines(draw):
    for (p1, p2), p_next, side in bracket_connections:
        pos1, pos2, pos_next = match_positions_final[p1], match_positions_final[p2], match_positions_final[p_next]
        if side == 'left':
            start1 = (pos1[0] + BOX_W_F, pos1[1] + BOX_H_F//2)
            start2 = (pos2[0] + BOX_W_F, pos2[1] + BOX_H_F//2)
            end = (pos_next[0], pos_next[1] + BOX_H_F//2)
            mid_x = start1[0] + (end[0] - start1[0]) // 2
        else:
            start1 = (pos1[0], pos1[1] + BOX_H_F//2)
            start2 = (pos2[0], pos2[1] + BOX_H_F//2)
            end = (pos_next[0] + BOX_W_F, pos_next[1] + BOX_H_F//2)
            mid_x = start1[0] - (start1[0] - end[0]) // 2
        draw.line([start1, (mid_x, start1[1]), (mid_x, end[1]), end], fill=LINE_COLOR_STRUCT, width=1)
        draw.line([start2, (mid_x, start2[1]), (mid_x, end[1]), end], fill=LINE_COLOR_STRUCT, width=1)

draw_bracket_lines(draw)
for p_id in match_positions_final.keys(): draw_match_card_final(draw, p_id)


# 5. INTEGRACIÓN DEL GRAFO NETWORKX (CAPA DE INTERACCIONES CORREGIDA)
# Al corregir match_positions_groups, el grafo hereda de forma automática las coordenadas reales corregidas.
all_match_positions = {**match_positions_groups, **match_positions_final}
pos_grafo_maestra = {}
for p_id, (x, y) in all_match_positions.items():
    w_box = BOX_W_G if p_id <= 72 else BOX_W_F
    h_box = BOX_H_G if p_id <= 72 else BOX_H_F
    pos_grafo_maestra[p_id] = (x + w_box // 2, y + h_box // 2)

print("Generando capa de grafos sobre el lienzo total...")

dpi = 100
figsize = (WIDTH / dpi, HEIGHT / dpi)
fig = plt.figure(num="Interacciones Totales del Mundial - Montecarlo", figsize=figsize, dpi=dpi)

ax = fig.add_axes([0, 0, 1, 1])
ax.imshow(img) 

G = nx.Graph()
for p_id in pos_grafo_maestra.keys(): G.add_node(p_id)

UMBRAL_CORRELACION_F = 0.30
edges = []
weights = []
edge_colors = []

partidos_corel = matrix_correlacion_total.columns

for i in range(len(partidos_corel)):
    for j in range(i + 1, len(partidos_corel)):
        p1 = partidos_corel[i]
        p2 = partidos_corel[j]
        
        if p1 in pos_grafo_maestra and p2 in pos_grafo_maestra:
            val_corr = matrix_correlacion_total.loc[p1, p2]
            if abs(val_corr) > UMBRAL_CORRELACION_F and not pd.isna(val_corr):
                es_cruce_grupos_final = (p1 <= 72 and p2 > 72) or (p1 > 72 and p2 <= 72)
                rad_val = "0.2" if es_cruce_grupos_final else "0.1" 
                
                G.add_edge(p1, p2, weight=val_corr, rad=rad_val)
                edges.append((p1, p2))
                weights.append(abs(val_corr) * 20) 
                edge_colors.append(val_corr)

# Dibujar nodos
nx.draw_networkx_nodes(
    G, pos_grafo_maestra, 
    node_size=150, 
    node_color='#a5b4fc', 
    alpha=0.25,
    ax=ax
)

sm = plt.cm.ScalarMappable(cmap=plt.cm.coolwarm, norm=plt.Normalize(vmin=-0.4, vmax=0.4))
sm.set_array([])

# Dibujar aristas con curvatura
for (u, v, d) in G.edges(data=True):
    val_corr_e = d['weight']
    nx.draw_networkx_edges(
        G, pos_grafo_maestra,
        edgelist=[(u,v)],
        width=abs(val_corr_e) * 20, 
        edge_color=[val_corr_e], 
        edge_cmap=plt.cm.coolwarm,
        edge_vmin=-0.4, edge_vmax=0.4,
        alpha=0.7,
        connectionstyle=f"arc3,rad={d['rad']}",
        ax=ax
    )

# Títulos de red centrados
ax.text(WIDTH // 2, Y_GRUPOS_START + 62, "CAPA DE RED: CONEXIONES ESTOCÁSTICAS EN GRUPOS CORREGIDOS", 
        fontsize=20, color='#a5b4fc', fontweight='bold', ha='center', va='center', alpha=0.8)

ax.text(WIDTH // 2, Y_BRACKET_START + 62, "CAPA DE RED: EFECTOS MARIPOSA Y DEPENDENCIAS EN FASE FINAL", 
        fontsize=20, color='#a5b4fc', fontweight='bold', ha='center', va='center', alpha=0.8)

# Colorbar inferior flotante
cax = fig.add_axes([0.35, 0.015, 0.30, 0.012])
cbar = fig.colorbar(sm, cax=cax, orientation='horizontal')
cbar.set_label('Índice de Dependencia Estocástica (Correlación Pearson en Montecarlo)', color='white', fontsize=14, labelpad=10)
cbar.ax.xaxis.set_tick_params(color='white', labelcolor='white', labelsize=12)

ax.axis('off')

print(f"\n¡Ajustes listos! Estructura de grupos corregida por mapeo de confederación real.")
print(f"Dimensiones de lienzo: {WIDTH}x{HEIGHT}. Abriendo visor interactivo...")
plt.show()


## GRAFICAR RESULTADO FASE GRUPOS

import os
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt 

# 1. CARGAR Y PROCESAR DATOS
resdef_path = resdef_path
estudio_path = "C:/Users/david/2026/v2/EstudioEstadisticoMundial.xlsx"

if not os.path.exists(resdef_path) or not os.path.exists(estudio_path):
    raise FileNotFoundError("Verifica los archivos CSV de origen.")

df_res = pd.read_excel(resdef_path)
df_est = pd.read_excel(estudio_path)
df_est=df_est[df_est['Escogido'] == 'Y']

df_est.columns = [c.strip() for c in df_est.columns]
df_res.columns = [c.strip() for c in df_res.columns]

team_to_group = {str(r['Selección']).strip(): str(r['Grupo']).strip() for _, r in df_est.iterrows()}
standings = {team: {'name': team, 'grupo': g, 'pj': 0, 'gf': 0, 'gc': 0, 'dg': 0, 'pts': 0} for team, g in team_to_group.items()}

for _, row in df_res[df_res['Fase'].str.strip() == 'Grupos'].iterrows():
    loc, vis = str(row['Local']).strip(), str(row['Visitante']).strip()
    gl, gv = int(row['Goles_L']), int(row['Goles_V'])
    if loc in standings and vis in standings:
        standings[loc]['pj'] += 1; standings[vis]['pj'] += 1
        standings[loc]['gf'] += gl; standings[loc]['gc'] += gv
        standings[vis]['gf'] += gv; standings[vis]['gc'] += gl
        if gl > gv: standings[loc]['pts'] += 3
        elif gv > gl: standings[vis]['pts'] += 3
        else: standings[loc]['pts'] += 1; standings[vis]['pts'] += 1

for t in standings: standings[t]['dg'] = standings[t]['gf'] - standings[t]['gc']

letras_grupos = sorted(list(set(team_to_group.values())))
grupos_consolidados = {}
for letra in letras_grupos:
    equipos = [s for s in standings.values() if s['grupo'] == letra]
    equipos.sort(key=lambda x: (x['pts'], x['dg'], x['gf']), reverse=True)
    grupos_consolidados[f"GRUPO {letra}"] = equipos

# 2. CONFIGURACIÓN VISUAL
WIDTH, HEIGHT = 2600, 1600
BG_COLOR, TABLE_BG, HEADER_BG = (15, 23, 42), (30, 41, 59), (15, 118, 110)
BORDER_COLOR, TEXT_COLOR, ACCENT_PTS = (71, 85, 105), (248, 250, 252), (45, 212, 191)
TABLE_WIDTH, TABLE_HEIGHT = 580, 380

try:
    font_path = "arial.ttf"
    font_main_title = ImageFont.truetype(font_path, 65)
    font_group_title = ImageFont.truetype(font_path, 32)
    font_header = ImageFont.truetype(font_path, 18)
    font_table_p = ImageFont.truetype(font_path, 20)
    font_table_bold = ImageFont.truetype(font_path, 22)
except IOError:
    font_main_title = font_group_title = font_header = font_table_p = font_table_bold = ImageFont.load_default()

def draw_group_table(draw, x, y, group_name, teams):
    draw.rounded_rectangle([x, y, x + TABLE_WIDTH, y + TABLE_HEIGHT], radius=12, fill=TABLE_BG, outline=BORDER_COLOR, width=1)
    draw.rounded_rectangle([x, y, x + TABLE_WIDTH, y + 60], radius=12, fill=HEADER_BG)
    draw.rectangle([x, y + 30, x + TABLE_WIDTH, y + 60], fill=HEADER_BG)
    draw.text((x + TABLE_WIDTH // 2, y + 30), group_name, fill=TEXT_COLOR, font=font_group_title, anchor="mm")
    
    curr_y = y + 80
    draw.text((x + 35, curr_y), "POS", fill=(148, 163, 184), font=font_header, anchor="mm")
    draw.text((x + 90, curr_y), "SELECCIÓN", fill=(148, 163, 184), font=font_header, anchor="lm")
    draw.text((x + 390, curr_y), "PJ", fill=(148, 163, 184), font=font_header, anchor="mm")
    draw.text((x + 460, curr_y), "DG", fill=(148, 163, 184), font=font_header, anchor="mm")
    draw.text((x + 530, curr_y), "PTS", fill=ACCENT_PTS, font=font_header, anchor="mm")
    draw.line([(x + 15, curr_y + 16), (x + TABLE_WIDTH - 15, curr_y + 16)], fill=(71, 85, 105), width=1)
    
    curr_y += 36
    for i, t in enumerate(teams):
        if i % 2 == 1: draw.rectangle([x + 5, curr_y - 12, x + TABLE_WIDTH - 5, curr_y + 50], fill=(22, 32, 51))
        pos_color = (52, 211, 153) if i < 2 else ((251, 191, 36) if i == 2 else (248, 113, 113))
        draw.text((x + 35, curr_y + 15), str(i + 1), fill=pos_color, font=font_table_bold, anchor="mm")
        draw.text((x + 90, curr_y + 15), t['name'][:18], fill=TEXT_COLOR, font=font_table_p, anchor="lm")
        draw.text((x + 390, curr_y + 15), str(t['pj']), fill=TEXT_COLOR, font=font_table_p, anchor="mm")
        dg_str = f"+{t['dg']}" if t['dg'] > 0 else str(t['dg'])
        draw.text((x + 460, curr_y + 15), dg_str, fill=TEXT_COLOR, font=font_table_p, anchor="mm")
        draw.text((x + 530, curr_y + 15), str(t['pts']), fill=ACCENT_PTS, font=font_table_bold, anchor="mm")
        curr_y += 62

def main():
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    draw.text((WIDTH // 2, 80), "TABLAS DE POSICIONES - FASE DE GRUPOS [MAS PROBABLE]", fill=TEXT_COLOR, font=font_main_title, anchor="mm")
    
    MARGIN_X, MARGIN_Y, GAP_X, GAP_Y = 60, 180, 40, 50
    lista_grupos = list(grupos_consolidados.items())
    for i in range(12):
        col, row = i % 4, i // 4
        x = MARGIN_X + (col * (TABLE_WIDTH + GAP_X))
        y = MARGIN_Y + (row * (TABLE_HEIGHT + GAP_Y))
        draw_group_table(draw, x, y, lista_grupos[i][0], lista_grupos[i][1])
        
    img.save("Visual_Grupos_Dinamico.png")
    print("Imagen guardada en disco.")
    
    # --- NUEVA VENTANA EMERGENTE INTERACTIVA ---
    plt.figure(num="Tablas de Posiciones - Mundial 2026", figsize=(14, 8))
    plt.imshow(img)
    plt.axis('off')
    plt.tight_layout()
    print("Abriendo ventana emergente... Cérrala para finalizar el script.")
    plt.show() 

if __name__ == "__main__":
    main()