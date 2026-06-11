
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
from PIL import Image, ImageDraw, ImageFont

# 1. PROCESAR ACERVO MONTECARLO (PRIDEF3) PARA CALCULAR CORRELACIONES
pride_path = "C:/Users/david/2026/v2/PRIDEF3.xlsx"
resdef_path = "C:/Users/david/2026/v2/RESDEF3.xlsx"

if not os.path.exists(pride_path) or not os.path.exists(resdef_path):
    raise FileNotFoundError("Asegúrate de tener PRIDEF3.xlsx - Sheet1.csv y RESDEF3.xlsx - Sheet1.csv en el directorio.")

print("Analizando interacciones en el acervo de Montecarlo (PRIDEF3)...")
df_pride = pd.read_excel(pride_path)

# Filtrar fase final (eliminación directa)
df_knockout = df_pride[df_pride['Fase'].str.strip() != 'Grupos'].copy()

# Crear una variable binaria: 1 si gana el equipo clasificado como Local, 0 si gana el Visitante
df_knockout['Winner_Loc'] = (df_knockout['Indicador'].str.strip() == 'GanaLocal').astype(int)

# Pivotar para tener las simulaciones como filas y los Partidos como columnas
pivot_simunicaciones = df_knockout.pivot(index='simulacion', columns='Partido', values='Winner_Loc').fillna(0)

# Calcular la matriz de correlación de Pearson entre los resultados de los partidos
matrix_correlacion = pivot_simunicaciones.corr()

# 2. CARGAR LA SIMULACIÓN MÁS PROBABLE (RESDEF3) PARA EL LIENZO BASE
df_res = pd.read_excel(resdef_path)
df_res['Partido'] = df_res['Partido'].astype(int)
df_res['Goles_L'] = df_res['Goles_L'].fillna(0).astype(int)
df_res['Goles_V'] = df_res['Goles_V'].fillna(0).astype(int)

# Garantizar un único registro por partido para el diseño visual estático
df_res = df_res.drop_duplicates(subset=['Partido'], keep='first')

matches_db = {}
for _, row in df_res.iterrows():
    matches_db[row['Partido']] = {
        'local': str(row['Local']).strip(),
        'goles_l': int(row['Goles_L']),
        'visitante': str(row['Visitante']).strip(),
        'goles_v': int(row['Goles_V']),
        'lugar': str(row['Lugar']).strip(),
        'fase': str(row['Fase']).strip()
    }

# 3. CONFIGURACIÓN DEL LIENZO GRÁFICO (PILLOW)
WIDTH, HEIGHT = 3560, 1350
BG_COLOR = (15, 23, 42)      
BOX_BG = (30, 41, 59)        
BOX_BORDER = (71, 85, 105)   
TEXT_COLOR = (248, 250, 252) 
SCORE_WIN = (52, 211, 153)   
SCORE_LOSE = (148, 163, 184)
LINE_COLOR = (51, 65, 85) # Líneas estructurales tenues para resaltar el grafo

BOX_WIDTH, BOX_HEIGHT = 320, 90
Y_OFFSET = 120

try:
    font_path = "arial.ttf"
    font_main = ImageFont.truetype(font_path, 20)
    font_score = ImageFont.truetype(font_path, 26)
    font_title = ImageFont.truetype(font_path, 55)
    font_info = ImageFont.truetype(font_path, 14)
except IOError:
    font_main = font_score = font_title = font_info = ImageFont.load_default()

# Posiciones exactas de los nodos/partidos
match_positions = {
    74: (80, 150 + Y_OFFSET),   77: (80, 275 + Y_OFFSET),
    73: (80, 400 + Y_OFFSET),   75: (80, 525 + Y_OFFSET),
    83: (80, 650 + Y_OFFSET),   84: (80, 775 + Y_OFFSET),
    81: (80, 900 + Y_OFFSET),   82: (80, 1025 + Y_OFFSET),
    89: (460, 212 + Y_OFFSET),  90: (460, 462 + Y_OFFSET),
    91: (460, 712 + Y_OFFSET),  92: (460, 962 + Y_OFFSET),
    97: (840, 337 + Y_OFFSET),  98: (840, 837 + Y_OFFSET),
    101: (1220, 587 + Y_OFFSET),
    104: (1620, 480 + Y_OFFSET), 103: (1620, 720 + Y_OFFSET),
    102: (2020, 587 + Y_OFFSET),
    99: (2400, 337 + Y_OFFSET),  100: (2400, 837 + Y_OFFSET),
    93: (2780, 212 + Y_OFFSET),  94: (2780, 462 + Y_OFFSET),
    95: (2780, 712 + Y_OFFSET),  96: (2780, 962 + Y_OFFSET),
    76: (3160, 150 + Y_OFFSET),  78: (3160, 275 + Y_OFFSET),
    79: (3160, 400 + Y_OFFSET),  80: (3160, 525 + Y_OFFSET),
    86: (3160, 650 + Y_OFFSET),  88: (3160, 775 + Y_OFFSET),
    85: (3160, 900 + Y_OFFSET),  87: (3160, 1025 + Y_OFFSET)
}

connections = [
    ((74, 77), 89, 'left'),   ((73, 75), 90, 'left'),   ((83, 84), 91, 'left'),   ((81, 82), 92, 'left'),
    ((89, 90), 97, 'left'),   ((91, 92), 98, 'left'),   ((97, 98), 101, 'left'),
    ((76, 78), 93, 'right'),  ((79, 80), 94, 'right'),  ((86, 88), 95, 'right'),  ((85, 87), 96, 'right'),
    ((93, 94), 99, 'right'),  ((95, 96), 100, 'right'), ((99, 100), 102, 'right')
]

def draw_match_card(draw, p_id):
    if p_id not in matches_db: return
    x, y = match_positions[p_id]
    m = matches_db[p_id]
    draw.rounded_rectangle([x, y, x + BOX_WIDTH, y + BOX_HEIGHT], radius=8, fill=BOX_BG, outline=BOX_BORDER, width=1)
    draw.line([(x + 230, y + 8), (x + 230, y + BOX_HEIGHT - 8)], fill=(71, 85, 105), width=1)
    draw.text((x + 115, y + 74), f"P{p_id} - {m['lugar']}", fill=(148, 163, 184), font=font_info, anchor="mm")
    
    c_l, c_v = SCORE_LOSE, SCORE_LOSE
    if m['goles_l'] > m['goles_v']: c_l = SCORE_WIN
    elif m['goles_v'] > m['goles_l']: c_v = SCORE_WIN
    
    draw.text((x + 20, y + 24), m['local'][:16], fill=TEXT_COLOR, font=font_main, anchor="lm")
    draw.text((x + 20, y + 50), m['visitante'][:16], fill=TEXT_COLOR, font=font_main, anchor="lm")
    draw.text((x + 275, y + 24), str(m['goles_l']), fill=c_l, font=font_score, anchor="mm")
    draw.text((x + 275, y + 50), str(m['goles_v']), fill=c_v, font=font_score, anchor="mm")

def draw_branches(draw):
    for (p1, p2), p_next, side in connections:
        pos1, pos2, pos_next = match_positions[p1], match_positions[p2], match_positions[p_next]
        if side == 'left':
            start1, start2 = (pos1[0] + BOX_WIDTH, pos1[1] + BOX_HEIGHT//2), (pos2[0] + BOX_WIDTH, pos2[1] + BOX_HEIGHT//2)
            end = (pos_next[0], pos_next[1] + BOX_HEIGHT//2)
            mid_x = start1[0] + (end[0] - start1[0]) // 2
        else:
            start1, start2 = (pos1[0], pos1[1] + BOX_HEIGHT//2), (pos2[0], pos2[1] + BOX_HEIGHT//2)
            end = (pos_next[0] + BOX_WIDTH, pos_next[1] + BOX_HEIGHT//2)
            mid_x = start1[0] - (start1[0] - end[0]) // 2
        draw.line([start1, (mid_x, start1[1]), (mid_x, end[1]), end], fill=LINE_COLOR, width=1)
        draw.line([start2, (mid_x, start2[1]), (mid_x, end[1]), end], fill=LINE_COLOR, width=1)

# 4. CONSTRUCCIÓN DEL LIENZO
img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
draw = ImageDraw.Draw(img)
draw.text((WIDTH // 2, 60), "DIAGRAMA DE GRAFOS: EFECTOS E INTERACCIONES EN LA FASE FINAL", fill=TEXT_COLOR, font=font_title, anchor="mm")

draw_branches(draw)
for p_id in match_positions.keys():
    draw_match_card(draw, p_id)

# 5. INTEGRACIÓN DE NETWORKX Y MATPLOTLIB (CAPA DE GRAFOS SOBRE EL CUADRANGULAR)
plt.figure(num="Grafo de Correlaciones - Montecarlo", figsize=(18, 10))
plt.imshow(img) # El cuadrangular se vuelve nuestro fondo real

# Inicializar grafo de NetworkX
G = nx.Graph()

# Agregar los partidos como nodos
for p_id in match_positions.keys():
    G.add_node(p_id)

# Filtrar y preparar las aristas basadas en dependencias significativas
UMBRAL_CORRELACION = 0.20 

edges = []
weights = []
edge_colors = []

partidos_disponibles = matrix_correlacion.columns

for i in range(len(partidos_disponibles)):
    for j in range(i + 1, len(partidos_disponibles)):
        p1 = partidos_disponibles[i]
        p2 = partidos_disponibles[j]
        
        if p1 in match_positions and p2 in match_positions:
            val_corr = matrix_correlacion.loc[p1, p2]
            
            if abs(val_corr) > UMBRAL_CORRELACION and not pd.isna(val_corr):
                G.add_edge(p1, p2, weight=val_corr)
                edges.append((p1, p2))
                weights.append(abs(val_corr) * 12) 
                edge_colors.append(val_corr)

# Mapear las posiciones del grafo al CENTRO de las tarjetas
pos_grafo = {p_id: (x + BOX_WIDTH // 2, y + BOX_HEIGHT // 2) for p_id, (x, y) in match_positions.items()}

# --- CORRECCIÓN AQUÍ: Cambiado plt.cm.Normalize por plt.Normalize ---
sm = plt.cm.ScalarMappable(cmap=plt.cm.coolwarm, norm=plt.Normalize(vmin=-0.4, vmax=0.4))
sm.set_array([])

nodes_draw = nx.draw_networkx_nodes(
    G, pos_grafo, 
    node_size=400, 
    node_color='#a5b4fc', 
    alpha=0.3
)

edges_draw = nx.draw_networkx_edges(
    G, pos_grafo, 
    edgelist=edges, 
    width=weights, 
    edge_color=edge_colors, 
    edge_cmap=plt.cm.coolwarm, 
    edge_vmin=-0.4, 
    edge_vmax=0.4, 
    alpha=0.75,
    connectionstyle="arc3,rad=0.15"
)

cbar = plt.colorbar(sm, ax=plt.gca(), orientation='horizontal', pad=0.02, shrink=0.4)
cbar.set_label('Índice de Correlación / Dependencia en Simulaciones (Montecarlo)', color='black', fontsize=12)

plt.axis('off')
plt.tight_layout()

print("\n¡Éxito! Abriendo el visor interactivo de grafos...")
plt.show()