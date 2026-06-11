import os
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt 

# 1. CARGAR Y PROCESAR LOS DATOS DE RESDEF3
csv_path = "C:/Users/david/2026/v2/RESDEF3.xlsx"
if not os.path.exists(csv_path):
    raise FileNotFoundError(f"No se encontró el archivo {csv_path}.")

df = pd.read_excel(csv_path)
df['Partido'] = df['Partido'].astype(int)
df['Goles_L'] = df['Goles_L'].fillna(0).astype(int)
df['Goles_V'] = df['Goles_V'].fillna(0).astype(int)

matches_db = {}
for _, row in df.iterrows():
    matches_db[row['Partido']] = {
        'local': str(row['Local']).strip(),
        'goles_l': int(row['Goles_L']),
        'visitante': str(row['Visitante']).strip(),
        'goles_v': int(row['Goles_V']),
        'lugar': str(row['Lugar']).strip(),
        'fase': str(row['Fase']).strip()
    }

# 2. CONFIGURACIÓN VISUAL
WIDTH, HEIGHT = 3560, 1350
BG_COLOR = (15, 23, 42)      
BOX_BG = (30, 41, 59)        
BOX_BORDER = (71, 85, 105)   
TEXT_COLOR = (248, 250, 252) 
SCORE_WIN = (52, 211, 153)   
SCORE_LOSE = (148, 163, 184)
LINE_COLOR = (99, 102, 241)  

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
        draw.line([start1, (mid_x, start1[1]), (mid_x, end[1]), end], fill=LINE_COLOR, width=2)
        draw.line([start2, (mid_x, start2[1]), (mid_x, end[1]), end], fill=LINE_COLOR, width=2)

    # Conexiones Finales
    draw.line([(match_positions[101][0] + BOX_WIDTH, match_positions[101][1] + BOX_HEIGHT//2), (match_positions[104][0], match_positions[104][1] + 25)], fill=LINE_COLOR, width=2)
    draw.line([(match_positions[102][0], match_positions[102][1] + BOX_HEIGHT//2), (match_positions[104][0] + BOX_WIDTH, match_positions[104][1] + 25)], fill=LINE_COLOR, width=2)

def main():
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    draw.text((WIDTH // 2, 60), "CUADRO DE DESARROLLO - COPA MUNDIAL DE LA FIFA 2026", fill=TEXT_COLOR, font=font_title, anchor="mm")
    
    draw_branches(draw)
    for p_id in match_positions.keys():
        draw_match_card(draw, p_id)
        
    img.save("Visual_Cuadrangulares_Dinamico.png")
    print("Imagen guardada en disco.")

    # --- NUEVA VENTANA EMERGENTE INTERACTIVA ---
    plt.figure(num="Fixture Fase Final - Mundial 2026", figsize=(15, 8))
    plt.imshow(img)
    plt.axis('off') 
    plt.tight_layout()
    print("Abriendo ventana emergente... Cérrala para finalizar el script.")
    plt.show()

if __name__ == "__main__":
    main()


import os
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt 

# 1. CARGAR Y PROCESAR DATOS
resdef_path = csv_path
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
    draw.text((WIDTH // 2, 80), "TABLAS DE POSICIONES - FASE DE GRUPOS", fill=TEXT_COLOR, font=font_main_title, anchor="mm")
    
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