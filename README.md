# ⚽ Mundial 2026 — Simulación Dixon-Coles

Dashboard interactivo construido con **Streamlit** para visualizar las predicciones del Mundial 2026 usando el modelo estadístico **Dixon-Coles** con simulación **Monte Carlo**.

## 📊 Funcionalidades

- **Partidos**: Resultados más probables por fase y equipo
- **Rivales & Esperanzas**: Probabilidades de Victoria / Empate / Derrota por matchup
- **Tabla de Grupos**: Standings calculados dinámicamente desde la simulación
- **Grafo de Correlaciones**: Red de dependencias estocásticas entre partidos

## 🗂️ Archivos de datos

| Archivo | Descripción |
|---|---|
| `RESDEF3.xlsx` | Marcadores más probables (simulación determinista) |
| `PRIDEF3.xlsx` | Acervo Monte Carlo (N simulaciones) |
| `EstudioEstadisticoMundial.xlsx` | Grupos, confederaciones y valores de mercado |

## 🚀 Cómo correr localmente

```bash
pip install -r requirements.txt
streamlit run mundial_2026_app.py
```

## 🔗 Conexión a MS Fabric / OneLake

En `load_data()` dentro de `mundial_2026_app.py`, reemplaza `pd.read_excel` por:

```python
import pyodbc
conn = pyodbc.connect(
    "Driver={ODBC Driver 18 for SQL Server};"
    "Server=tu-servidor.datawarehouse.fabric.microsoft.com;"
    "Database=tu_lakehouse;"
    "Authentication=ActiveDirectoryInteractive"
)
df_res = pd.read_sql("SELECT * FROM dbo.RESDEF3", conn)
```

## 🧮 Modelo

- **Dixon-Coles** con corrección τ para marcadores bajos
- Ajuste de parámetros λ por fase del torneo (deflactor progresivo)
- Muestreo inverso sobre CDF conjunta normalizada
- Correlaciones de Pearson entre partidos via Monte Carlo

## 📦 Deploy en Streamlit Cloud

1. Fork este repositorio
2. Ve a [share.streamlit.io](https://share.streamlit.io)
3. Conecta tu repo y apunta a `mundial_2026_app.py`

---
*Modelo estadístico: Dixon & Coles (1997) — Applied Statistics*
