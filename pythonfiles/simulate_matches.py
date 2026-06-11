
import dixon_coles_cdf_d
import sample_score_from_cdf
#def simulate_matches(lam1, lam2, rho, max_goals=6):
def simulate_matches(lam1, lam2, rho,fase, max_goals=5):
    mode='montecarlo'
    #cdf = dixon_coles_cdf_d.build_dixon_coles_cdf_d(lam1, lam2, rho, max_goals)
    cdf = dixon_coles_cdf_d.build_dixon_coles_cdf_d(lam1, lam2, rho,fase,mode, max_goals)
    
    results=(sample_score_from_cdf.sample_score_from_cdf(cdf))

    return results

def predict_most_probable_score(lam1, lam2, rho, fase, max_goals=5):
    """
    Nueva función: Calcula las probabilidades macro (Local, Empate, Visitante)
    y obtiene el marcador más probable alineado con el resultado más esperado,
    incluyendo un margen de tolerancia para rescatar los empates en Fase de Grupos.
    """
    mode = 'deterministic'
    # 1. Obtener la CDF calculada y normalizada
    cdf = dixon_coles_cdf_d.build_dixon_coles_cdf_d(lam1, lam2, rho, fase, mode, max_goals)
    
    # 2. Reconstruir las probabilidades individuales a partir de la CDF acumulada
    score_probs = []
    prev_cumulative = 0.0
    for cumulative, (x, y) in cdf:
        p = cumulative - prev_cumulative
        score_probs.append(((x, y), p))
        prev_cumulative = cumulative
        
    # 3. Agrupar probabilidades para determinar el Ganador Más Probable
    prob_home = 0.0
    prob_draw = 0.0
    prob_away = 0.0
    
    for (x, y), p in score_probs:
        if x > y:
            prob_home += p
        elif x == y:
            prob_draw += p
        else:
            prob_away += p
            
    outcomes = {
        'Local': prob_home,
        'Empate': prob_draw,
        'Visitante': prob_away
    }
    
# --- NUEVA LÓGICA: MARGEN DE TOLERANCIA PARA EMPATES (Fase de Grupos) ---

    # PARÁMETROS CALIBRABLES:
    # tol_paridad: Máxima diferencia entre Local y Visita para considerar que el partido está "cerrado".
    # tol_empate: Qué tan cerca (como máximo) debe estar el empate de la victoria más probable.
    tol_paridad = 0.09  # 6% de diferencia máxima
    tol_empate = 0.18   # El empate puede estar hasta un 18% por debajo del favorito
    
    diff_home_away = abs(prob_home - prob_away)
    max_prob_victoria = max(prob_home, prob_away)
    diff_empate_ganador = max_prob_victoria - prob_draw
    
    # Si el partido es muy parejo Y la probabilidad de empate está cerca de los líderes:
    if (diff_home_away <= tol_paridad and diff_empate_ganador <= tol_empate) or (diff_home_away <= tol_paridad*0.9 and  diff_empate_ganador >= tol_empate*2) or (diff_empate_ganador<tol_empate*(-3.2)) :
        ganador_mas_probable = 'Empate'
    else:
        # Si no cumple el criterio de cercanía, se usa el argmax clásico
        ganador_mas_probable = max(outcomes, key=outcomes.get)

    
    # 4. Encontrar el marcador más probable DENTRO del outcome ganador
    marcador_mas_probable = None
    max_p_marcador = -1.0
    
    for (x, y), p in score_probs:
        es_coherente = False
        if ganador_mas_probable == 'Local' and x > y:
            es_coherente = True
        elif ganador_mas_probable == 'Empate' and x == y:
            es_coherente = True
        elif ganador_mas_probable == 'Visitante' and x < y:
            es_coherente = True
            
        if es_coherente and p > max_p_marcador:
            max_p_marcador = p
            marcador_mas_probable = (x, y)
            
    return marcador_mas_probable

def predict_most_probable_score_2(lam1, lam2, rho, fase, max_goals=5):
    mode = 'deterministic'
    cdf = dixon_coles_cdf_d.build_dixon_coles_cdf_d(lam1, lam2, rho, fase, mode, max_goals)
    
    # Reconstruir probabilidades individuales
    score_probs = []
    prev = 0.0
    for cumulative, (x, y) in cdf:
        p = cumulative - prev
        score_probs.append(((x, y), p))
        prev = cumulative

    # Argmax directo sobre TODOS los marcadores
    marcador_mas_probable = max(score_probs, key=lambda item: item[1])[0]
    return marcador_mas_probable