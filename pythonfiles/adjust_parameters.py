# Antes de pasar lam1 y lam2 a dixon_coles_pmf:
def adjust_parameters(lam1, lam2, fase,mode):
    # Deflactores por fase (coherencia historica)
    deflactores = {'Grupos': 1.0, '16vos': 0.93, '8vos': 0.88, '4tos': 0.83, 'semi': 0.80, 'Final': 0.75}

    adj = deflactores.get(fase, 1.0)

    if mode == 'montecarlo':
        # Cap dinamico por fase para no comprimir demasiado las diferencias
        cap_fase = {'Grupos': 3.0, '16vos': 2.9, '8vos': 2.7, '4tos': 2.5, 'semi': 2.2, '3ros': 2.0, 'Final': 2.0}
        lam1 *= adj
        lam2 *= adj

        # Cap de seguridad por fase
        cap = cap_fase.get(fase, 2.5)
        lam1 = min(lam1, cap)
        lam2 = min(lam2, cap)
    else: 
        mode == 'deterministic'

        # Aplicamos el ajuste de fase base
        lam1 *= adj
        lam2 *= adj
        
        # Techos dinámicos altos para permitir que el argmax elija 3 o 4 goles
        caps = {
            'Grupos': 3.9, '16vos': 3.6, '8vos': 3.0, '4tos': 2.9, 'semi': 2.0, 'Final': 2.0
        }
        max_cap = caps.get(fase, 3.2)
        
        # Ajuste asimétrico para abrir la brecha en partidos desiguales
        diff = lam1 - lam2
        umbral_disparidad = 0.35
        
        if diff > umbral_disparidad:
            lam1 += (diff * 0.35)
            lam2 -= (diff * 0.20)
        elif diff < -umbral_disparidad:
            lam2 += (abs(diff) * 0.35)
            lam1 -= (abs(diff) * 0.20)
            
        lam1 = min(max(lam1, 0.1), max_cap)
        lam2 = min(max(lam2, 0.1), max_cap)


    

    return lam1, lam2
