import streamlit as st
import requests
import re
import pandas as pd

st.set_page_config(page_title="Reporte de Selfies", layout="centered")

st.markdown("<h3 style='text-align: center; color: #007BFF;'>HUMANO INGRESA TUS CREDENCIALES DE SIGOF WEB</h3>", unsafe_allow_html=True) 

# Inicializar estado
for key in ["logged_in", "dataframe", "usuario", "clave", "session", "headers", "fecha_filtro_seleccionada", "new_records_count", "new_records_urls"]:
    if key not in st.session_state:
        st.session_state[key] = None if key not in ["logged_in", "fecha_filtro_seleccionada", "new_records_count", "new_records_urls"] else False if key == "logged_in" else "Todas" if key == "fecha_filtro_seleccionada" else 0 if key == "new_records_count" else set()
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
    url = "http://sigof.distriluz.com.pe/plus/ComlecOrdenlecturas/ajax_mostar_mapa_selfie" // AUTOR
    registros = []
    try:
        data_response = session.get(url, headers=headers, timeout=10)
        data_response.raise_for_status()
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
                    "fecha_hora_completa": fecha_hora,
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
                response = session.post(login_url, data=credentials, headers=headers, timeout=10)
                response.raise_for_status()

                if "incorrecto" in response.text:
                    st.error("🧠 Usuario o contraseña incorrectos.")
                else:
                    with st.spinner('Cargando selfies...'):
                        df = obtener_selfies(session, headers)
                    if not df.empty:
                        st.session_state.update({
                            "logged_in": True,
                            "usuario": usuario,
                            "clave": clave,
                            "session": session,
                            "headers": headers,
                            "dataframe": df,
                            "new_records_count": 0, # Reiniciar el contador al iniciar sesión
                            "new_records_urls": set() # Reiniciar las URLs nuevas
                        })
                        st.success("✅ ¡Inicio de sesión exitoso y datos cargados!")
                        st.experimental_rerun()
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
        opciones_fecha = ["Todas"] + sorted(st.session_state.dataframe["fecha"].unique(), reverse=True)
        try:
            current_date_index = opciones_fecha.index(st.session_state.fecha_filtro_seleccionada)
        except ValueError:
            current_date_index = 0

        fecha_opcion = st.selectbox(
            "📅 Filtrar por Fecha",
            opciones_fecha,
            index=current_date_index,
            key="fecha_filtro_selectbox"
        )
        if fecha_opcion != st.session_state.fecha_filtro_seleccionada:
            st.session_state.fecha_filtro_seleccionada = fecha_opcion

        if st.button("🔄 Actualizar Selfies"):
            # Guardar el DataFrame actual antes de la actualización para comparar
            old_df_urls = set(st.session_state.dataframe['url'].tolist()) # Usamos la URL como identificador único

            st.info("Reautenticando y actualizando datos...")
            login_url_refresh = "http://sigof.distriluz.com.pe/plus/usuario/login" # ¡Considera cambiar a HTTPS!
            try:
                session_refresh = requests.Session()
                credentials_refresh = {
                    "data[Usuario][usuario]": st.session_state.usuario,
                    "data[Usuario][pass]": st.session_state.clave
                }
                headers_refresh = {"User-Agent": "Mozilla/5.0", "Referer": login_url_refresh}

                response_refresh = session_refresh.post(login_url_refresh, data=credentials_refresh, headers=headers_refresh, timeout=10)
                response_refresh.raise_for_status()

                if "incorrecto" not in response_refresh.text:
                    with st.spinner('Actualizando datos de selfies...'):
                        new_retrieved_df = obtener_selfies(session_refresh, headers_refresh)

                    if not new_retrieved_df.empty:
                        # Convertir la nueva columna a datetime para comparación y ordenamiento
                        new_retrieved_df['fecha_hora_completa'] = pd.to_datetime(new_retrieved_df['fecha_hora_completa'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
                        new_retrieved_df.dropna(subset=['fecha_hora_completa'], inplace=True)

                        # Identificar nuevos registros
                        new_urls = set(new_retrieved_df['url'].tolist())
                        newly_added_urls = new_urls - old_df_urls # URLs que están en el nuevo, pero no en el viejo
                        st.session_state.new_records_count = len(newly_added_urls)
                        st.session_state.new_records_urls = newly_added_urls # Guardar las URLs de los nuevos registros

                        st.session_state.dataframe = new_retrieved_df # Actualizar el DataFrame en el estado
                        st.session_state.session = session_refresh
                        st.session_state.headers = headers_refresh

                        if st.session_state.new_records_count > 0:
                            st.success(f"✅ Datos actualizados. ¡Se encontraron **{st.session_state.new_records_count} nuevos registros**!")
                        else:
                            st.info("ℹ️ Datos actualizados. No se encontraron nuevos registros.")
                    else:
                        st.warning("⚠️ No se encontraron nuevos datos de selfies después de la actualización.")
                        st.session_state.dataframe = pd.DataFrame() # Limpiar si no hay datos
                        st.session_state.new_records_count = 0
                        st.session_state.new_records_urls = set()

                else:
                    st.error("🔐 La sesión expiró o las credenciales ya no son válidas. Por favor, reinicia la aplicación y vuelve a iniciar sesión.")
                    st.session_state.logged_in = False
                    st.experimental_rerun()
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
        # Convertir la columna 'fecha_hora_completa' a datetime para un ordenamiento correcto
        df['fecha_hora_completa'] = pd.to_datetime(df['fecha_hora_completa'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
        # Eliminar filas con fechas inválidas si las hubiera
        df.dropna(subset=['fecha_hora_completa'], inplace=True)

        # Ordenar el DataFrame por la columna 'fecha_hora_completa' de forma descendente
        df_sorted = df.sort_values(by='fecha_hora_completa', ascending=False).reset_index(drop=True)

        # Aplicar el filtro de fecha usando la selección guardada en session_state
        df_filtrado = df_sorted.copy()
        if st.session_state.fecha_filtro_seleccionada != "Todas":
            df_filtrado = df_filtrado[df_filtrado["fecha"] == st.session_state.fecha_filtro_seleccionada]

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            nombre_opcion = st.selectbox("👤 Filtrar por Lecturista", ["Todos"] + sorted(df_filtrado["nombre"].unique()))

        if nombre_opcion != "Todos":
            df_filtrado = df_filtrado[df_filtrado["nombre"] == nombre_opcion]

        st.markdown("---")
        st.markdown(f"<h4 style='text-align: center; color:#007BFF'>📸 {len(df_filtrado)} selfies encontradas</h4>", unsafe_allow_html=True)

        # Mostrar el contador de nuevos registros si hubo una actualización reciente
        if st.session_state.new_records_count > 0:
            st.markdown(f"<p style='text-align: center; color: green; font-weight: bold;'>¡Se encontraron {st.session_state.new_records_count} nuevos registros!</p>", unsafe_allow_html=True)
            # Después de mostrar, limpiar el contador para que no aparezca en subsiguientes renders sin nueva actualización
            # st.session_state.new_records_count = 0 # No lo limpiamos aquí para que persista hasta la próxima actualización.

        for _, row in df_filtrado.iterrows():
            # Determinar el estilo para el nombre (rojo si es nuevo, azul si no)
            nombre_color = "#007BFF"
            nuevo_tag = ""
            if row['url'] in st.session_state.new_records_urls:
                nombre_color = "red"
                nuevo_tag = " (NUEVO SELFIE)"

            st.markdown(f"<div style='text-align: center; margin-bottom: 15px;'>"
                        f"<img src='{row['url']}' style='width: 250px; border-radius: 10px;'><br>"
                        f"<div style='font-weight: bold; font-size: 14px; margin-top: 5px; color: {nombre_color};'>"
                        f"{row['nombre']} - {row['fecha']}{nuevo_tag}</div></div>", unsafe_allow_html=True)
    elif st.session_state.logged_in:
        st.info("No hay selfies para mostrar con los filtros aplicados o aún no se han cargado datos.")
