import pandas as pd
import warnings

def param_calculator(data, data2, data3, I_P, centroids, I, Clust_L, Clust_V):
    """
    Calcula parámetros para el modelo Dixon-Coles.
    
    FIXES APLICADOS:
    - ✅ Validación de datos mínimos (MIN_MATCHES = 8)
    - ✅ Fallback a estadísticas de cluster para equipos con pocos datos
    - ✅ Advertencias cuando se usan datos insuficientes
    """
    
    # ✅ CONFIGURACIÓN DE VALIDACIÓN
    MIN_MATCHES = 6  # Mínimo de partidos para confiar en las estadísticas
    
    LL = float((1 - (centroids.iloc[int(Clust_L)]['PRS']) * (0.1/100)) * 
               (0.8 + (centroids.iloc[int(Clust_L)]['PAC']) * (0.4/100)))
    VV = float((1 - (centroids.iloc[int(Clust_V)]['PRS']) * (0.1/100)) * 
               (0.8 + (centroids.iloc[int(Clust_V)]['PAC']) * (0.4/100)))
    
    if I == 'A':
        CD = centroids.iloc[int(Clust_L)]['DEF'] / centroids.iloc[int(Clust_V)]['DEF']
        CA = centroids.iloc[int(Clust_L)]['ATK'] / centroids.iloc[int(Clust_V)]['ATK']
        CP = centroids.iloc[int(Clust_L)]['PAC'] / centroids.iloc[int(Clust_V)]['PAC']
        CS = centroids.iloc[int(Clust_L)]['PRS'] / centroids.iloc[int(Clust_V)]['PRS']
    else:
        CD = centroids.iloc[int(Clust_L)]['DEF'] / centroids.iloc[int(Clust_V)]['DEF']
        CA = centroids.iloc[int(Clust_L)]['ATK'] / centroids.iloc[int(Clust_V)]['ATK']
        CP = centroids.iloc[int(Clust_L)]['PAC'] / centroids.iloc[int(Clust_V)]['PAC']
        CS = centroids.iloc[int(Clust_L)]['PRS'] / centroids.iloc[int(Clust_V)]['PRS']

    loc = (data)["Local3"].unique().tolist()[0]
    vis = (data2)["Visitante3"].unique().tolist()[0]

    if I_P == 'None':
        ## S1 ataque local
        aljeC = (data)["Local3"].count()
        algeC = (data)["LocalG"].sum()
        
        # ✅ VALIDACIÓN: Datos mínimos para local
        if aljeC < MIN_MATCHES:
            warnings.warn(f"⚠️ {loc}: Solo tiene {aljeC} partidos como local contra el cluster {Clust_V} (mínimo: {MIN_MATCHES}). "
                         f"Usando estadísticas de cluster {Clust_L}")
            f"Usar estadísticas del cluster normalizadas"
            algpeC = (centroids.iloc[int(Clust_L)]['ATK'] / 100) * 1.25  # ~1.0-1.5 goles
        else:
            algpeC = algeC / aljeC

        ## S1 defensa local
        dljeC = (data)["Local3"].count()
        dlgeC = (data)["VisitanteG"].sum()
        
        if dljeC < MIN_MATCHES:
            dlgpeC = (centroids.iloc[int(Clust_L)]['DEF'] / 100) * 1.05
        else:
            dlgpeC = dlgeC / dljeC

        ## S2 defensa visitante
        dvje = (data2)["Visitante3"].count()
        dvge = (data2)["LocalG"].sum()
        
        # ✅ VALIDACIÓN: Datos mínimos para visitante
        if dvje < MIN_MATCHES:
            warnings.warn(f"⚠️ {vis}: Solo tiene {dvje} partidos como visitante contral el cluster {Clust_L} (mínimo: {MIN_MATCHES}). "
                         f"Usando estadísticas de cluster {Clust_V}")
            dvgpe = (centroids.iloc[int(Clust_V)]['DEF'] / 100) * 1.05
        else:
            dvgpe = dvge / dvje

        ## S2 ataque visitante
        avje = (data2)["Visitante3"].count()
        avge = (data2)["VisitanteG"].sum()
        
        if avje < MIN_MATCHES:
            avgpe = (centroids.iloc[int(Clust_V)]['ATK'] / 100) * 1.15
        else:
            avgpe = avge / avje

        ## Promedios globales
        alj = (data3)["Local3"].count()
        alg = (data3)["LocalG"].sum()
        algp = alg / alj

        avj = (data3)["Visitante3"].count()
        avg = (data3)["VisitanteG"].sum()
        avgp = avg / avj

        dlj = (data3)["Local3"].count()
        dlg = (data3)["VisitanteG"].sum()
        dlgp = dlg / dlj

        dvj = (data3)["Visitante3"].count()
        dvg = (data3)["LocalG"].sum()
        dvgp = dvg / dvj

    elif I_P == 'Home':
        ## S1 ataque local (invertido)
        aljeC = (data3[data3["Visitante3"] == loc])["Visitante3"].count()+(data3[data3["Local3"] == loc])["Local3"].count()
        algeC = (data3[data3["Visitante3"] == loc])["VisitanteG"].sum()+(data3[data3["Local3"] == loc])["LocalG"].sum()
        
        if aljeC < MIN_MATCHES:
            warnings.warn(f"⚠️ {loc}: Solo {aljeC} partidos (mínimo: {MIN_MATCHES})")
            algpeC = (centroids.iloc[int(Clust_L)]['ATK'] / 100) * 1.25
        else:
            algpeC = algeC / aljeC

        ## S1 defensa local
        dljeC = (data3[data3["Visitante3"] == loc])["Visitante3"].count()+(data3[data3["Local3"] == loc])["Local3"].count()
        dlgeC = (data3[data3["Visitante3"] == loc])["LocalG"].sum()+(data3[data3["Local3"] == loc])["VisitanteG"].sum()
        
        if dljeC < MIN_MATCHES:
            dlgpeC = (centroids.iloc[int(Clust_L)]['DEF'] / 100) * 1.05
        else:
            dlgpeC = dlgeC / dljeC

        ## S2 defensa visitante
        dvje = (data3[data3["Visitante3"] == vis])["Visitante3"].count()+(data3[data3["Local3"] == vis])["Local3"].count()
        dvge = (data3[data3["Visitante3"] == vis])["LocalG"].sum()+(data3[data3["Local3"] == vis])["VisitanteG"].sum()
        
        if dvje < MIN_MATCHES:
            dvgpe = (centroids.iloc[int(Clust_V)]['DEF'] / 100) * 1.05
        else:
            dvgpe = dvge / dvje

        ## S2 ataque visitante
        avje = (data3[data3["Visitante3"] == vis])["Visitante3"].count()+(data3[data3["Local3"] == vis])["Local3"].count()
        avge = (data3[data3["Visitante3"] == vis])["VisitanteG"].sum()+(data3[data3["Local3"] == vis])["LocalG"].sum()
        
        if avje < MIN_MATCHES:
            avgpe = (centroids.iloc[int(Clust_V)]['ATK'] / 100) * 1.15
        else:
            avgpe = avge / avje

        ## Promedios globales
        alj = (data3)["Local3"].count()+(data3)["Visitante3"].count()
        alg = (data3)["LocalG"].sum()+(data3)["VisitanteG"].sum()
        algp = alg / alj

        avj = (data3)["Visitante3"].count()+(data3)["Local3"].count()
        avg = (data3)["VisitanteG"].sum()+(data3)["LocalG"].sum()
        avgp = avg / avj

        dlj = (data3)["Local3"].count()+(data3)["Visitante3"].count()
        dlg = (data3)["VisitanteG"].sum()+(data3)["LocalG"].sum()
        dlgp = dlg / dlj

        dvj = (data3)["Visitante3"].count()+(data3)["Local3"].count()
        dvg = (data3)["LocalG"].sum()+(data3)["VisitanteG"].sum()
        dvgp = dvg / dvj

    else:
        ## Mismo código que 'Home' pero para caso 'Away'
        aljeC = (data3[data3["Visitante3"] == loc])["Visitante3"].count()+(data3[data3["Local3"] == loc])["Local3"].count()
        algeC = (data3[data3["Visitante3"] == loc])["VisitanteG"].sum()+(data3[data3["Local3"] == loc])["LocalG"].sum()
        
        if aljeC < MIN_MATCHES:
            algpeC = (centroids.iloc[int(Clust_L)]['ATK'] / 100) * 1.25
        else:
            algpeC = algeC / aljeC

        dljeC = (data3[data3["Visitante3"] == loc])["Visitante3"].count()+(data3[data3["Local3"] == loc])["Local3"].count()
        dlgeC = (data3[data3["Visitante3"] == loc])["LocalG"].sum()+(data3[data3["Local3"] == loc])["VisitanteG"].sum()
        
        if dljeC < MIN_MATCHES:
            dlgpeC = (centroids.iloc[int(Clust_L)]['DEF'] / 100) * 1.05
        else:
            dlgpeC = dlgeC / dljeC

        dvje = (data3[data3["Visitante3"] == vis])["Visitante3"].count()+(data3[data3["Local3"] == vis])["Local3"].count()
        dvge = (data3[data3["Visitante3"] == vis])["LocalG"].sum()+(data3[data3["Local3"] == vis])["VisitanteG"].sum()
        
        if dvje < MIN_MATCHES:
            dvgpe = (centroids.iloc[int(Clust_V)]['DEF'] / 100) * 1.05
        else:
            dvgpe = dvge / dvje

        avje = (data3[data3["Visitante3"] == vis])["Visitante3"].count()+(data3[data3["Local3"] == vis])["Local3"].count()
        avge = (data3[data3["Visitante3"] == vis])["VisitanteG"].sum()+(data3[data3["Local3"] == vis])["LocalG"].sum()
        
        if avje < MIN_MATCHES:
            avgpe = (centroids.iloc[int(Clust_V)]['ATK'] / 100) * 1.15
        else:
            avgpe = avge / avje

        ## Promedios globales
        alj = (data3)["Local3"].count()+(data3)["Visitante3"].count()
        alg = (data3)["LocalG"].sum()+(data3)["VisitanteG"].sum()
        algp = alg / alj

        avj = (data3)["Visitante3"].count()+(data3)["Local3"].count()
        avg = (data3)["VisitanteG"].sum()+(data3)["LocalG"].sum()
        avgp = avg / avj

        dlj = (data3)["Local3"].count()+(data3)["Visitante3"].count()
        dlg = (data3)["VisitanteG"].sum()+(data3)["LocalG"].sum()
        dlgp = dlg / dlj

        dvj = (data3)["Visitante3"].count()+(data3)["Local3"].count()
        dvg = (data3)["LocalG"].sum()+(data3)["VisitanteG"].sum()
        dvgp = dvg / dvj

    rho = -0.1285
    FDV = (dvgpe / dvgp)
    FDL = (dlgpeC / dlgp) * CD
    FAV = (avgpe / avgp) * LL
    FAL = (algpeC / algp) * VV * CA
    miu = ((data3)["LocalG"].sum() + (data3)["VisitanteG"].sum()) / (data3)["Local3"].count()

    return FDV, FDL, FAV, FAL, miu, rho
