import os
import streamlit as st

# ==========================================
# CONFIGURACIÓN DE LA PÁGINA WEB
# ==========================================
st.set_page_config(
    page_title="METEO DEIVID",
    page_icon="⛈️",
    layout="centered"
)

st.title("⛈️ MODELO METEOZEN")
st.write("¡Bienvenido! Aquí puedes ver los mapas de mi propio modelo meteorológico: MeteoZen.¡Espero que te guste!")

# ==========================================
# DEFINICIÓN DE RUTAS DE LOS PNGs
# ==========================================
BASE_DIR = "/home/david/Escritorio/phyton"

OPCIONES = {
    "Radar de Reflectividad ⛈️": os.path.join(BASE_DIR, "salida_radar", "radar_{:02d}.png"),
    "Temperatura a 2m 🌡️": os.path.join(BASE_DIR, "salida_temperatura", "temperatura_{:02d}.png"),
    "Viento a 10m 💨": os.path.join(BASE_DIR, "salida_viento", "viento_{:02d}.png"),
    "Lluvia Horaria 🌧️": os.path.join(BASE_DIR, "salida_lluvia_horaria", "lluvia_{:02d}.png"),
    "Lluvia Acumulada 🌊": os.path.join(BASE_DIR, "salida_lluvia_acumulada", "lluvia_acum_{:02d}.png")
}

# ==========================================
# MENÚS EN LA INTERFAZ
# ==========================================
# 1. Selector de variable meteorológica
variable_seleccionada = st.selectbox("Selecciona la variable a visualizar:", list(OPCIONES.keys()))

# 2. Control deslizante (Slider) para las horas
# Suponemos 24 horas por defecto, pero puedes cambiar el 24 por el número de horas que tenga tu run
hora = st.slider("Paso de tiempo (Hora de la simulación):", min_value=0, max_value=23, value=0, format="Hora %02d:00")

# ==========================================
# RENDERIZADO DEL MAPA
# ==========================================
# Construimos la ruta exacta de la imagen usando la hora del slider
plantilla_ruta = OPCIONES[variable_seleccionada]
ruta_imagen = plantilla_ruta.format(hora)

# Comprobamos si el archivo existe antes de pintarlo para evitar pantallazos de error
if os.path.exists(ruta_imagen):
    st.image(ruta_imagen, use_container_width=True)
else:
    st.error(f"⚠️ No se encontró el mapa para la Hora {hora:02d}. No existen datos.")

st.info("💡 Consejo: Usa el ratón o las flechas de dirección del teclado para desplazarte entre las horas.")
