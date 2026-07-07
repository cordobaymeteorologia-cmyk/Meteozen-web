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
tab_mapas, tab_municipios, tab_avisos = st.tabs(["🗺️ Mapas Generales", "🔍 Predicción por Municipio", "⚠️ Avisos METEOZEN"])

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
    with st.container():
        OPCIONES = {
            "Radar de Reflectividad ⛈️": os.path.join("salida_radar", "radar_{:02d}.png"),
            "Temperatura a 2m 🌡️": os.path.join("salida_temperatura", "temperatura_{:02d}.png"),
            "Viento a 10m 💨": os.path.join("salida_viento", "viento_{:02d}.png"),
            "Lluvia Horaria 🌧️": os.path.join("salida_lluvia_horaria", "lluvia_{:02d}.png"),
            "Lluvia Acumulada 🌊": os.path.join("salida_lluvia_acumulada", "lluvia_acum_{:02d}.png"),
            "Humedad Relativa 💧": os.path.join("salida_humedad", "humedad_{:02d}.png"),      
            "Cobertura Nubosa ☁️": os.path.join("salida_nubosidad", "nubes_{:02d}.png"),       
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
    with st.container():
        st.header("🔍 Predicción por Localidad")
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
            # =====================================================================
            # 1. FILTRO EN DOS PASOS (OPTIMIZACIÓN ANTI-CONGELAMIENTO)
            # =====================================================================
            # Primero elegimos la provincia para aligerar la carga del navegador
            lista_provincias = sorted(df_pueblos["Provincia"].unique())
            provincia_elegida = st.selectbox("1. Selecciona tu provincia:", lista_provincias, key="selector_provincia")
        
            # Filtramos el DataFrame para quedarnos SOLO con los pueblos de esa provincia
            df_filtrado = df_pueblos[df_pueblos["Provincia"] == provincia_elegida]
            lista_pueblos_filtrados = sorted(df_filtrado["Localidad"].unique())
        
            # Ahora el buscador solo tiene que procesar unos pocos pueblos, ¡adiós cuelgues!
            pueblo_elegido = st.selectbox("2. Selecciona tu municipio:", lista_pueblos_filtrados, key="selector_pueblo")
        
            # Obtenemos los datos del pueblo seleccionado del DataFrame filtrado
            datos_pueblo = df_filtrado[df_filtrado["Localidad"] == pueblo_elegido].iloc[0]
            lat_pueblo = datos_pueblo["Latitud"]
            lon_pueblo = datos_pueblo["Longitud"]
            provincia = datos_pueblo["Provincia"]
            altitud = datos_pueblo.get("Altitud", "N/A")
            # =====================================================================
        
            st.markdown(f"### 📍 Pronóstico para: **{pueblo_elegido} ({provincia})** — *Altitud: {altitud} m*")       
            st.write("---")
        
            # 2. SECCIÓN MAPA INTERACTIVO ESTILO WINDY
            st.subheader("🗺️ Mapa interactivo")
        
            col_capa, col_hora = st.columns([1, 1])
        
            with col_capa:
                capa_seleccionada = st.selectbox(
                    "Selecciona la capa del mapa:",
                    ["Temperatura 🌡️", "Lluvia Horaria 🌧️", "Viento 💨", "Humedad Relativa 💧", "Cobertura Nubosa ☁️"],
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
        
            # Rutas de tus scripts independientes (*_mapa.py)
            MAPA_CAPAS = {
                "Temperatura 🌡️": os.path.join("salida_temperatura_mapa", "temperatura_{:02d}.png"),
                "Lluvia Horaria 🌧️": os.path.join("salida_lluvia_horaria_mapa", "lluvia_{:02d}.png"),
                "Viento 💨": os.path.join("salida_viento_mapa", "viento_{:02d}.png"),
                "Humedad Relativa 💧": os.path.join("salida_humedad_mapa", "humedad_{:02d}.png"), 
                "Cobertura Nubosa ☁️": os.path.join("salida_nubosidad_mapa", "nubes_{:02d}.png"), 
            }
        
            ruta_capa_img = MAPA_CAPAS[capa_seleccionada].format(hora_mapa)
            limites_mapa = [[35.0, -10.0], [44.5, 4.5]] 
        
            m = folium.Map(location=[lat_pueblo, lon_pueblo], zoom_start=8, tiles="CartoDB dark_matter")
        
            if os.path.exists(ruta_capa_img):
                folium.raster_layers.ImageOverlay(
                    image=ruta_capa_img,
                    bounds=limites_mapa,
                    opacity=0.6,
                    interactive=True,
                    cross_origin=False
                ).add_to(m)
            else:
                st.caption("⚠️ Datos no disponibles en el servidor.")
        
            folium.Marker(
                location=[lat_pueblo, lon_pueblo],
                popup=f"📍 {pueblo_elegido}",
                icon=folium.Icon(color="red", icon="info-sign")
            ).add_to(m)
        
            st_folium(m, width="100%", height=500, key="mapa_windy_render")
            st.write("---")
        
            # 3. LÓGICA DE LAS GRÁFICAS Y PREVISIÓN LOCAL (¡Recuperada!)
            ruta_hora_00 = os.path.join("salida_datos", "datos_hora_00.csv")
        
            if os.path.exists(ruta_hora_00):
                df_malla_base = pd.read_csv(ruta_hora_00)
            
                # Cálculo del vecino más cercano en la malla WRF
                distancias = np.sqrt((df_malla_base["lat_wrf"] - lat_pueblo)**2 + (df_malla_base["lon_wrf"] - lon_pueblo)**2)
                indice_mas_cercano = distancias.idxmin()
            
                cronograma = []
                for h in range(24):
                    ruta_hora = os.path.join("salida_datos", f"datos_hora_{h:02d}.csv")
                    if os.path.exists(ruta_hora):
                        df_hora = pd.read_csv(ruta_hora)
                        fila_pueblo = df_hora.iloc[indice_mas_cercano]
                        momento_exacto = fecha_inicio_prevision + datetime.timedelta(hours=h + 2)
                    
                        cronograma.append({
                            "Fecha/Hora": momento_exacto.strftime("%d/%m %H:%M"),
                            "Temperatura (°C)": fila_pueblo["temperatura"],
                            "Viento (km/h)": fila_pueblo["viento"],
                            "Lluvia (mm)": fila_pueblo["lluvia"],
                            "Humedad (%)": fila_pueblo["humedad"],
                            "Nubosidad (%)": fila_pueblo["nubosidad"],
                        })
            
                df_pronostico = pd.DataFrame(cronograma)
            
                # Tarjetas de resumen (Métricas)
                col1, col2, col3, col4 = st.columns(4)
                temp_max = df_pronostico["Temperatura (°C)"].max()
                temp_min = df_pronostico["Temperatura (°C)"].min()
                viento_max = df_pronostico["Viento (km/h)"].max()
                lluvia_total = df_pronostico["Lluvia (mm)"].max()  # Sumamos la lluvia para tener el acumulado del día
            
                col1.metric("Temperatura Máxima", f"{temp_max:.1f} °C")
                col2.metric("Temperatura Mínima", f"{temp_min:.1f} °C")
                col3.metric("Racha Viento Máx.", f"{viento_max:.1f} km/h")
                col4.metric("Precip. Acumulada", f"{lluvia_total:.1f} mm")
            
                st.write("---")
            
                # Gráfica interactiva de Temperatura
                fig_temp = px.line(df_pronostico, x="Fecha/Hora", y="Temperatura (°C)", title="📈 Evolución de la Temperatura (°C)", markers=True, color_discrete_sequence=['#FF4B4B'])
                fig_temp.update_layout(xaxis_title="Fecha/Hora (UTC+2)", yaxis_title="Temperatura (°C)")
                st.plotly_chart(fig_temp, use_container_width=True)
            
                # Gráficas de Lluvia y Viento en paralelo
                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    fig_lluvia = px.bar(df_pronostico, x="Fecha/Hora", y="Lluvia (mm)", title="🌧️ Precipitación Horaria (mm)", color_discrete_sequence=['#0083B0'])
                    fig_lluvia.update_layout(xaxis_title="Fecha/Hora (UTC+2)", yaxis_title="Precipitación (mm)")
                    st.plotly_chart(fig_lluvia, use_container_width=True)
                with col_g2:
                    fig_viento = px.line(df_pronostico, x="Fecha/Hora", y="Viento (km/h)", title="💨 Velocidad del Viento (km/h)", markers=True, color_discrete_sequence=['#FF9933'])
                    fig_viento.update_layout(xaxis_title="Fecha/Hora (UTC+2)", yaxis_title="Velocidad (km/h)")
                    st.plotly_chart(fig_viento, use_container_width=True)

                st.write("---")

                col_g3, col_g4 = st.columns(2)
                with col_g3:
                    # Línea interactiva con marcadores de color cyan/azul claro para la humedad
                    fig_humedad = px.line(df_pronostico, x="Fecha/Hora", y="Humedad (%)", title="💧 Evolución de la Humedad Relativa (%)", markers=True, color_discrete_sequence=['#00D2FF'])
                    fig_humedad.update_layout(xaxis_title="Fecha/Hora (UTC+2)", yaxis_title="Humedad (%)", yaxis=dict(range=[0, 105]))
                    st.plotly_chart(fig_humedad, use_container_width=True)
                with col_g4:
                    # Usamos una gráfica de área rellena en gris claro para simular visualmente el cielo cubierto
                    fig_nubes = px.area(df_pronostico, x="Fecha/Hora", y="Nubosidad (%)", title="☁️ Evolución de la Cobertura Nubosa (%)", color_discrete_sequence=['#A0A0A0'])
                    fig_nubes.update_layout(xaxis_title="Fecha/Hora (UTC+2)", yaxis_title="Nubosidad (%)", yaxis=dict(range=[0, 105]))
                    st.plotly_chart(fig_nubes, use_container_width=True)

                
            else:
                st.warning("⏳ Los datos numéricos para los municipios aún se están procesando...")
        else:
            st.error("❌ Los datos de las localidades no están disponibles ahora mismo.")

# ==========================================
# PESTAÑA NUEVA: ⚠️ AVISOS METEOROLÓGICOS (AEMET COMARCAL)
# ==========================================
with tab_avisos:
    with st.container():
        st.header("⚠️ Avisos (MeteoZen)")
        st.write(
            "Avisos automáticos con los umbrales de la AEMET y su plan MeteoAlerta."
            "⚠️IMPORTANTE: Toma estos avisos como una referencia. En caso de tiempo severo, siempre sigue las alertas de la AEMET. Estos avisos son automáticos y pueden tener errores."
        )

        # 1. Selector de Variable de Aviso
        opcion_mapa = st.selectbox(
            "📊 Selecciona el tipo de aviso:",
            ["Temperatura Máxima (T2)", "Rachas de Viento", "Precipitación en 1 Hora"],
            key="pestana_avisos_variable"
        )

        diccionario_carpetas = {
            "Temperatura Máxima (T2)": "salida_avisos_t2",
            "Rachas de Viento": "salida_avisos_viento",
            "Precipitación en 1 Hora": "salida_avisos_lluvia1h"
        }
        diccionario_prefijos = {
            "Temperatura Máxima (T2)": "t2",
            "Rachas de Viento": "viento",
            "Precipitación en 1 Hora": "lluvia1h"
        }

        carpeta_seleccionada = diccionario_carpetas[opcion_mapa]
        prefijo_archivo = diccionario_prefijos[opcion_mapa]

        # 2. Selector deslizante de horas
        hora_seleccionada = st.select_slider(
            "🕒 Evolución horaria de los avisos (UTC):",
            options=list(range(24)),
            format_func=lambda x: f"{x:02d}:00 UTC",
            key="pestana_avisos_hora"
        )

        # 🌟 3. CÁLCULO DINÁMICO DE LA HORA EN UTC+2
        # Sumamos 2 horas a la hora UTC seleccionada. Si pasa de 24, usamos el módulo (%) 24
        hora_local = (hora_seleccionada + 2) % 24
    
        # Mostramos el cartel destacado con las dos horas (Válido para...)
        st.info(f"📅 Avisos válidos para: {hora_local:02d}:00 (UTC+2)")

        # 3. 🌟 RUTA RELATIVA PARA LA NUBE (Busca dentro del propio repositorio cargado)
        # Ya no usamos "/home/david/..." -> Buscamos en el directorio actual del servidor "."
        nombre_imagen = f"{prefijo_archivo}_{hora_seleccionada:02d}.png"
        ruta_completa_imagen = os.path.join(".", carpeta_seleccionada, nombre_imagen)

        st.write("---")

        # 4. Renderizado del mapa
        if os.path.exists(ruta_completa_imagen):
            st.image(
                ruta_completa_imagen, 
                width=700 
            )
        else:
            st.warning(
                f"⚠️ El mapa de avisos para las {hora_seleccionada:02d}:00 UTC aún no está disponible en el servidor."
            )
            st.info(
                "No hay datos."
            )
