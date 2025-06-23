import streamlit as st
import requests
import re
import pandas as pd

st.set_page_config(page_title="Reporte de Selfies", layout="centered")

st.markdown("<h3 style='text-align: center; color: #007BFF;'>INGRESA TUS CREDENCIALES DE SIGOF WEB</h3>", unsafe_allow_html=True)

# Inicializar estado
for key in ["logged_in", "dataframe", "usuario", "clave", "session", "headers"]:
    if key not in st.session_state:
        st.session_state[key] = None if key != "logged_in" else False
if st.session_state["dataframe"] is None:
    st.session_state["dataframe"] = pd.DataFrame()

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

def obtener_selfies(session, headers):
    url = "http://sigof.distriluz.com.pe/plus/ComlecOrdenlecturas/ajax_mostar_mapa_selfie"
    data_response = session.get(url, headers=headers)
    data = data_response.text
    data_cleaned = re.sub(r"</?\w+.*?>", "", data.replace("\\/", "/"))
    data_cleaned = re.sub(r"\s+", " ", data_cleaned).strip()
    blocks = re.split(r"Ver detalle", data_cleaned)

    registros = []
    for block in blocks:
        fecha = re.search(r"Fecha Selfie:\s*(\d{1,2} de [a-zA-Z]+ de \d{4} en horas: \d{2}:\d{2}:\d{2})", block)
        lecturista = re.search(r"Lecturista:\s*([\w\sÁÉÍÓÚáéíóúÑñ]+)", block)
        url = re.search(r'url\\":\\"(https[^"]+)', block)  # <- Línea corregida

        if fecha and lecturista and url:
            fecha_hora = convertir_fecha_hora(fecha.group(1).strip())
            registros.append({
                "fecha": fecha_hora.split()[0],
                "nombre": lecturista.group(1).strip(),
                "url": url.group(1).strip()
            })

    return pd.DataFrame(registros)

if not st.session_state.logged_in:
    with st.form("login_form"):
        usuario = st.text_input("👤 Usuario:", max_chars=30)
        clave = st.text_input("🔑 Contraseña:", type="password", max_chars=30)
        submitted = st.form_submit_button("🔓 Iniciar sesión")
        if submitted:
            login_url = "http://sigof.distriluz.com.pe/plus/usuario/login"
            session = requests.Session()
            credentials = {
                "data[Usuario][usuario]": usuario,
                "data[Usuario][pass]": clave
            }
            headers = {"User-Agent": "Mozilla/5.0", "Referer": login_url}
            response = session.post(login_url, data=credentials, headers=headers)
            if "incorrecto" in response.text:
                st.error("🧠 Usuario o contraseña incorrectos.")
            else:
                df = obtener_selfies(session, headers)
                if not df.empty:
                    st.session_state.update({
                        "logged_in": True,
                        "usuario": usuario,
                        "clave": clave,
                        "session": session,
                        "headers": headers,
                        "dataframe": df
                    })
                else:
                    st.warning("⚠️ No se encontraron datos.")

if st.session_state.logged_in:
    if st.button("🔄 Actualizar Selfies"):
        session = requests.Session()
        credentials = {
            "data[Usuario][usuario]": st.session_state.usuario,
            "data[Usuario][pass]": st.session_state.clave
        }
        headers = {"User-Agent": "Mozilla/5.0", "Referer": "http://sigof.distriluz.com.pe/plus/usuario/login"}
        response = session.post("http://sigof.distriluz.com.pe/plus/usuario/login", data=credentials, headers=headers)
        if "incorrecto" not in response.text:
            st.session_state.dataframe = obtener_selfies(session, headers)
        else:
            st.error("🔐 La sesión expiró. Vuelve a iniciar sesión.")

    df = st.session_state.dataframe
    if not df.empty:
        fecha_opcion = st.selectbox("📅 Filtrar por Fecha", ["Todas"] + sorted(df["fecha"].unique()))
        df_filtrado = df[df["fecha"] == fecha_opcion] if fecha_opcion != "Todas" else df

        nombre_opcion = st.selectbox("👤 Filtrar por Lecturista", ["Todos"] + sorted(df_filtrado["nombre"].unique()))
        df_filtrado = df_filtrado[df_filtrado["nombre"] == nombre_opcion] if nombre_opcion != "Todos" else df_filtrado

        st.markdown(f"<h4 style='text-align: center; color:#007BFF'>📸 {len(df_filtrado)} selfies encontradas</h4>", unsafe_allow_html=True)
        for _, row in df_filtrado.iterrows():
            st.markdown(f"<div style='text-align: center; margin-bottom: 15px;'>"
                        f"<img src='{row['url']}' style='width: 250px; border-radius: 10px;'><br>"
                        f"<div style='font-weight: bold; font-size: 14px; margin-top: 5px; color: #007BFF;'>"
                        f"{row['nombre']} - {row['fecha']}</div></div>", unsafe_allow_html=True)
