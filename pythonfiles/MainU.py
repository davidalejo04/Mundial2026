import pandas as pd
import clusters3
import simulacion_FIXED
import time
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')


df_resultados_f_A=[]
df_analisis_A=[]
df_dir_A=[]
df_3ros_A=[]
df_3_A=[]
df_norm_A=[]

join_df_f=clusters3.clusters3()[0]
centroids=clusters3.clusters3()[1]



while True:
    modo = input("Selecciona opción válida, deseas ver; ¿marcador mas probable (p), simulación montecarlo (m)? (p/m): ").lower()
    
    if modo == 'm' or modo == 'p':
        break  

if modo == 'm':
    while True:
        try:
            
            cantidad_simulaciones = int(input("Ingresa la cantidad de simulaciones (número entero): "))
            
            
            if cantidad_simulaciones > 0:
                break
            else:
                print("Por favor, ingresa un número mayor a cero.")
                
        except ValueError:
            
            print("Error: Entrada no válida. Debes ingresar un número entero sin letras.")

    print(f"Has ingresado un número válido: {cantidad_simulaciones}")

elif modo == 'p':
    cantidad_simulaciones = 1
    


 

for i in tqdm(range(cantidad_simulaciones)):

    if i<cantidad_simulaciones-1:

        modo='m'

        #df_resultados_f,df_resultados_3,df_analisis,df_dir,df_3ros,df_norm=simulacion_FIXED.simulacion(join_df_f,centroids)
        res=simulacion_FIXED.simulacion(join_df_f,centroids,modo)
    else:
        print("llegamos aca")
        modo='p'
        res=simulacion_FIXED.simulacion(join_df_f,centroids,modo)



    df_resultados_f=res[0].copy()
    df_resultados_3=res[1].copy()
    df_analisis=res[2].copy()
    df_dir=res[3].copy()
    df_3ros=res[4].copy()
    df_norm=res[5].copy()


    df_resultados_f['simulacion']=i
    df_resultados_3['simulacion']=i
    df_analisis['simulacion']=i
    df_dir['simulacion']=i
    df_3ros['simulacion']=i
    df_norm['simulacion']=i


    df_resultados_f_A.append(df_resultados_f)
    df_3_A.append(df_resultados_3)
    df_analisis_A.append(df_analisis)
    df_dir_A.append(df_dir)
    df_3ros_A.append(df_3ros)
    df_norm_A.append(df_norm)

        
time.sleep(0.01)
df_resultados_f_F = pd.DataFrame(pd.concat(df_resultados_f_A))
df_3_f_F=pd.DataFrame(pd.concat(df_3_A))
df_analisis_f_F = pd.DataFrame(pd.concat(df_analisis_A))
df_dir_f_F = pd.DataFrame(pd.concat(df_dir_A))
df_3ros_f_F = pd.DataFrame(pd.concat(df_3ros_A))
df_norm_f_F=pd.DataFrame(pd.concat(df_norm_A))
df_resultados_f_M = df_resultados_f_F[df_resultados_f_F['simulacion'] == df_resultados_f_F['simulacion'].max()]


resultadosF=pd.DataFrame(df_norm_f_F)
#print(df_resultados_f_F)
resultadosF.to_excel('NORMDEF3.xlsx', index=False)
AnalisisF=pd.DataFrame(df_analisis_f_F)
#print(df_analisis_f_F)
AnalisisF.to_excel('ANADEF3.xlsx', index=False)
ResultadosF=pd.DataFrame(df_resultados_f_F)
#print(df_analisis_f_F)
ResultadosF.to_excel('PRIDEF3.xlsx', index=False)
ResultadosM=pd.DataFrame(df_resultados_f_M)
ResultadosM.to_excel('RESDEF3.xlsx', index=False)

