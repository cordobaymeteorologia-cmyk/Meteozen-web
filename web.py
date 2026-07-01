import datetime
import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px  # Librería para las gráficas interactivas

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
            # Definimos los nombres de las columnas que sabemos que tiene tu archivo
            nombres_columnas = ["Comunidad", "Provincia", "Localidad", "Latitud", "Longitud", "Altitud", "Id1", "Id2", "Id3"]
            
            # Leemos indicando header=None para que no use la fila de Abla como títulos, y le metemos nuestros nombres
            return pd.read_csv("localidades.csv", sep=";", header=None, names=nombres_columnas, encoding="utf-8")
        return None

    df_pueblos = cargar_localidades()

    if df_pueblos is not None:

	  # --- NUEVO: SECCIÓN MAPA INTERACTIVO ---
        st.subheader("🗺️ Mapa de Estaciones de Consulta")
        
        # Creamos el mapa centrado en España de fondo
        m = folium.Map(location=[40.4167, -3.7037], zoom_start=6, tiles="OpenStreetMap")
        
        # Filtramos una muestra o añadimos los pueblos principales para no saturar el navegador si son miles.
        # En este ejemplo añadimos todos, pero si notas lentitud puedes filtrar por provincias.
        for idx, fila in df_pueblos.iterrows():
            # Crear un bocadillo estético para el mapa
            html_popup = f"""
            <div style='font-family: sans-serif; min-width: 140px;'>
                <h5 style='margin:0 0 5px 0;'><b>{fila['Localidad']}</b></h5>
                <p style='margin:0;'>📍 Prov: {fila['Provincia']}</p>
                <p style='margin:0;'>⛰️ Altitud: {fila['Altitud']} m</p>
            </div>
            """
            folium.Marker(
                location=[fila["Latitud"], fila["Longitud"]],
                popup=folium.Popup(html_popup, max_width=250),
                icon=folium.Icon(color="blue", icon="cloud")
            ).add_to(m)
            
        # Renderizamos el mapa en la interfaz ocupando buen espacio
        st_folium(m, width="100%", height=450, key="mapa_municipios")
        
        st.write("---")

        # Buscador ordenado alfabéticamente
        lista_pueblos = sorted(df_pueblos["Localidad"].unique())
        pueblo_elegido = st.selectbox("Escribe o selecciona tu municipio:", lista_pueblos, key="selector_pueblo")
        
        # Extraemos coordenadas y datos de la base de datos
        datos_pueblo = df_pueblos[df_pueblos["Localidad"] == pueblo_elegido].iloc[0]
        lat_pueblo = datos_pueblo["Latitud"]
        lon_pueblo = datos_pueblo["Longitud"]
        provincia = datos_pueblo["Provincia"]
        altitud = datos_pueblo.get("Altitud", "N/A")
        
        st.markdown(f"### 📍 Pronóstico para: **{pueblo_elegido} ({provincia})** — *Altitud: {altitud} m*")
        
        # Usamos los datos de la Hora 00 para calcular las distancias en la malla del WRF
        ruta_hora_00 = os.path.join("salida_datos", "datos_hora_00.csv")
        
        if os.path.exists(ruta_hora_00):
            df_malla_base = pd.read_csv(ruta_hora_00)
            
            # Cálculo del vecino más cercano (Distancia euclidiana)
            distancias = np.sqrt((df_malla_base["lat_wrf"] - lat_pueblo)**2 + (df_malla_base["lon_wrf"] - lon_pueblo)**2)
            indice_mas_cercano = distancias.idxmin()
            
            # Construimos la serie temporal recopilando los datos de cada hora
            cronograma = []
            for h in range(24):
                ruta_hora = os.path.join("salida_datos", f"datos_hora_{h:02d}.csv")
                if os.path.exists(ruta_hora):
                    df_hora = pd.read_csv(ruta_hora)
                    fila_pueblo = df_hora.iloc[indice_mas_cercano]
                    
                    # Calculamos el momento exacto en el tiempo para esta hora
                    momento_exacto = fecha_inicio_prevision + datetime.timedelta(hours=h + 2)
                    
                    cronograma.append({
                        "Fecha/Hora": momento_exacto.strftime("%d/%m %H:%M"),
                        "Temperatura (°C)": fila_pueblo["temperatura"],
                        "Viento (km/h)": fila_pueblo["viento"],
                        "Lluvia (mm)": fila_pueblo["lluvia"]
                    })
            
            df_pronostico = pd.DataFrame(cronograma)
            
            # --- MÓDULO VISUAL: Tarjetas de resumen estético ---
            col1, col2, col3, col4 = st.columns(4) # Añadimos una columna más para meter la mínima y la máxima
            
            # Calculamos los valores directamente del DataFrame de pronóstico
            temp_max = df_pronostico["Temperatura (°C)"].max()
            temp_min = df_pronostico["Temperatura (°C)"].min()
            viento_max = df_pronostico["Viento (km/h)"].max()
            lluvia_total = df_pronostico["Lluvia (mm)"].max()
            
            # Pintamos las 4 tarjetas en horizontal
            col1.metric("Temperatura Máxima", f"{temp_max} °C")
            col2.metric("Temperatura Mínima", f"{temp_min} °C")
            col3.metric("Racha Viento Máx.", f"{viento_max} km/h")
            col4.metric("Precip. Acumulada", f"{lluvia_total} mm")

            
            st.write("---")
            
            # --- GRÁFICA 1: Temperatura interactiva (Plotly) ---
            fig_temp = px.line(
                df_pronostico, x="Fecha/Hora", y="Temperatura (°C)", 
                title="📈 Temperatura (°C)", markers=True,
                color_discrete_sequence=['#FF4B4B']
            )
            # Personalizamos el diseño para que quede limpio
            fig_temp.update_layout(xaxis_title="Fecha/Hora (UTC+2)", yaxis_title="Temperatura (°C)")
            st.plotly_chart(fig_temp, use_container_width=True)
            
            # --- GRÁFICAS 2 y 3: Lluvia y Viento en paralelo ---
            col_g1, col_g2 = st.columns(2)
            
            with col_g1:
                fig_lluvia = px.bar(
                    df_pronostico, x="Fecha/Hora", y="Lluvia (mm)", 
                    title="🌧️ Precipitación (mm)",
                    color_discrete_sequence=['#0083B0']
                )
                fig_lluvia.update_layout(xaxis_title="Fecha/Hora (UTC+2)", yaxis_title="Precipitación (mm)")
                st.plotly_chart(fig_lluvia, use_container_width=True)
                
            with col_g2:
                fig_viento = px.line(
                    df_pronostico, x="Fecha/Hora", y="Viento (km/h)", 
                    title="💨 Rachas de Viento (km/h)", markers=True,
                    color_discrete_sequence=['#FF9933']
                )
                fig_viento.update_layout(xaxis_title="Fecha/Hora (UTC+2)", yaxis_title="Velocidad (km/h)")
                st.plotly_chart(fig_viento, use_container_width=True)
                
        else:
            st.warning("⏳ Los datos numéricos de los municipios se están procesando o subiendo al repositorio. Esperando archivos...")
    else:
        st.error("❌ No se encuentra el archivo 'localidades.csv' en la raíz de la web. Asegúrate de hacerle un git push.")
