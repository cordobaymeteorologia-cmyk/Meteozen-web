import datetime
import os
import streamlit as st

# ==========================================
# CONFIGURACIÓN DE LA PÁGINA WEB
# ==========================================
st.set_page_config(page_title="METEO DEIVID", page_icon="⛈️", layout="centered")

st.title("⛈️ MODELO METEOZEN")
st.write(
    "¡Bienvenido! Aquí puedes ver los mapas de mi propio modelo meteorológico: MeteoZen. ¡Espero que te guste!"
)

# ==========================================
# LÓGICA DINÁMICA DE FECHAS
# ==========================================
# 1. Leer la fecha en la que corrió el modelo (generada por tu WRF.py)
ruta_fecha = "fecha_run.txt"
if os.path.exists(ruta_fecha):
    with open(ruta_fecha, "r") as f:
        fecha_str = f.read().strip()
    fecha_base = datetime.datetime.strptime(fecha_str, "%d/%m/%Y %H:%M")
else:
    # Plan B por si acaso
    fecha_base = datetime.datetime.now().replace(
        hour=0, minute=0, second=0, microsecond=0
    )

# 2. Sumamos 1 día automáticamente porque la previsión es para el día siguiente
fecha_inicio_prevision = fecha_base + datetime.timedelta(days=1)


# ==========================================
# MENÚS EN LA INTERFAZ
# ==========================================
# Definición de las carpetas (ahora relativas, dentro del repositorio)
OPCIONES = {
    "Radar de Reflectividad ⛈️": os.path.join(
        "salida_radar", "radar_{:02d}.png"
    ),
    "Temperatura a 2m 🌡️": os.path.join(
        "salida_temperatura", "temperatura_{:02d}.png"
    ),
    "Viento a 10m 💨": os.path.join("salida_viento", "viento_{:02d}.png"),
    "Lluvia Horaria 🌧️": os.path.join(
        "salida_lluvia_horaria", "lluvia_{:02d}.png"
    ),
    "Lluvia Acumulada 🌊": os.path.join(
        "salida_lluvia_acumulada", "lluvia_acum_{:02d}.png"
    ),
}

# 1. Selector de variable meteorológica
variable_seleccionada = st.selectbox(
    "Selecciona la variable a visualizar:", list(OPCIONES.keys())
)

# 2. Control deslizante (Slider) para las horas (de 0 a 23)
hora = st.slider(
    "Paso de tiempo (Hora de la simulación):",
    min_value=0,
    max_value=23,
    value=0,
    format="Hora %02d:00",
)

# 3. Cálculo de la fecha exacta para la hora seleccionada
fecha_mapa = fecha_inicio_prevision + datetime.timedelta(hours=hora)

# 4. Mostramos la fecha real e hiperprecisa en la web
st.subheader(
    f"📆 Mapa válido para el: {fecha_mapa.strftime('%d/%m/%Y a las %H:%M')} UTC"
)


# ==========================================
# RENDERIZADO DEL MAPA
# ==========================================
# Construimos la ruta exacta de la imagen usando la hora del slider
plantilla_ruta = OPCIONES[variable_seleccionada]
ruta_imagen = plantilla_ruta.format(hora)

# Comprobamos si el archivo existe en el repositorio antes de pintarlo
if os.path.exists(ruta_imagen):
    st.image(ruta_imagen, use_container_width=True)
else:
    st.error(
        f"⚠️ No se encontró el mapa para la Hora {hora:02d}. Todavía no existen datos en el servidor."
    )

st.info(
    "💡 Consejo: Usa el ratón o las flechas de dirección del teclado para desplazarte entre las horas."
)
