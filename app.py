import streamlit as st
import requests

st.set_page_config(page_title="Depuración Selfies SIGOF", layout="centered")
st.title("🔍 Depuración - Selfies SIGOF")

def obtener_raw(session, headers):
    url = "http://sigof.distriluz.com.pe/plus/ComlecOrdenlecturas/ajax_mostar_mapa_selfie"
    response = session.get(url, headers=headers)
    return response.text

with st.form("login_form"):
    usuario = st.text_input("👤 Usuario:")
    clave = st.text_input("🔑 Contraseña:", type="password")
    submitted = st.form_submit_button("Iniciar sesión")

    if submitted:
        login_url = "http://sigof.distriluz.com.pe/plus/usuario/login"
        session = requests.Session()
        credentials = {
            "data[Usuario][usuario]": usuario,
            "data[Usuario][pass]": clave
        }
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": login_url
        }

        login_response = session.post(login_url, data=credentials, headers=headers)

        if "incorrecto" in login_response.text:
            st.error("❌ Usuario o contraseña incorrectos.")
        else:
            st.success("✅ Login correcto. Mostrando datos crudos del servidor...")
            raw_text = obtener_raw(session, headers)
            st.subheader("Contenido crudo de respuesta (hasta 2000 caracteres):")
            st.code(raw_text[:2000], language="html")
