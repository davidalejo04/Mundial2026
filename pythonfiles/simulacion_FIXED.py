import numpy as np
import pandas as pd
import statsmodels as sm
import math as mt
import scipy as sc
import random as rm
import dixon_coles_inverse_cdf
from scipy.stats import poisson
import second_phase
import match_iterator_FIXED
import warnings

def simulacion(join_df_f, centroids,modo):
    """
    Función principal de simulación del Mundial 2026.
    
    FIXES APLICADOS:
    - ✅ Bug #3: Validación de equipos antes de asignar cluster default
    - ✅ Advertencias para equipos con datos insuficientes
    """

    ## CARGAMOS DATA Y ASIGNAMOS CLUSTERS A CADA EQUIPO PARA MEJORAR LA EXACTITUD DEL MODELO

    data = pd.read_excel("C:/Users/david/2026/v2/Futbol_3__779033794.xlsx", sheet_name="Hoja4")
    data_dic = pd.read_excel("C:/Users/david/2026/v2/EstudioEstadisticoMundial.xlsx", sheet_name="Hoja1")
    data_match = pd.read_excel("C:/Users/david/2026/v2/Matches_Groups_Phase.xlsx", sheet_name="Hoja1")
    df_match_place = pd.read_excel('C:/Users/david/2026/v2/Match_Places.xlsx', sheet_name='Hoja1')
    df_match_place = pd.DataFrame(df_match_place)

    data = pd.DataFrame(data)
    df_dic = pd.DataFrame(data_dic)
    df_dic = df_dic[(df_dic['Escogido'] == 'Y')]
    df_match = pd.DataFrame(data_match)
    
    # ✅ FIX CRÍTICO: Validar equipos ANTES de hacer merge
    equipos_en_mundial = pd.concat([df_match['Home'], df_match['Away']]).unique()
    equipos_con_cluster = join_df_f['Selección_r'].unique()
    equipos_sin_cluster = set(equipos_en_mundial) - set(equipos_con_cluster)

    # Evitar hardcodear el cluster "default". Con 4 clusters (0..3) puede quedar apuntando a un cluster
    # fuerte/incorrecto y sesgar los cálculos. Para equipos sin cluster (normalmente selecciones débiles),
    # usar el cluster "más débil" según centroides como fallback.
    try:
        default_cluster = int(
            centroids[['PAC', 'DEF', 'ATK', 'PRS']].sum(axis=1).astype(float).idxmin()
        )
    except Exception:
        default_cluster = 0
    
    if len(equipos_sin_cluster) > 0:
        warnings.warn(
            f"\n⚠️  ADVERTENCIA CRÍTICA: Los siguientes equipos del Mundial NO tienen cluster asignado:\n"
            f"{list(equipos_sin_cluster)}\n"
            f"Se les asignará cluster {default_cluster} (default) pero esto puede afectar resultados.\n"
            f"Considera agregar estos equipos a TeamStats.xlsx para mejores resultados."
        )
        
        # Contar partidos históricos de estos equipos
        for equipo in equipos_sin_cluster:
            partidos_local = data[data['Local3'] == equipo].shape[0]
            partidos_visitante = data[data['Visitante3'] == equipo].shape[0]
            total_partidos = partidos_local + partidos_visitante
            
            if total_partidos < 30:
                warnings.warn(
                    f"   ⚠️  {equipo}: Solo {total_partidos} partidos históricos "
                    f"(recomendado: ≥30). Resultados poco confiables."
                )
    
    # Merge de datos con clusters
    data_g = pd.merge(
        pd.merge(
            data, join_df_f,
            left_on='Local3',
            right_on='Selección_r',
            how='left',
            suffixes=('_left', '_right')
        ).rename(columns={'Cluster_Label': 'Cluster_Label_L', 'Selección_r': 'Selección_L'}),
        join_df_f,
        left_on='Visitante3',
        right_on='Selección_r',
        how='left',
        suffixes=('_left', '_right')
    ).rename(columns={'Cluster_Label': 'Cluster_Label_V', 'Selección_r': 'Selección_V'})
    
    # ✅ MEJORADO: Default de cluster solo como último recurso (dinámico según centroides)
    data_g['Cluster_Label_L'] = data_g['Cluster_Label_L'].fillna(default_cluster)
    data_g['Cluster_Label_V'] = data_g['Cluster_Label_V'].fillna(default_cluster)
    data_g['Selección_L'] = data_g['Selección_L'].fillna(data_g['Local3'])
    data_g['Selección_V'] = data_g['Selección_V'].fillna(data_g['Visitante3'])
    data_g = pd.DataFrame(data_g)

    ## OBTENEMOS LOS RESULTADOS DE LA FASE DE GRUPOS

    P = 'G'
    marcadorVA, marcadorLA, SeleccionV, SeleccionL, PuntosLA, PuntosVA, IndicadorA, fase = \
        match_iterator_FIXED.match_iterator(data_g, df_match, P, centroids,modo)
    
    ## ORGANIZAMOS RESULTADOS DE LA FASE DE GRUPOS

    df_resultados = pd.concat([
        pd.DataFrame(SeleccionL).rename(columns={0: 'Local'}),
        pd.DataFrame(marcadorLA).rename(columns={0: 'Goles_L'}),
        pd.DataFrame(SeleccionV).rename(columns={0: 'Visitante'}),
        pd.DataFrame(marcadorVA).rename(columns={0: 'Goles_V'}),
        pd.DataFrame(PuntosLA).rename(columns={0: 'PuntosL'}),
        pd.DataFrame(PuntosVA).rename(columns={0: 'PuntosV'}),
        pd.DataFrame(IndicadorA).rename(columns={0: 'Indicador'}),
        pd.DataFrame(fase).rename(columns={0: 'Fase'})
    ], axis=1)
    df_resultados = df_resultados.tail(72)
    
    df_analisis = pd.concat([
        pd.concat([pd.DataFrame(SeleccionL), pd.DataFrame(SeleccionV)], axis=0).rename(columns={0: 'Seleccion'}),
        pd.concat([pd.DataFrame(marcadorLA), pd.DataFrame(marcadorVA)], axis=0).rename(columns={0: 'GolesF'}),
        pd.concat([pd.DataFrame(PuntosLA), pd.DataFrame(PuntosVA)], axis=0).rename(columns={0: 'Puntos'}),
        pd.concat([pd.DataFrame(marcadorVA), pd.DataFrame(marcadorLA)], axis=0).rename(columns={0: 'GolesC'})
    ], axis=1)
    df_analisis = df_analisis.groupby(['Seleccion'])[['GolesF', 'GolesC', 'Puntos']].sum()
    df_analisis = pd.DataFrame(df_analisis).reset_index()

    ## Calculamos posiciones

    df_analisis = pd.merge(
        df_analisis, df_dic,
        left_on='Seleccion',
        right_on='Selección',
        how='left',
        suffixes=('_left', '_right')
    )
    columnas_a_mantener = ['Seleccion', 'Grupo', 'GolesF', 'GolesC', 'Puntos']
    df_analisis = df_analisis[columnas_a_mantener]
    df_analisis['Dif'] = df_analisis['GolesF'] - df_analisis['GolesC']
    df_analisis = df_analisis.sort_values(
        by=['Grupo', 'Puntos', 'Dif', 'GolesF'], 
        ascending=False
    ).reset_index()
    df_analisis['num'] = 1
    df_analisis['Pos'] = df_analisis.groupby(['Grupo'])[['num']].cumcount() + 1

    ## Calculamos clasificados directos (1ros y 2dos)

    df_dir = df_analisis[df_analisis['Pos'] < 3]

    ## Calculamos mejores terceros

    df_3ros = df_analisis[df_analisis['Pos'] == 3].sort_values(
        by=['Puntos', 'Dif', 'GolesF'], 
        ascending=False
    ).reset_index().head(8)
    df_3ros = df_3ros.drop(['level_0'], axis=1)

    ## SORTEAMOS LA SEGUNDA FASE A PARTIR DE LOS RESULTADOS DE LA FASE DE GRUPOS
    ## CALCULAMOS LOS RESULTADOS DE LA SEGUNDA FASE:

    P = 'S'

    # Definimos la matriz de rivales en 16vos
    m16 = second_phase.second_phase_16(df_dir, df_3ros)

    ## Calculamos los marcadores de cada duelo
    marcadorVAS, marcadorLAS, SeleccionVS, SeleccionLS, PuntosLAS, PuntosVAS, IndicadorAS, faseS = \
        match_iterator_FIXED.match_iterator(data_g, m16, P, centroids,modo)

    df_resultados_16 = pd.concat([
        pd.DataFrame(SeleccionLS).rename(columns={0: 'Local'}),
        pd.DataFrame(marcadorLAS).rename(columns={0: 'Goles_L'}),
        pd.DataFrame(SeleccionVS).rename(columns={0: 'Visitante'}),
        pd.DataFrame(marcadorVAS).rename(columns={0: 'Goles_V'}),
        pd.DataFrame(PuntosLAS).rename(columns={0: 'PuntosL'}),
        pd.DataFrame(PuntosVAS).rename(columns={0: 'PuntosV'}),
        pd.DataFrame(IndicadorAS).rename(columns={0: 'Indicador'}),
        pd.DataFrame(faseS).rename(columns={0: 'Fase'})
    ], axis=1)
    df_resultados_16 = df_resultados_16.tail(16)

    ## Ajustar el orden de los duelos
    df_resultados_16a = pd.merge(
        df_resultados_16,
        m16.sort_values(by='ID', ascending=True),
        left_index=True,
        right_index=True,
        how='left',
        suffixes=('_left', '_right')
    ).sort_values(by='ID', ascending=True).reset_index().drop(
        ['Home', 'Away', 'Visitante_u', 'Fase_right', 'Local_right', 'ID', 'index','indx'], 
        axis=1
    ).rename(columns={'Local_left': 'Local', 'Fase_left': 'Fase'})

    ## CALCULAMOS LOS RESULTADOS DE LA SEGUNDA FASE [8VOS]:

    m8 = second_phase.second_phase_8(df_resultados_16.tail(16).reset_index())

    marcadorVA8, marcadorLA8, SeleccionV8, SeleccionL8, PuntosLA8, PuntosVA8, IndicadorA8, fase8 = \
        match_iterator_FIXED.match_iterator(data_g, m8, P, centroids,modo)
    
    df_resultados_8 = pd.concat([
        pd.DataFrame(SeleccionL8).rename(columns={0: 'Local'}),
        pd.DataFrame(marcadorLA8).rename(columns={0: 'Goles_L'}),
        pd.DataFrame(SeleccionV8).rename(columns={0: 'Visitante'}),
        pd.DataFrame(marcadorVA8).rename(columns={0: 'Goles_V'}),
        pd.DataFrame(PuntosLA8).rename(columns={0: 'PuntosL'}),
        pd.DataFrame(PuntosVA8).rename(columns={0: 'PuntosV'}),
        pd.DataFrame(IndicadorA8).rename(columns={0: 'Indicador'}),
        pd.DataFrame(fase8).rename(columns={0: 'Fase'})
    ], axis=1)
    df_resultados_8 = df_resultados_8.tail(8)

    ## CALCULAMOS LOS RESULTADOS DE LA SEGUNDA FASE [4TOS]:

    m4 = second_phase.second_phase_8(df_resultados_8.tail(8).reset_index())

    marcadorVA4, marcadorLA4, SeleccionV4, SeleccionL4, PuntosLA4, PuntosVA4, IndicadorA4, fase4 = \
        match_iterator_FIXED.match_iterator(data_g, m4, P, centroids,modo)
    
    df_resultados_4 = pd.concat([
        pd.DataFrame(SeleccionL4).rename(columns={0: 'Local'}),
        pd.DataFrame(marcadorLA4).rename(columns={0: 'Goles_L'}),
        pd.DataFrame(SeleccionV4).rename(columns={0: 'Visitante'}),
        pd.DataFrame(marcadorVA4).rename(columns={0: 'Goles_V'}),
        pd.DataFrame(PuntosLA4).rename(columns={0: 'PuntosL'}),
        pd.DataFrame(PuntosVA4).rename(columns={0: 'PuntosV'}),
        pd.DataFrame(IndicadorA4).rename(columns={0: 'Indicador'}),
        pd.DataFrame(fase4).rename(columns={0: 'Fase'})
    ], axis=1)
    df_resultados_4 = df_resultados_4.tail(4)

    ## CALCULAMOS LOS RESULTADOS DE LA SEGUNDA FASE [SEMI]:

    ms = second_phase.second_phase_8(df_resultados_4.tail(4).reset_index())

    marcadorVA2, marcadorLA2, SeleccionV2, SeleccionL2, PuntosLA2, PuntosVA2, IndicadorA2, fase2 = \
        match_iterator_FIXED.match_iterator(data_g, ms, P, centroids,modo)
    
    df_resultados_2 = pd.concat([
        pd.DataFrame(SeleccionL2).rename(columns={0: 'Local'}),
        pd.DataFrame(marcadorLA2).rename(columns={0: 'Goles_L'}),
        pd.DataFrame(SeleccionV2).rename(columns={0: 'Visitante'}),
        pd.DataFrame(marcadorVA2).rename(columns={0: 'Goles_V'}),
        pd.DataFrame(PuntosLA2).rename(columns={0: 'PuntosL'}),
        pd.DataFrame(PuntosVA2).rename(columns={0: 'PuntosV'}),
        pd.DataFrame(IndicadorA2).rename(columns={0: 'Indicador'}),
        pd.DataFrame(fase2).rename(columns={0: 'Fase'})
    ], axis=1)
    df_resultados_2 = df_resultados_2.tail(2)

    ## CALCULAMOS LOS RESULTADOS DE LA SEGUNDA FASE [FINAL y 3ro]:

    mf = second_phase.second_phase_8(df_resultados_2.tail(2).reset_index())

    ## Definimos la matriz de rivales de 3RO
    m3s = pd.DataFrame(pd.concat([ms['Home'], ms['Away']])).reset_index()
    m3f = pd.DataFrame(pd.concat([mf['Home'], mf['Away']])).reset_index()
    m3 = pd.merge(m3s, m3f, left_on=0, right_on=0, how='left', suffixes=('_left', '_right'))
    m3 = m3[m3['index_right'] != 0].drop(['index_right', 'index_left'], axis=1)
    m3['Home'] = m3[0].head(1)
    m3['Away'] = m3[0].tail(1)
    m3 = pd.DataFrame({col: m3[col].dropna().reset_index(drop=True) for col in m3}).drop([0], axis=1).head(1)
    fila = m3.loc[0]
    m3 = pd.concat([m3, fila.to_frame().T], ignore_index=True)
    m3 = pd.concat([m3, fila.to_frame().T], ignore_index=True)

    marcadorVA3, marcadorLA3, SeleccionV3, SeleccionL3, PuntosLA3, PuntosVA3, IndicadorA3, fase3 = \
        match_iterator_FIXED.match_iterator(data_g, m3, P, centroids,modo)
    
    df_resultados_3 = pd.concat([
        pd.DataFrame(SeleccionL3).rename(columns={0: 'Local'}),
        pd.DataFrame(marcadorLA3).rename(columns={0: 'Goles_L'}),
        pd.DataFrame(SeleccionV3).rename(columns={0: 'Visitante'}),
        pd.DataFrame(marcadorVA3).rename(columns={0: 'Goles_V'}),
        pd.DataFrame(PuntosLA3).rename(columns={0: 'PuntosL'}),
        pd.DataFrame(PuntosVA3).rename(columns={0: 'PuntosV'}),
        pd.DataFrame(IndicadorA3).rename(columns={0: 'Indicador'}),
        pd.DataFrame(fase3).rename(columns={0: 'Fase'})
    ], axis=1)
    df_resultados_3 = df_resultados_3.tail(1)

    marcadorVAf, marcadorLAf, SeleccionVf, SeleccionLf, PuntosLAf, PuntosVAf, IndicadorAf, fasef = \
        match_iterator_FIXED.match_iterator(data_g, mf, P, centroids,modo)
    
    df_resultados_f = pd.concat([
        pd.DataFrame(SeleccionLf).rename(columns={0: 'Local'}),
        pd.DataFrame(marcadorLAf).rename(columns={0: 'Goles_L'}),
        pd.DataFrame(SeleccionVf).rename(columns={0: 'Visitante'}),
        pd.DataFrame(marcadorVAf).rename(columns={0: 'Goles_V'}),
        pd.DataFrame(PuntosLAf).rename(columns={0: 'PuntosL'}),
        pd.DataFrame(PuntosVAf).rename(columns={0: 'PuntosV'}),
        pd.DataFrame(IndicadorAf).rename(columns={0: 'Indicador'}),
        pd.DataFrame(fasef).rename(columns={0: 'Fase'})
    ], axis=1)
    df_resultados_f = df_resultados_f.tail(1)

    df_tot = pd.concat([
        df_resultados,
        df_resultados_16a,
        df_resultados_8,
        df_resultados_4,
        df_resultados_2,
        df_resultados_3,
        df_resultados_f
    ], ignore_index=True)
    
    df_tot = pd.merge(
        df_tot,
        df_match_place,
        left_index=True,
        right_index=True,
        how='left'
    )
    df_norm= pd.concat([pd.DataFrame(df_tot[['Local','Goles_L','PuntosL','Indicador','Fase','Partido','Lugar']]).rename(columns={'Local':'S','Goles_L':'G','PuntosL':'P'}).assign(E='Local'), pd.DataFrame(df_tot[['Visitante','Goles_V','PuntosV','Indicador','Fase','Partido','Lugar']]).rename(columns={'Visitante':'S','Goles_V':'G','PuntosV':'P'}).assign(E='Visitante')], axis=0, ignore_index=True)
    
    return df_tot, df_resultados_3, df_analisis, df_dir, df_3ros,df_norm
