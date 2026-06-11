import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
from scipy.stats import norm, kstest
import pylab
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import plotly.express as px
import plotly.express.colors as px_colors 

## Leemos y limpiamos los datos

opcion = input("¿Deseas ver los gráficos en un solo cuadro? (s/n): ").lower()
df_stars_c = pd.read_excel("C:/Users/david/2026/mi_dataframe.xlsx",sheet_name="Sheet1")
df_stars_1 = pd.read_excel("C:/Users/david/2026/v2/TeamStats.xlsx",sheet_name="Hoja1")
df_stars_1=pd.DataFrame(df_stars_1)
df_stars_c=pd.DataFrame(df_stars_c)
df_stars_1=df_stars_1.join(df_stars_c, lsuffix='_le', rsuffix='_r')
slim_df = df_stars_1[(~df_stars_1['Selección_le'].isin(['Liechtenstein', 'Sudán','Somalia','Barbados','Vanuatu','Fiyi','Tailandia','Mozambique']) ) ].drop(['Cluster_Label', 'SHO', 'PAS', 'DRI','OVR'], axis=1)
#,'OVR', 'SHO', 'PAS', 'DRI'
dataset_size = df_stars_1.shape[0]


slim_df2 = slim_df.reset_index()
slim_df = slim_df.drop(['Selección_le','Selección_r'], axis=1)
variable_list = [ 'PAC', 'DEF','ATK','PRS']

## Creamos graficas evaluativas
if opcion=='s':
    fig, ax = plt.subplots(4, 2, figsize=(12, 64))
    for idx, variable in enumerate(variable_list):
        axes_hist = ax[idx][0]
        axes_box  = ax[idx][1]
        sns.histplot(data=slim_df, x=variable, ax=axes_hist)
        sns.boxplot(data=slim_df, y=variable, ax=axes_box)

    plt.style.use('dark_background')
    plt.show()
else:
    print("se omitio graficas evaluativas")


## analizamos normalidad

if opcion=='s':

    fig2, ax2 = plt.subplots(4, 2, figsize=(8, 12))

    for idx2, variable in enumerate(variable_list):
        if idx2 % 2 == 0:
            ax = ax2[int(idx2/2)][0]
        else:
            ax = ax2[int(idx2/2)][1]
        sm.qqplot(slim_df[variable], line='45', ax=ax)
    
    plt.style.use('dark_background')
    plt.show()

else:
    print("se omitio graficas de normalidad")

for variable in variable_list:
    ks_statistic, p_value = kstest(slim_df[variable], 'norm')
    if p_value < 0.05:
        print(f'La variable: "{variable}", tiene un p-value para el test de Kolmogorov-Smirnov de: {p_value}, así que asumimos que la distribución no es normal')
    else:
        print(f'La variable: "{variable}", tiene un p-value para el test de Kolmogorov-Smirnov de: {p_value}, así que asumimos que la distribución es normal')

## realizamos transformacion de variables

scaler = StandardScaler()
scaled_array = scaler.fit_transform(slim_df)

scaled_df = pd.DataFrame(scaled_array, columns=slim_df.columns)

if opcion=='s':

    sns.pairplot(data=scaled_df)
    plt.style.use('dark_background')
    plt.show()
else:
    print("se omitio graficas de pairplot")
    

## aplicamos kmeans

kmeans = KMeans(n_clusters=7, random_state=42, init='k-means++', n_init=10)
kmeans.fit(scaled_df)

scaled_df['Cluster_Label'] = kmeans.predict(scaled_df)
scaled_df=pd.DataFrame(scaled_df)
join_df=scaled_df.join(slim_df2,lsuffix='_l', rsuffix='_r')

      
# 4. Visualization in 3D

fig = plt.figure(figsize=(4, 6))
ax = fig.add_subplot(111, projection='3d')

# Scatter plot for each cluster
cluster_colors = ['#00FF41', '#FF6B35', '#00D4FF', '#FFD700', '#FF00FF', '#FF4444', '#ADFF2F']
#cluster_colors = ['#00FF41', '#FF6B35', '#00D4FF', '#FFD700', '#FF00FF', '#FF4444']
#cluster_colors = ['#00FF41', '#FF6B35', '#00D4FF', '#FFD700']
for i, cluster in enumerate(sorted(join_df['Cluster_Label'].unique())):
    subset = join_df[join_df['Cluster_Label'] == cluster]
    color = cluster_colors[i % len(cluster_colors)]
    ax.scatter(subset['PRS_r'], subset['DEF_r'], subset['ATK_r'],
               label=f'Cluster {cluster}',
               c=color,
               s=60,
               alpha=0.85,
               edgecolors='white',
               linewidths=0.3)
    for xi, yi, zi, label in zip(subset['PRS_r'], subset['DEF_r'], subset['ATK_r'], subset['Selección_r']):
        ax.text(xi, yi, zi, label, color=color, fontsize=7)

# Centroids
centroids_scaled = kmeans.cluster_centers_
centroids_original = scaler.inverse_transform(centroids_scaled)
ax.scatter(centroids_original[:, 3], centroids_original[:, 1], centroids_original[:, 2],
           s=200, c='#FFFFFF', marker='x', linewidths=2.5, label='Centroids')

df_centroids_original = pd.DataFrame(centroids_original).rename(columns={0: 'PAC', 1: 'DEF', 2: 'ATK', 3: 'PRS'})

ax.set_xlabel('PRS', color='white')
ax.set_ylabel('DEF', color='white')
ax.set_zlabel('ATK', color='white')
ax.set_title('K-Means Clustering with 3 Variables', color='white')
ax.tick_params(colors='white')
ax.legend(facecolor='#1a1a1a', edgecolor='white', labelcolor='white')

if opcion=='s':
 plt.style.use('dark_background')
 plt.show()
else:
    print("se omitio graficas de clusters")


# 1. Definimos la paleta Cyberpunk
cyber_colors = yber_colors = ['#00F3FF', '#FF0055', '#F3EF00', '#00FF9F', '#9400FF', '#FF6100', '#ADFF2F']
#cyber_colors = yber_colors = ['#00F3FF', '#FF0055', '#F3EF00', '#00FF9F']

fig = px.scatter_3d(join_df,
    x='PRS_r', y='DEF_r', z='ATK_r', 
    color='Cluster_Label',
    text='Selección_r',
    template='plotly_dark',
    size='PAC_r',
    size_max=25,    
    color_discrete_sequence=cluster_colors
)

# 2. Tuning del estilo "Dark Space"
fig.update_layout(
    paper_bgcolor='black',  # Fondo exterior
    plot_bgcolor='black',   # Fondo del gráfico
    scene=dict(
        xaxis=dict(backgroundcolor="black", gridcolor="#1f1f1f", showbackground=True),
        yaxis=dict(backgroundcolor="black", gridcolor="#1f1f1f", showbackground=True),
        zaxis=dict(backgroundcolor="black", gridcolor="#1f1f1f", showbackground=True),
    ),
    title=dict(
        text="K-Means Clustering with 3 Variables",
        font=dict(family="Courier New", size=24, color='#00F3FF') # Fuente tipo terminal
    )
)

# 3. Hacer que los puntos "brillen"
fig.update_traces(
    textposition='top center',
    marker=dict(
        sizemode='diameter',
        opacity=0.9,
        line=dict(width=0.5, color='rgba(255, 255, 255, 0.3)') # Brillo perimetral
    ),

    selector=dict(mode='markers')
)
fig.update_traces(
    textposition='top center',
    textfont=dict(
        family="Courier New", # Fuente estilo terminal
        size=15,
        color='#00F3FF'      # Blanco puro para que resalte
    )
)
if opcion=='s':
    fig.show()
else:
    print("se omitio graficas de clusters mejorada")


cluster_sizes = list(range(1, 11))
inertias = {}

for n_clusters in cluster_sizes:
    kmeans_v = KMeans(n_clusters=n_clusters)
    kmeans_v.fit(scaled_df)
    inertia = kmeans_v.inertia_
    inertias[n_clusters] = inertia


if opcion=='s':
    plt.figure(figsize=(7, 6))
    plt.plot(inertias.keys(), inertias.values(), 'o-')
    pointsx = [7]

    for pointx in pointsx:
        inertia = inertias[pointx]
        plt.plot([pointx], [inertia], 'ro')
        
    plt.style.use('dark_background')
    plt.show()
else:
    print("se omitio graficas de codo")

def clusters3(): 
 join_df_f=join_df.drop(['PAC_r', 'DEF_r','ATK_r','PRS_r','PAC_l', 'DEF_l','ATK_l','PRS_l','Selección_le','index'], axis=1)
 return join_df_f,df_centroids_original