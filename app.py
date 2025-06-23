import streamlit as st
import requests
import re
import pandas as pd

st.set_page_config(page_title="Reporte de Selfies", layout="centered")

st.markdown("<h3 style='text-align: center; color: #007BFF;'>INGRESA TUS CREDENCIALES DE SIGOF WEB</h3>", unsafe_allow_html=True)

# Inicializar estado
for key in ["logged_in", "dataframe", "usuario", "clave", "session", "headers", "fecha_filtro_seleccionada"]:
    if key not in st.session_state:
        st.session_state[key] = None if key not in ["logged_in", "fecha_filtro_seleccionada"] else False if key == "logged_in" else "Todas"
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
    registros = []
    try:
        data_response = session.get(url, headers=headers, timeout=10) # Añadido timeout
        data_response.raise_for_status() # Lanza un error para códigos de estado HTTP 4xx/5xx
        data = data_response.text
        data_cleaned = re.sub(r"<\/?\w+.*?>", "", data.replace("\\/", "/"))
        data_cleaned = re.sub(r"\s+", " ", data_cleaned).strip()
        blocks = re.split(r"Ver detalle", data_cleaned)

        for block in blocks:
            fecha = re.search(r"Fecha Selfie:\s*(\d{1,2} de [a-zA-Z]+ de \d{4} en horas: \d{2}:\d{2}:\d{2})", block)
            lecturista = re.search(r"Lecturista:\s*([\w\sÁÉÍÓÚáéíóúÑñ]+)", block)
            url = re.search(r"url\":\"(https[^\"]+)", block)
            if fecha and lecturista and url:
                fecha_hora = convertir_fecha_hora(fecha.group(1).strip())
                registros.append({
                    "fecha": fecha_hora.split()[0],
                    "nombre": lecturista.group(1).strip(),
                    "url": url.group(1).strip()
                })
        return pd.DataFrame(registros)
    except requests.exceptions.Timeout:
        st.error("⏳ La solicitud ha excedido el tiempo de espera. Intenta de nuevo más tarde.")
        return pd.DataFrame()
    except requests.exceptions.ConnectionError:
        st.error("❌ Error de conexión. Asegúrate de tener acceso a internet y que el servidor de SIGOF esté disponible.")
        return pd.DataFrame()
    except requests.exceptions.HTTPError as e:
        st.error(f"⚠️ Error HTTP al obtener datos: {e}. El servidor de SIGOF puede estar experimentando problemas.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"⛔ Ocurrió un error inesperado al procesar los datos de selfies: {e}")
        return pd.DataFrame()


if not st.session_state.logged_in:
    with st.form("login_form"):
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            usuario = st.text_input("👤 Usuario:", max_chars=30)
            clave = st.text_input("🔑 Contraseña:", type="password", max_chars=30)
            submitted = st.form_submit_button("🔓 Iniciar sesión")

        if submitted:
            # ¡Considera cambiar a HTTPS!
            login_url = "http://sigof.distriluz.com.pe/plus/usuario/login"
            session = requests.Session()
            credentials = {
                "data[Usuario][usuario]": usuario,
                "data[Usuario][pass]": clave
            }
            headers = {"User-Agent": "Mozilla/5.0", "Referer": login_url}

            try:
                response = session.post(login_url, data=credentials, headers=headers, timeout=10) # Añadido timeout
                response.raise_for_status() # Lanza un error para códigos de estado HTTP 4xx/5xx

                if "incorrecto" in response.text:
                    st.error("🧠 Usuario o contraseña incorrectos.")
                else:
                    with st.spinner('Cargando selfies...'): # Indicador de carga
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
                        st.success("✅ ¡Inicio de sesión exitoso y datos cargados!")
                        st.experimental_rerun() # Fuerza una recarga para mostrar la galería
                    else:
                        st.warning("⚠️ No se encontraron datos de selfies para tu usuario.")
            except requests.exceptions.Timeout:
                st.error("⏳ La solicitud de inicio de sesión ha excedido el tiempo de espera. Intenta de nuevo más tarde.")
            except requests.exceptions.ConnectionError:
                st.error("❌ Error de conexión al intentar iniciar sesión. Asegúrate de tener acceso a internet y que el servidor de SIGOF esté disponible.")
            except requests.exceptions.HTTPError as e:
                st.error(f"⚠️ Error HTTP al iniciar sesión: {e}. Verifica tus credenciales o el estado del servidor.")
            except Exception as e:
                st.error(f"⛔ Ocurrió un error inesperado durante el inicio de sesión: {e}")

if st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Guardar la selección actual de la fecha en session_state antes de los selectbox
        # para que persista a través de las actualizaciones.
        # Usa index para mantener la selección
        opciones_fecha = ["Todas"] + sorted(st.session_state.dataframe["fecha"].unique())
        try:
            current_date_index = opciones_fecha.index(st.session_state.fecha_filtro_seleccionada)
        except ValueError:
            current_date_index = 0 # Si la fecha seleccionada ya no existe (ej. por datos nuevos), vuelve a 'Todas'

        fecha_opcion = st.selectbox(
            "📅 Filtrar por Fecha",
            opciones_fecha,
            index=current_date_index,
            key="fecha_filtro_selectbox" # Añadir una key para asegurar que Streamlit lo rastree correctamente
        )
        # Actualizar la selección guardada solo cuando el selectbox cambia por interacción del usuario
        if fecha_opcion != st.session_state.fecha_filtro_seleccionada:
            st.session_state.fecha_filtro_seleccionada = fecha_opcion


        if st.button("🔄 Actualizar Selfies"):
            st.session_state.dataframe = pd.DataFrame() # Limpiar el dataframe antes de actualizar
            st.info("Reautenticando y actualizando datos...")
            # ¡Considera cambiar a HTTPS!
            login_url_refresh = "http://sigof.distriluz.com.pe/plus/usuario/login"
            try:
                # Recrear la sesión con las credenciales guardadas
                session_refresh = requests.Session()
                credentials_refresh = {
                    "data[Usuario][usuario]": st.session_state.usuario,
                    "data[Usuario][pass]": st.session_state.clave
                }
                headers_refresh = {"User-Agent": "Mozilla/5.0", "Referer": login_url_refresh}

                response_refresh = session_refresh.post(login_url_refresh, data=credentials_refresh, headers=headers_refresh, timeout=10) # Añadido timeout
                response_refresh.raise_for_status()

                if "incorrecto" not in response_refresh.text:
                    with st.spinner('Actualizando datos de selfies...'): # Indicador de carga
                        new_df = obtener_selfies(session_refresh, headers_refresh)
                    if not new_df.empty:
                        st.session_state.dataframe = new_df
                        st.session_state.session = session_refresh # Actualizar la sesión guardada
                        st.session_state.headers = headers_refresh # Actualizar los headers guardados
                        st.success("✅ Datos actualizados correctamente.")
                        # No es necesario un rerun si el estado ya maneja la visualización
                        # La selección de fecha ya está en session_state.fecha_filtro_seleccionada
                        # y el selectbox se inicializa con ella.
                    else:
                        st.warning("⚠️ No se encontraron nuevos datos de selfies.")
                else:
                    st.error("🔐 La sesión expiró o las credenciales ya no son válidas. Por favor, reinicia la aplicación y vuelve a iniciar sesión.")
                    st.session_state.logged_in = False # Forzar logout
                    st.experimental_rerun() # Fuerza un rerun para ir a la pantalla de login
            except requests.exceptions.Timeout:
                st.error("⏳ La solicitud de actualización ha excedido el tiempo de espera. Intenta de nuevo más tarde.")
            except requests.exceptions.ConnectionError:
                st.error("❌ Error de conexión al intentar actualizar. Verifica tu conexión a internet.")
            except requests.exceptions.HTTPError as e:
                st.error(f"⚠️ Error HTTP al actualizar: {e}. El servidor de SIGOF puede estar experimentando problemas.")
            except Exception as e:
                st.error(f"⛔ Ocurrió un error inesperado durante la actualización: {e}")

    df = st.session_state.dataframe
    if not df.empty:
        # Aplicar el filtro de fecha usando la selección guardada en session_state
        df_filtrado = df.copy()
        if st.session_state.fecha_filtro_seleccionada != "Todas":
            df_filtrado = df_filtrado[df_filtrado["fecha"] == st.session_state.fecha_filtro_seleccionada]

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            # Reconstruir las opciones para el filtro de nombre basado en el df_filtrado actual
            nombre_opcion = st.selectbox("👤 Filtrar por Lecturista", ["Todos"] + sorted(df_filtrado["nombre"].unique()))

        if nombre_opcion != "Todos":
            df_filtrado = df_filtrado[df_filtrado["nombre"] == nombre_opcion]

        st.markdown("---")
        st.markdown(f"<h4 style='text-align: center; color:#007BFF'>📸 {len(df_filtrado)} selfies encontradas</h4>", unsafe_allow_html=True)
        for _, row in df_filtrado.iterrows():
            st.markdown(f"<div style='text-align: center; margin-bottom: 15px;'>"
                        f"<img src='{row['url']}' style='width: 250px; border-radius: 10px;'><br>"
                        f"<div style='font-weight: bold; font-size: 14px; margin-top: 5px; color: #007BFF;'>"
                        f"{row['nombre']} - {row['fecha']}</div></div>", unsafe_allow_html=True)
    elif st.session_state.logged_in: # Solo mostrar si está logueado pero el DF está vacío
        st.info("No hay selfies para mostrar con los filtros aplicados o aún no se han cargado datos.")
