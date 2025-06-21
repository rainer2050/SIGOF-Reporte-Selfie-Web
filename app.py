from flask import Flask, request, render_template_string, send_file
from reporte_selfie import generar_excel_selfies  # <- tu función ya creada
import os

app = Flask(__name__)

HTML_FORM = """
<!DOCTYPE html>
<html>
<head>
    <title>Reporte Selfies SIGOF</title>
</head>
<body style="font-family: Arial, sans-serif; background: #f0f2f5; padding: 40px;">
    <h2 style="color: #007bff;">📸 Generador de Reporte Selfies SIGOF</h2>
    <form method="post">
        <label>👤 Usuario SIGOF:</label><br>
        <input type="text" name="usuario" style="width: 250px;" required><br><br>

        <label>🔑 Clave SIGOF:</label><br>
        <input type="password" name="clave" style="width: 250px;" required><br><br>

        <input type="submit" value="Generar Reporte" style="padding: 8px 16px; background-color: #28a745; color: white; border: none; cursor: pointer;">
    </form>
    {% if error %}
        <p style="color: red;">⚠️ {{ error }}</p>
    {% endif %}
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        usuario = request.form['usuario']
        clave = request.form['clave']
        try:
            archivo = generar_excel_selfies(usuario, clave)
            if not os.path.exists(archivo):
                return render_template_string(HTML_FORM, error="No se generó ningún archivo.")
            return send_file(archivo, as_attachment=True)
        except Exception as e:
            return render_template_string(HTML_FORM, error=str(e))
    return render_template_string(HTML_FORM)
