from flask import Flask, send_file
from reporte_selfie import generar_excel_selfies

app = Flask(__name__)

@app.route('/')
def inicio():
    return '<h2>✅ Bienvenido a Reporte Selfie - SIGOF</h2><a href="/descargar">📥 Descargar Excel</a>'

@app.route('/descargar')
def descargar():
    filename = generar_excel_selfies()
    return send_file(filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
