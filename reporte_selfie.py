def generar_excel_selfies():
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.append(["Lecturista", "Fecha", "Url Foto"])
    ws.append(["Ejemplo", "21/06/2025", "http://ejemplo.com/foto.jpg"])
    filename = "Lmc_ReporteSelfie.xlsx"
    wb.save(filename)
    return filename
