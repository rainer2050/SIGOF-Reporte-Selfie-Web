
from flask import Flask, render_template, request, send_file
from reporte_selfie import generar_excel_selfies
import os

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        usuario = request.form["usuario"]
        clave = request.form["clave"]
        archivo = generar_excel_selfies(usuario, clave)
        if archivo:
            return send_file(archivo, as_attachment=True)
        else:
            return render_template("index.html", error="Usuario o clave incorrecta, o no hay datos.")
    return render_template("index.html")
