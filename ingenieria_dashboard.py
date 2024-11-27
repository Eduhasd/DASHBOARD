import streamlit as st
import pandas as pd
import requests

import subprocess
import sys

try:
    import matplotlib.pyplot as plt
    print("matplotlib está instalado correctamente.")
except ImportError:
    print("matplotlib no está instalado. Procediendo a la instalación...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "matplotlib"])
    
import matplotlib.dates as mdates

# Título del dashboard
st.title('Dashboard Climático Global: Datos Actuales y Pronóstico a 5 Días')

# API Key
api_key = "ee0cf905482aa924fb952ad10e89b753"

# Ciudades seleccionadas (distintos continentes)
ciudades = {
    "Nueva York": {"lat": 40.7128, "lon": -74.0060},
    "Londres": {"lat": 51.5074, "lon": -0.1278},
    "Tokio": {"lat": 35.6895, "lon": 139.6917},
    "Sídney": {"lat": -33.8688, "lon": 151.2093},
    "Ciudad del Cabo": {"lat": -33.9249, "lon": 18.4241},
    "Concepción": {"lat": -36.8269, "lon": -73.0497},
}

# Sidebar: Selección de filtros
st.sidebar.header("Configuración de Filtros")

# 1. Seleccionar ciudad
ciudad_seleccionada = st.sidebar.selectbox('Selecciona una ciudad', list(ciudades.keys()))
lat, lon = ciudades[ciudad_seleccionada]['lat'], ciudades[ciudad_seleccionada]['lon']

# 2. Seleccionar tipo de datos
tipo_datos = st.sidebar.radio('Selecciona el tipo de datos', ['Actuales', 'Pronóstico a 5 días'])

# Mostrar datos actuales o pronóstico a 5 días
if tipo_datos == 'Actuales':
    st.subheader(f"Datos Climáticos Actuales: {ciudad_seleccionada}")
    
    url_actual = "http://api.openweathermap.org/data/2.5/weather"
    params_actual = {
        "lat": lat,
        "lon": lon,
        "appid": api_key,
        "units": "metric",
    }
    
    response_actual = requests.get(url_actual, params=params_actual)
    data_actual = response_actual.json()
    
    if response_actual.status_code == 200:
        st.metric("Temperatura Actual (°C)", data_actual['main']['temp'])
        st.metric("Humedad (%)", data_actual['main']['humidity'])
        st.metric("Velocidad del viento (m/s)", data_actual['wind']['speed'])
        st.metric("Precipitaciones (mm)", data_actual.get('rain', {}).get('1h', 0))
        st.metric("Dirección del viento (°)", data_actual['wind']['deg'])
    else:
        st.error("No se pudieron obtener los datos actuales.")
else:
    st.subheader(f"Pronóstico Climático a 5 Días: {ciudad_seleccionada}")
    
    url_forecast = "https://api.openweathermap.org/data/2.5/forecast"
    params_forecast = {
        "lat": lat,
        "lon": lon,
        "appid": api_key,
        "units": "metric"
    }
    
    response_forecast = requests.get(url_forecast, params=params_forecast)
    data_forecast = response_forecast.json()
    
    if response_forecast.status_code == 200 and "list" in data_forecast:
        df_forecast = pd.DataFrame(data_forecast['list'])
        df_forecast['datetime'] = pd.to_datetime(df_forecast['dt_txt'])
        
        # Extraer las columnas deseadas
        df_forecast['temp'] = df_forecast['main'].apply(lambda x: x['temp'])
        df_forecast['humidity'] = df_forecast['main'].apply(lambda x: x['humidity'])
        df_forecast['wind_speed'] = df_forecast['wind'].apply(lambda x: x['speed'])
        df_forecast['wind_deg'] = df_forecast['wind'].apply(lambda x: x['deg'])
        
        # Aquí es donde debes agregar la verificación de lluvia:
        # Verifica si la clave 'rain' existe antes de acceder a ella
        df_forecast['rain'] = df_forecast.apply(
    lambda row: row['rain'].get('3h', 0) if isinstance(row.get('rain'), dict) else 0, axis=1
)

        # Filtrar datos en intervalos de 3 horas
        df_forecast = df_forecast[df_forecast['datetime'].dt.hour % 3 == 0]
        
        # Métricas y sus etiquetas
        metricas = {
            'Temperatura (°C)': 'temp',
            'Humedad (%)': 'humidity',
            'Velocidad del viento (m/s)': 'wind_speed',
            'Precipitaciones (mm)': 'rain',
            'Dirección del viento (°)': 'wind_deg'
        }

        for nombre_metrica, columna in metricas.items():
            st.subheader(f'{nombre_metrica}')
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(df_forecast['datetime'], df_forecast[columna], label=nombre_metrica)
            ax.set_title(f'{nombre_metrica} en {ciudad_seleccionada}')
            ax.set_xlabel('Fecha y Hora')
            ax.set_ylabel(nombre_metrica)
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))  # Formato sin año
            plt.xticks(rotation=45)
            ax.legend()
            st.pyplot(fig)
    else:
        st.error("No se pudieron obtener los datos del pronóstico.")
