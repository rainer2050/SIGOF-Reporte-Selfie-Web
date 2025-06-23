import streamlit as st
import requests
import re
import pandas as pd

st.set_page_config(page_title="Reporte de Selfies", layout="centered")

st.markdown("<h3 style='text-align: center; color: #007BFF;'>INGRESA TUS CREDENCIALES DE SIGOF WEB</h3>", unsafe_allow_html=True)

# --- Inicializar estado ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "dataframe" not in st.session_state:
    st.session_state.dataframe = pd.DataFrame()

# --- Función para convertir fechas ---
def convertir_fecha_hora(fecha_hora_str):
    meses = {
        "January": "01", "February": "02", "March": "03", "April": "04",
        "May": "05", "June": "06", "July": "07", "August": "08",
        "September": "09", "October": "10", "November": "11", "December": "12"
    }
    match = re.match(r"(\d{1,2}) de ([a-zA-Z]+) de (\d{4}) en horas: (\d{2}:\d{2}:\d{2})", fecha_hora_str)
    if match:
        dia, mes, anio, hora = match.groups()
        mes_num = meses.get(mes, "00")
        return f"{dia.zfill(2)}/{mes_num}/{anio} {hora}"
    return fecha_hora_str

# --- FORMULARIO DE LOGIN ---
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            usuario = st.text_input("👤 Usuario:", max_chars=30)
            clave = st.text_input("🔑 Contraseña:", type="password", max_chars=30)
            submitted = st.form_submit_button("🔓 Humano inicia sesión")

            if submitted:
                login_url = "http://sigof.distriluz.com.pe/plus/usuario/login"
                data_url = "http://sigof.distriluz.com.pe/plus/ComlecOrdenlecturas/ajax_mostar_mapa_selfie"

                with requests.Session() as session:
                    credentials = {
                        "data[Usuario][usuario]": usuario,
                        "data[Usuario][pass]": clave
                    }
                    headers = {
                        "User-Agent": "Mozilla/5.0",
                        "Referer": login_url
                    }

                    response = session.post(login_url, data=credentials, headers=headers)

                    if "Usuario o contraseña incorrecto" in response.text:
                        st.error("🧠 Usuario o contraseña incorrectos.")
                    else:
                        data_response = session.get(data_url, headers=headers)
                        data = data_response.text
                        data_cleaned = data.replace("\\/", "/")
                        data_cleaned = re.sub(r"<\/?\w+.*?>", "", data_cleaned)
                        data_cleaned = re.sub(r"\s+", " ", data_cleaned).strip()
                        blocks = re.split(r"Ver detalle", data_cleaned)

                        registros = []
                        for block in blocks:
                            fecha = re.search(r"Fecha Selfie:\s*(\d{1,2} de [a-zA-Z]+ de \d{4} en horas: \d{2}:\d{2}:\d{2})", block)
                            lecturista = re.search(r"Lecturista:\s*([\w\sÁÉÍÓÚáéíóúÑñ]+)", block)
                            url = re.search(r"url\":\"(https[^\"]+)", block)

                            if fecha and lecturista and url:
                                fecha_hora = convertir_fecha_hora(fecha.group(1).strip())
                                fecha_sola = fecha_hora.split()[0]
                                nombre = lecturista.group(1).strip()
                                imagen_url = url.group(1).strip()
                                registros.append({
                                    "fecha": fecha_sola,
                                    "nombre": nombre,
                                    "url": imagen_url
                                })

                        if registros:
                            df = pd.DataFrame(registros)
                            st.session_state.logged_in = True
                            st.session_state.dataframe = df
                        else:
                            st.warning("⚠️ Humano tu usuario o contraseña es incorrecta / no se encontró datos para exportar.")

# --- GALERÍA DE SELFIES ---
if st.session_state.logged_in and not st.session_state.dataframe.empty:
    df = st.session_state.dataframe

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        fecha_filtro = st.selectbox("📅 Humano Filtrar por Fecha", ["Todas"] + sorted(df["fecha"].unique()))

    df_filtrado = df.copy()
    if fecha_filtro != "Todas":
        df_filtrado = df_filtrado[df_filtrado["fecha"] == fecha_filtro]

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        nombre_filtro = st.selectbox("👤 Humano Filtrar por Lecturista", ["Todos"] + sorted(df_filtrado["nombre"].unique()))

    if nombre_filtro != "Todos":
        df_filtrado = df_filtrado[df_filtrado["nombre"] == nombre_filtro]

    st.markdown("---")
    st.markdown(f"<h4 style='text-align: center; color:#007BFF'> Humano 📸 {len(df_filtrado)} selfies encontradas</h4>", unsafe_allow_html=True)

    for _, row in df_filtrado.iterrows():
        st.markdown(
            f"""
            <div style='text-align: center; margin-bottom: 15px;'>
                <img src="{row['url']}" style='width: 250px; border-radius: 10px;'><br>
                <div style='font-weight: bold; font-size: 14px; margin-top: 5px; color: #007BFF;'>
                    {row['nombre']} - {row['fecha']}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
