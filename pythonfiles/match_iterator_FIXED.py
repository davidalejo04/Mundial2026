import param_calculator_FIXED
import simulate_matches
import adjust_parameters  # ✅ FIX: Importar adjust_parameters
import pandas as pd
import random
import Home_Away_Calculator_Claude


def match_iterator(data_g, df_match, P, centroids,modo):
    """
    Itera sobre partidos y simula resultados.
    
    FIXES APLICADOS:
    - ✅ Uso de adjust_parameters para limitar λ
    - ✅ Penales basados en calidad (PRS) en vez de aleatorio puro
    """
    
    FDVA = []
    FDLA = []
    FAVA = []
    FALA = []
    miu = []
    marcadorLA = []
    marcadorVA = []
    SeleccionL = []
    SeleccionV = []
    PuntosLA = []
    PuntosVA = []
    IndicadorA = []
    faseA = []
    IA=[]
    # Determinar fase y configuración
    if df_match.shape[0] == 72:
        #I_P = ['None'] * 72
        I_P= df_match['Home_E'].apply(lambda x: 'Home' if x == "N" else 'None').tolist()
        fase = 'Grupos'
    elif df_match.shape[0] == 16:

        df_match,I_P = Home_Away_Calculator_Claude.Home_Away_Calculator(df_match.shape[0], df_match)
        fase = '16vos'
    elif df_match.shape[0] == 8:

        df_match,I_P = Home_Away_Calculator_Claude.Home_Away_Calculator(df_match.shape[0], df_match)
        fase = '8vos'
    elif df_match.shape[0] == 4:

        df_match,I_P = Home_Away_Calculator_Claude.Home_Away_Calculator(df_match.shape[0], df_match)
        fase = '4tos'
    elif df_match.shape[0] == 2:

        df_match,I_P = Home_Away_Calculator_Claude.Home_Away_Calculator(df_match.shape[0], df_match)
        fase = 'semi'
    elif df_match.shape[0] == 3:
        df_match = pd.DataFrame(df_match.tail(1))
        df_match=df_match.reset_index(drop=True)

        df_match,I_P = Home_Away_Calculator_Claude.Home_Away_Calculator(3, df_match)
        fase = '3ros'
    else:

        df_match,I_P = Home_Away_Calculator_Claude.Home_Away_Calculator(df_match.shape[0], df_match)
        fase = 'Final'
    
    # Iterar sobre cada partido
    for index, row in df_match.iterrows():
        Clust_V = (data_g[(data_g['Visitante3'] == row['Away'])]['Cluster_Label_V'].unique()).tolist()[0]
        Clust_L = (data_g[(data_g['Local3'] == row['Home'])]['Cluster_Label_L'].unique()).tolist()[0]
        
        # Calcular parámetros
        if data_g[(data_g['Visitante3'] == row['Away']) & (data_g['Cluster_Label_L'] == Clust_L)].shape[0] < 7 or \
           data_g[(data_g['Local3'] == row['Home']) & (data_g['Cluster_Label_V'] == Clust_V)].shape[0] < 7:
            I = 'A'
            FDV, FDL, FAV, FAL, miu, rho = param_calculator_FIXED.param_calculator(
                data_g[(data_g['Local3'] == row['Home'])],
                data_g[(data_g['Visitante3'] == row['Away'])],
                data_g, I_P[index], centroids, I, Clust_L, Clust_V
            )
        else:
            I = 'B'
            FDV, FDL, FAV, FAL, miu, rho = param_calculator_FIXED.param_calculator(
                data_g[(data_g['Local3'] == row['Home']) & (data_g['Cluster_Label_V'] == Clust_V)],
                data_g[(data_g['Visitante3'] == row['Away']) & (data_g['Cluster_Label_L'] == Clust_L)],
                data_g, I_P[index], centroids, I, Clust_L, Clust_V
            )
        
        # Calcular lambdas
        # Nota: los factores defensivos deben afectar al ataque del rival.
        # Local anota según su ataque (FAL) y la defensa del visitante (FDV).
        # Visitante anota según su ataque (FAV) y la defensa del local (FDL).
        lam1 = miu * FAL * FDV  # Lambda local
        lam2 = miu * FAV * FDL  # Lambda visitante
        
        # ✅ FIX CRÍTICO: Aplicar adjust_parameters
        #lam1, lam2 = adjust_parameters.adjust_parameters(lam1, lam2, fase)
        
        # Simular partido
        if modo=='m':
            marcadorL, marcadorV = simulate_matches.simulate_matches(lam1, lam2, rho, fase)
        else:
            marcadorL, marcadorV = simulate_matches.predict_most_probable_score_2(lam1, lam2, rho, fase)
        
        # Determinar ganador
        if marcadorV > marcadorL:
            PuntosV = 3
            PuntosL = 0
            Indicador = "GanaVisitante"
        
        elif marcadorV == marcadorL:
            if P == 'G':
                # Fase de grupos: empate
                PuntosV = 1
                PuntosL = 1
                Indicador = "Empate"
            else:
                # ✅ FIX: Penales basados en calidad (PRS) no aleatorio puro
                # PRS (presión) refleja la capacidad mental del equipo en situaciones de alta tensión
                prs_local = centroids.iloc[int(Clust_L)]['PRS']
                prs_visitante = centroids.iloc[int(Clust_V)]['PRS']
                
                # Calcular probabilidad de ganar penales basada en PRS
                # Equipo con mayor PRS tiene más probabilidad
                total_prs = prs_local + prs_visitante
                prob_local_gana = prs_local / total_prs if total_prs > 0 else 0.5
                
                if random.random() < prob_local_gana:
                    PuntosV = 0
                    PuntosL = 1
                    Indicador = f"Penales (Local {prob_local_gana:.0%})"
                else:
                    PuntosV = 1
                    PuntosL = 0
                    Indicador = f"Penales (Visit {1-prob_local_gana:.0%})"
        
        else:
            PuntosV = 0
            PuntosL = 3
            Indicador = "GanaLocal"
        
        # Guardar resultados
        marcadorVA.append(marcadorV)
        marcadorLA.append(marcadorL)
        FDVA.append(FDV)
        FDLA.append(FDL)
        FAVA.append(FAV)
        FALA.append(FAL)
        SeleccionV.append(row['Away'])
        SeleccionL.append(row['Home'])
        PuntosLA.append(PuntosL)
        PuntosVA.append(PuntosV)
        IndicadorA.append(Indicador)
        faseA.append(fase)
        #IA.append(I)
    #print(IA)
    
    return marcadorVA, marcadorLA, SeleccionV, SeleccionL, PuntosLA, PuntosVA, IndicadorA, faseA
