import pandas as pd

spsm=pd.read_excel("C:/Users/david/2026/v2/Second_Phase_Sort_Matrix.xlsx",sheet_name="Hoja2")
data_match_second=pd.read_excel("C:/Users/david/2026/v2/Matches_Groups_Second_Phase.xlsx",sheet_name="Hoja1")
df_spsm=pd.DataFrame(spsm)
df_data_match_second=pd.DataFrame(data_match_second)


gp_key={'Group':['A','B','C','D','E','F','G','H','I','J','K','L'],'Key':[2,3,5,7,11,13,17,19,23,29,31,37],'3Group':['3A','3B','3C','3D','3E','3F','3G','3H','3I','3J','3K','3L']}
df_gp_key=pd.DataFrame(gp_key)


## 16VOS

def second_phase_16(data1,data2):

        data1=data1.copy()
        
        data2=data2.copy()

        #data1['key']=data1['Pos'].astype(str).copy()+data1['Grupo'].copy()
        #data2['key']=data2['Pos'].astype(str).copy()+data2['Grupo'].copy()

        data1.loc[:,'key']=data1['Pos'].copy().astype(str)+data1['Grupo'].copy()
        data2.loc[:,'key']=data2['Pos'].copy().astype(str)+data2['Grupo'].copy()



        dataF=pd.concat([data1,data2], ignore_index=True)
        columna=['key']
        df_data2 = data2[columna]
        df_data2_K=pd.merge(df_data2,df_gp_key,
                left_on='key',
                right_on='3Group',
                how='left').reset_index().drop(['key','Group','3Group','index'], axis=1).T
        df_data2_K['Result'] = df_data2_K[0] * df_data2_K[1] * df_data2_K[2]* df_data2_K[3] * df_data2_K[4]* df_data2_K[5] * df_data2_K[6]* df_data2_K[7]
        df_spsm1=pd.DataFrame(pd.merge(df_data2_K,df_spsm,
                left_on='Result',
                right_on='Key',
                how='left',suffixes=('_left', '_right')).drop([0,1,2,3,4,5,6,7,'Result','Key'], axis=1).T).reset_index()
        
        data_match_second1=pd.merge(data_match_second,df_spsm1,
                left_on='Local',
                right_on='index',
                how='left',suffixes=('_left', '_right')).drop(['index'], axis=1)
        data_match_second1['Visitante_u']=data_match_second1['Visitante'].fillna('')+data_match_second1[0].fillna('')

        data_match_second2=pd.merge(pd.merge(data_match_second1,dataF,
                left_on='Local',
                right_on='key',
                how='left',suffixes=('_left', '_right')),dataF,
                left_on='Visitante_u',
                right_on='key',how='left').drop(['Pos_y','num_y','Dif_y','Puntos_y','GolesC_y','GolesF_y','Grupo_y','index_y','Pos_x','num_x','Dif_x','Puntos_x','GolesC_x','GolesF_x','Grupo_x','index_x',0,'Visitante','key_x','key_y'],axis=1).rename(columns={'Seleccion_x': 'Home', 'Seleccion_y': 'Away'})                            

        return data_match_second2

## 8VOS, 4TOS, SEMI, FINAL

def second_phase_8(data3):
        data4h=[]
        data4a=[]
        data5a=[]
        data5h=[]

        

        for j in range(0,data3.shape[0],2):

         if data3.iloc[j]['PuntosL'] > data3.iloc[j]['PuntosV']:
               data4h=data3.iloc[j]['Local']

               if data3.iloc[j+1]['PuntosL'] > data3.iloc[j+1]['PuntosV']:
                     data4a=data3.iloc[j+1]['Local']

               else:
                     data4a=data3.iloc[j+1]['Visitante']

         else:
               data4h=data3.iloc[j]['Visitante']

               if data3.iloc[j+1]['PuntosL'] > data3.iloc[j+1]['PuntosV']:
                     data4a=data3.iloc[j+1]['Local']

               else:
                     data4a=data3.iloc[j+1]['Visitante']

  
         data5a.append(data4a)
         data5h.append(data4h)
        
        
        data6 = {"Home": data5h, "Away": data5a}
        data6=pd.DataFrame(data6)
        

        return data6