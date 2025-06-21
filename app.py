from flask import Flask, request, render_template, send_file
import requests
import re
import pandas as pd
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from io import BytesIO

app = Flask(__name__)

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

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        usuario = request.form['usuario']
        clave = request.form['clave']

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
                return render_template('index.html', error="Credenciales incorrectas")

            data_response = session.get(data_url, headers=headers)

        data = data_response.text.replace("\\/", "/")
        data = re.sub(r"<\/?\w+.*?>", "", data)
        data = re.sub(r"\s+", " ", data).strip()
        blocks = re.split(r"Ver detalle", data)

        results = {}
        for block in blocks:
            fecha = re.search(r"Fecha Selfie:\s*(\d{1,2} de [a-zA-Z]+ de \d{4} en horas: \d{2}:\d{2}:\d{2})", block)
            lecturista = re.search(r"Lecturista:\s*([\w\sÁÉÍÓÚáéíóúÑñ]+)", block)
            url = re.search(r"url\":\"(https[^"]+)", block)

            if fecha and lecturista and url:
                fecha_formateada = convertir_fecha_hora(fecha.group(1).strip())
                fecha_selfie, _ = fecha_formateada.split(" ")
                lecturista_nombre = lecturista.group(1).strip()
                url_imagen = url.group(1).strip()

                key = (lecturista_nombre, fecha_selfie)
                if key not in results:
                    results[key] = {"URLs Imagen": []}
                results[key]["URLs Imagen"].append(url_imagen)

        if not results:
            return render_template('index.html', error="No se encontraron datos o credenciales incorrectas")

        max_urls = max(len(item["URLs Imagen"]) for item in results.values())
        columns = ["Fecha Selfie", "Lecturista"] + [f"Url_foto {i+1}" for i in range(max_urls)]
        vista_columns = [f"Vista Url_foto {i+1}" for i in range(max_urls)]

        data = []
        for (lecturista, fecha), info in results.items():
            row = [fecha, lecturista] + info["URLs Imagen"] + [""] * (max_urls - len(info["URLs Imagen"]))
            data.append(row)

        df = pd.DataFrame(data, columns=columns)
        wb = Workbook()
        ws = wb.active
        ws.title = "LmcSelfiesLectura"
        ws.append(columns + vista_columns)

        for i, row in enumerate(df.itertuples(index=False), start=2):
            row_data = list(row)
            ws.append(row_data + [""] * max_urls)
            for j in range(max_urls):
                col_index = 3 + j
                url_cell = f"{get_column_letter(col_index)}{i}"
                vista_col_index = len(columns) + j + 1
                formula_cell = f"{get_column_letter(vista_col_index)}{i}"
                ws[formula_cell] = f'=IMAGE({url_cell},4,200,140)'
                ws.column_dimensions[get_column_letter(vista_col_index)].width = round(140 / 7, 1)
            ws.row_dimensions[i].height = 151

        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return send_file(output, as_attachment=True, download_name="Lmc_ReporteSelfie.xlsx", mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)


