import datetime
import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px  # Librería para las gráficas interactivas
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
        
# ==========================================
# CONFIGURACIÓN DE LA PÁGINA WEB
# ==========================================
# Cambiamos el layout a "wide" (ancho) para que las gráficas del municipio se vean perfectas en pantalla
st.set_page_config(page_title="METEO DEIVID", page_icon="⛈️", layout="wide")

st.title("⛈️ MODELO METEOZEN")
st.write(
    "¡Bienvenido! Aquí puedes ver los mapas y las predicciones locales de mi propio modelo meteorológico: MeteoZen. ¡Espero que te guste!⚠️ NOTA: Pese a que mi modelo puede ser fiable, siempre es recomendable contrastarlo con modelos globales (GFS/ECMWF) y con las previsiones de la AEMET. El modelo no es perfecto y puede cometer errores en las previsiones"
)

# Creamos las dos pestañas principales de la interfaz
tab_mapas, tab_municipios = st.tabs(["🗺️ Mapas Generales", "🔍 Predicción por Municipio"])

# ==========================================
# LÓGICA DINÁMICA DE FECHAS (Se queda arriba para que sirva a ambas pestañas)
# ==========================================
ruta_fecha = "fecha_run.txt"
if os.path.exists(ruta_fecha):
    with open(ruta_fecha, "r") as f:
        fecha_str = f.read().strip()
    fecha_base = datetime.datetime.strptime(fecha_str, "%d/%m/%Y %H:%M")
else:
    fecha_base = datetime.datetime.now().replace(
        hour=0, minute=0, second=0, microsecond=0
    )

fecha_inicio_prevision = fecha_base + datetime.timedelta(days=1)


# ==========================================
# PESTAÑA 1: MAPAS GENERALES (Tu código original intacto)
# ==========================================
with tab_mapas:
    OPCIONES = {
        "Radar de Reflectividad ⛈️": os.path.join("salida_radar", "radar_{:02d}.png"),
        "Temperatura a 2m 🌡️": os.path.join("salida_temperatura", "temperatura_{:02d}.png"),
        "Viento a 10m 💨": os.path.join("salida_viento", "viento_{:02d}.png"),
        "Lluvia Horaria 🌧️": os.path.join("salida_lluvia_horaria", "lluvia_{:02d}.png"),
        "Lluvia Acumulada 🌊": os.path.join("salida_lluvia_acumulada", "lluvia_acum_{:02d}.png"),
    }

    variable_seleccionada = st.selectbox(
        "Selecciona la variable a visualizar:", list(OPCIONES.keys()), key="var_mapas"
    )

    hora = st.slider(
        "Paso de tiempo (Hora de la simulación):",
        min_value=0,
        max_value=23,
        value=0,
        format="Hora %02d:00",
        key="slider_mapas"
    )

    fecha_mapa = fecha_inicio_prevision + datetime.timedelta(hours=hora + 2)

    st.subheader(
        f"📆 Mapa válido para el: {fecha_mapa.strftime('%d/%m/%Y a las %H:%M')} UTC+2"
    )

    plantilla_ruta = OPCIONES[variable_seleccionada]
    ruta_imagen = plantilla_ruta.format(hora)

    if os.path.exists(ruta_imagen):
         # Creamos 3 columnas: vacía (15%), centro para el mapa (70%), vacía (15%)
        # Puedes jugar con los números (ej. [0.2, 0.6, 0.2]) si lo quieres aún más estrecho
        col_izq, col_mapa, col_der = st.columns([0.15, 0.70, 0.15])
        
        with col_mapa:
            st.image(ruta_imagen, use_container_width=True)
    else:
        st.error(
            f"⚠️ No se encontró el mapa para la Hora {hora:02d}. Todavía no existen datos en el servidor."
        )

    st.info(
        "💡 Consejo: Usa el ratón o las flechas de dirección del teclado para desplazarte entre las horas."
    )


# ==========================================
# PESTAÑA 2: PREDICCIÓN POR MUNICIPIO (Buscador Local)
# ==========================================
with tab_municipios:
    st.header("🔍 Buscador de Predicción por Localidad")
    st.write("Consulta la evolución del tiempo directamente en tu municipio para las próximas 24 horas.")
    
    # Cargamos el archivo de localidades usando la caché de Streamlit
    @st.cache_data
    def cargar_localidades():
        if os.path.exists("localidades.csv"):
            nombres_columnas = ["Comunidad", "Provincia", "Localidad", "Latitud", "Longitud", "Altitud", "Id1", "Id2", "Id3"]
            return pd.read_csv("localidades.csv", sep=";", header=None, names=nombres_columnas, encoding="utf-8")
        return None

    df_pueblos = cargar_localidades()

    if df_pueblos is not None:
        # 1. EL BUSCADOR PRIMERO (Para que Python guarde el pueblo y sus coordenadas)
        lista_pueblos = sorted(df_pueblos["Localidad"].unique())
        pueblo_elegido = st.selectbox("Escribe o selecciona tu municipio:", lista_pueblos, key="selector_pueblo")
        
        # Extraemos las coordenadas inmediatamente
        datos_pueblo = df_pueblos[df_pueblos["Localidad"] == pueblo_elegido].iloc[0]
        lat_pueblo = datos_pueblo["Latitud"]
        lon_pueblo = datos_pueblo["Longitud"]
        provincia = datos_pueblo["Provincia"]
        altitud = datos_pueblo.get("Altitud", "N/A")
        
        st.markdown(f"### 📍 Pronóstico para: **{pueblo_elegido} ({provincia})** — *Altitud: {altitud} m*")
        
        st.write("---")
        
        # 2. EL MAPA INTERACTIVO DESPUÉS (Ahora ya conoce lat_pueblo y lon_pueblo)
        st.subheader("🗺️ Capa de Simulación Dinámica (Estilo Windy)")
        
        col_capa, col_hora = st.columns([1, 1])
        
        with col_capa:
            capa_seleccionada = st.selectbox(
                "Selecciona la capa del mapa:",
                ["Temperatura 🌡️", "Lluvia Horaria 🌧️", "Viento 💨"],
                key="capa_mapa_interactivo"
            )
            
        with col_hora:
            hora_mapa = st.slider(
                "Ver hora de la simulación:",
                min_value=0,
                max_value=23,
                value=0,
                format="Hora %02d:00",
                key="slider_mapa_interactivo"
            )
            
        fecha_mapa_interactivo = fecha_inicio_prevision + datetime.timedelta(hours=hora_mapa + 2)
        st.markdown(f"⏱️ **Mapa válido para el:** `{fecha_mapa_interactivo.strftime('%d/%m/%Y a las %H:%M')} UTC+2`")
        
        # 1. ACTUALIZADO: Apuntamos a tus carpetas de scripts independientes
        MAPA_CAPAS = {
            "Temperatura 🌡️": os.path.join("salida_temperatura_mapa", "temperatura_{:02d}.png"),
            "Lluvia Horaria 🌧️": os.path.join("salida_lluvia_horaria_mapa", "lluvia_{:02d}.png"),
            "Viento 💨": os.path.join("salida_viento_mapa", "viento_{:02d}.png"),
        }
        
        ruta_capa_img = MAPA_CAPAS[capa_seleccionada].format(hora_mapa)
        
        # 2. ACTUALIZADO: Límites geográficos clavados al milímetro con Matplotlib
        # [Latitud Mínima, Longitud Mínima], [Latitud Máxima, Longitud Máxima]
        limites_mapa = [[35.0, -10.0], [44.5, 4.5]] 
        
        # Mapa base oscuro estilo Windy
        m = folium.Map(location=[37.8882, -4.7794], zoom_start=7, tiles="CartoDB dark_matter")
        
        # 3. Superponer la imagen limpia y transparente
        if os.path.exists(ruta_capa_img):
            folium.raster_layers.ImageOverlay(
                image=ruta_capa_img,
                bounds=limites_mapa,
                opacity=0.6,          # Transparencia de la mancha de color
                interactive=True,
                cross_origin=False
            ).add_to(m)
        else:
            st.caption("⚠️ Capa de simulación transparente no disponible para esta hora. Ejecuta tus scripts *_mapa.py primero.")
        
        # Marcador del pueblo seleccionado
        folium.Marker(
            location=[lat_pueblo, lon_pueblo],
            popup=f"📍 {pueblo_elegido}",
            icon=folium.Icon(color="red", icon="info-sign")
        ).add_to(m)
        
        # Renderizar en la web
        st_folium(m, width="100%", height=500, key="mapa_windy_render")
