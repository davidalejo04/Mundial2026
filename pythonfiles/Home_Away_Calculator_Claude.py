import pandas as pd

df_match_place=pd.read_excel('C:/Users/david/2026/v2/Match_Places.xlsx',sheet_name='Hoja1')
df_match_place=pd.DataFrame(df_match_place)
data_dic=pd.read_excel("C:/Users/david/2026/v2/EstudioEstadisticoMundial.xlsx",sheet_name="Hoja1")
data_dic=pd.DataFrame(data_dic)
loc=df_match_place.shape[0]


def Home_Away_Calculator(qty,df_match):
    I_P_A=[]   
    
    if qty==3:
       indx=102
       qty=1
    elif qty==1:
       indx=103
       qty=1
    else:
     indx=loc-(qty*2)
    if qty==16:
        df_match['indx']=(df_match.reset_index())['ID']-(indx+1)
        df_match=df_match.reset_index(drop=True).set_index('indx',inplace=False)
    else:
        
        df_match=df_match
    
    


    for j in range(indx,indx+qty): 

        #filas_idx = df_match.index[j - indx]
        filas_idx=j-indx
        columnas      = ['Home', 'Away']
        columnas_swap = ['Away', 'Home']

        home_ventaja = (data_dic[data_dic['Selección'] == df_match.loc[j - indx]['Home']]['Tipo_Ventaja']).tolist()[0]
        away_ventaja = (data_dic[data_dic['Selección'] == df_match.loc[j - indx]['Away']]['Tipo_Ventaja']).tolist()[0]
        lugar        = df_match_place.iloc[j]['Lugar']

        if home_ventaja == 'N' and away_ventaja == 'N':
            # Ambos neutros — no hay ventaja de local, no se hace swap
            #print(j - indx, j + 1,filas_idx,qty, " ", df_match.loc[j - indx]['Home'], df_match.loc[j - indx]['Away'], " ", lugar, " ", 1)
            I_P = 'Away'

        elif lugar == away_ventaja and lugar == home_ventaja:
            # Los dos tienen ventaja en este lugar — no se hace swap
            #print(j - indx, j + 1,filas_idx,qty, " ", df_match.loc[j - indx]['Home'], df_match.loc[j - indx]['Away'], " ", lugar, " ", 2)
            I_P = 'Home'

        elif lugar == home_ventaja and lugar != away_ventaja:
            # Home ya tiene ventaja → no hay swap necesario
            #print(j - indx, j + 1,filas_idx,qty, " ", df_match.loc[j - indx]['Home'], df_match.loc[j - indx]['Away'], " ", lugar, " ", 3)
            I_P = 'None'

        elif lugar == away_ventaja and (lugar != home_ventaja or home_ventaja == 'N'):
            # Away tiene ventaja → SWAP: Away pasa a ser Home
            #print(j - indx, j + 1,filas_idx,qty, " ", df_match.loc[j - indx]['Home'], df_match.loc[j - indx]['Away'], " ", lugar, " ", 4)
            df_match.loc[filas_idx, columnas]  = df_match.loc[filas_idx, columnas_swap].to_numpy()
            #print(j - indx, j + 1,filas_idx,qty, " ", df_match.loc[j - indx]['Home'], df_match.loc[j - indx]['Away'], " ", lugar, " ", 4)
            I_P = 'None'

        else:
            #print(j - indx, j + 1,filas_idx,qty, " ", df_match.loc[j - indx]['Home'], df_match.loc[j - indx]['Away'], " ", lugar, " ", 5)
            I_P = 'None'

        I_P_A.append(I_P)

    if qty==16:
     df_match=(df_match.reset_index(drop=True))
    else:
        
     df_match=df_match


    
    return pd.DataFrame(df_match),I_P_A