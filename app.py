from flask import Flask, render_template, request, send_file
import os
import re
import requests
import pandas as pd
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from datetime import datetime

app = Flask(__name__)

# Ruta para guardar archivos
RUTA_ARCHIVO = "static/archivos"
os.makedirs(RUTA_ARCHIVO, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        clave = request.form.get('clave')

        login_url = "http://sigof.distriluz.com.pe/plus/usuario/login"
        data_url = "http://sigof.distriluz.com.pe/plus/ComlecOrdenlecturas/ajax_mostar_mapa_selfie"

        credentials = {
            "data[Usuario][usuario]": usuario,
            "data[Usuario][pass]": clave
        }

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": login_url,
        }

        with requests.Session() as session:
            login_response = session.post(login_url, data=credentials, headers=headers)
            if "Usuario o contraseña incorrecto" in login_response.text:
                return render_template('index.html', error="Usuario o contraseña incorrectos")

            data_response = session.get(data_url, headers=headers)

        data = data_response.text
        data_cleaned = data.replace("\\/", "/")
        data_cleaned = re.sub(r"<\/?\w+.*?>", "", data_cleaned)
        data_cleaned = re.sub(r"\s+", " ", data_cleaned).strip()
        blocks = re.split(r"Ver detalle", data_cleaned)

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

        results = {}
        for block in blocks:
            fecha = re.search(r"Fecha Selfie:\s*(\d{1,2} de [a-zA-Z]+ de \d{4} en horas: \d{2}:\d{2}:\d{2})", block)
            lecturista = re.search(r"Lecturista:\s*([\w\sÁÉÍÓÚáéíóúÑñ]+)", block)
            url = re.search(r"url\":\"(https[^"]+)", block)

            if fecha and lecturista and url:
                fecha_hora_formateada = convertir_fecha_hora(fecha.group(1).strip())
                fecha_selfie, _ = fecha_hora_formateada.split(" ")
                lecturista_nombre = lecturista.group(1).strip()
                url_imagen = url.group(1).strip()

                key = (lecturista_nombre, fecha_selfie)
                if key not in results:
                    results[key] = {"URLs Imagen": []}
                results[key]["URLs Imagen"].append(url_imagen)

        if not results:
            return render_template('index.html', error="No se encontraron datos para exportar.")

        max_urls = max(len(item["URLs Imagen"]) for item in results.values())
        url_columns = [f"Url_foto {i+1}" for i in range(max_urls)]
        columns = ["Fecha Selfie", "Lecturista"] + url_columns

        data = []
        for (lecturista, fecha_selfie), info in results.items():
            row = [fecha_selfie, lecturista] + info["URLs Imagen"] + [""] * (max_urls - len(info["URLs Imagen"]))
            data.append(row)

        df = pd.DataFrame(data, columns=columns)

        wb = Workbook()
        ws = wb.active
        ws.title = "LmcSelfiesLectura"
        ws.append(columns)

        for i, row in enumerate(df.itertuples(index=False), start=2):
            row_data = list(row)
            ws.append(row_data)

        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ReporteSelfie_{now}.xlsx"
        path = os.path.join(RUTA_ARCHIVO, filename)
        wb.save(path)

        return send_file(path, as_attachment=True)

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)

