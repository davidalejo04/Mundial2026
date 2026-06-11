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
        print(df_match)
    else:
        
        df_match=df_match
    
    


    for j in range(indx,indx+qty): 

        if (data_dic[data_dic['Selección']==df_match.loc[j-indx]['Home']]['Tipo_Ventaja']).tolist()[0]=='N' and (data_dic[data_dic['Selección']==df_match.loc[j-indx]['Away']]['Tipo_Ventaja']).tolist()[0]=='N':
            

            print(j-indx,j+1," ",df_match.loc[j-indx]['Home'],df_match.loc[j-indx]['Away']," ",df_match_place.iloc[j]['Lugar']," ",1)
            filas_idx = df_match.index[j-indx]
            columnas = ['Home', 'Away']
            columnas_swap = ['Away', 'Home']
            df_match.loc[filas_idx, columnas] = df_match.loc[filas_idx, columnas].to_numpy()
            I_P='Away'

        elif (df_match_place.iloc[j]['Lugar'])==(data_dic[data_dic['Selección']==df_match.loc[j-indx]['Away']]['Tipo_Ventaja']).tolist()[0] and (df_match_place.iloc[j]['Lugar'])==(data_dic[data_dic['Selección']==df_match.loc[j-indx]['Home']]['Tipo_Ventaja']).tolist()[0]:
            
            print(j-indx,j+1," ",df_match.loc[j-indx]['Home'],df_match.loc[j-indx]['Away']," ",df_match_place.iloc[j]['Lugar']," ",2)
            filas_idx = df_match.index[j-indx]
            columnas = ['Home', 'Away']
            columnas_swap = ['Away', 'Home']
            df_match.loc[filas_idx, columnas] = df_match.loc[filas_idx, columnas].to_numpy()
            I_P='Home'


        elif (df_match_place.iloc[j]['Lugar'])==(data_dic[data_dic['Selección']==df_match.loc[j-indx]['Home']]['Tipo_Ventaja']).tolist()[0] and (df_match_place.iloc[j]['Lugar'])!=(data_dic[data_dic['Selección']==df_match.loc[j-indx]['Away']]['Tipo_Ventaja']).tolist()[0]:
            print(j-indx,j+1," ",df_match.loc[j-indx]['Home'],df_match.loc[j-indx]['Away']," ",df_match_place.iloc[j]['Lugar']," ",3)
            filas_idx = df_match.index[j-indx]
            columnas = ['Home', 'Away']
            columnas_swap = ['Away', 'Home']
            df_match.loc[filas_idx, columnas] = df_match.loc[filas_idx, columnas].to_numpy()
            I_P='None'


        elif (df_match_place.iloc[j]['Lugar'])==(data_dic[data_dic['Selección']==df_match.loc[j-indx]['Away']]['Tipo_Ventaja']).tolist()[0] and ((df_match_place.iloc[j]['Lugar'])!=(data_dic[data_dic['Selección']==df_match.loc[j-indx]['Home']]['Tipo_Ventaja']).tolist()[0] or (data_dic[data_dic['Selección']==df_match.loc[j-indx]['Home']]['Tipo_Ventaja']).tolist()[0]=='N' ):

            print(j-indx,j+1," ",df_match.loc[j-indx]['Home'],df_match.loc[j-indx]['Away']," ",df_match_place.iloc[j]['Lugar']," ",4)
            #print(df_match.iloc[j-indx]['Home'],df_match.iloc[j-indx]['Away'])
            filas_idx = df_match.index[j-indx]
            columnas = ['Home', 'Away']
            columnas_swap = ['Away', 'Home']
            df_match.loc[filas_idx, columnas] = df_match.loc[filas_idx, columnas_swap].to_numpy()
            print(j-indx,j+1," ",df_match.loc[j-indx]['Home'],df_match.loc[j-indx]['Away']," ",df_match_place.iloc[j]['Lugar']," ",4)
            I_P='None'

        else:

            print(j-indx,j+1," ",df_match.loc[j-indx]['Home'],df_match.loc[j-indx]['Away']," ",df_match_place.iloc[j]['Lugar']," ",5)
            filas_idx = df_match.index[j-indx]
            columnas = ['Home', 'Away']
            columnas_swap = ['Away', 'Home']
            df_match.loc[filas_idx, columnas] = df_match.loc[filas_idx, columnas].to_numpy()
            I_P='None'


        #filas_idx = df_match.index[j-indx]
        #columnas = ['Home', 'Away']
        #columnas_swap = ['Away', 'Home']
        #df_match.loc[filas_idx, columnas] = df_match.loc[filas_idx, columnas].to_numpy()
        I_P_A.append(I_P)
    if qty==16:
     df_match=(df_match.reset_index(drop=True))
    else:
        
     df_match=df_match


    
    return pd.DataFrame(df_match),I_P_A