from datetime import datetime
from pathlib import Path

import flet as ft

# Utilidad para exportar datos de una tabla a un archivo Excel.

def mostrar_mensaje(pagina, mensaje, color=ft.Colors.GREEN):
    snack = ft.SnackBar(
        content=ft.Text(mensaje),
        bgcolor=color,
        duration=3000
    )
    pagina.overlay.append(snack)
    snack.open = True
    pagina.update()


def obtener_texto_control(control):
    if control is None:
        return ""
    if hasattr(control, "value"):
        return str(control.value)
    if hasattr(control, "text"):
        return str(control.text)
    return str(control)


def obtener_datos_tabla(tabla_documentos):
    encabezados = [
        obtener_texto_control(columna.label)
        for columna in tabla_documentos.columns
    ]

    filas = []
    for fila in tabla_documentos.rows:
        filas.append([
            obtener_texto_control(celda.content)
            for celda in fila.cells
        ])

    return encabezados, filas


def crear_informe_tabla(pagina, tabla_documentos):
    """Crea un Excel con la información que está cargada en la tabla."""
    try:
        ruta_informe = crear_informe_facturas(tabla_documentos)
        mostrar_mensaje(pagina, f"Informe creado: {ruta_informe}")
    except Exception as e:
        print(f"Error al crear informe: {e}")
        mostrar_mensaje(pagina, f"Error al crear informe: {e}", ft.Colors.RED)


def crear_informe_facturas(tabla_documentos):
    """Crea un archivo Excel con la información actual de una DataTable."""
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill
        from openpyxl.utils import get_column_letter
    except ImportError as exc:
        raise RuntimeError("Falta instalar openpyxl para crear el informe.") from exc

    carpeta_informes = Path.home() / "OneDrive" / "GA BD Soft Factinven" / "Informes" / "Inventario"
    carpeta_informes.mkdir(parents=True, exist_ok=True)

    nombre_archivo = (
        f"informe_inventario_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    )
    ruta_informe = carpeta_informes / nombre_archivo

    encabezados, filas = obtener_datos_tabla(tabla_documentos)

    libro = Workbook()
    hoja = libro.active
    hoja.title = "Informe"
    hoja.append(encabezados)

    for celda in hoja[1]:
        celda.font = Font(color="FFFFFF")
        celda.fill = PatternFill(
            start_color="1F4E78",
            end_color="1F4E78",
            fill_type="solid"
        )

    hoja.auto_filter.ref = f"A1:{get_column_letter(len(encabezados))}1"

    for fila in filas:
        hoja.append(fila)

    for columna in hoja.columns:
        longitud_maxima = 0
        letra_columna = get_column_letter(columna[0].column)
        for celda in columna:
            valor = "" if celda.value is None else str(celda.value)
            longitud_maxima = max(longitud_maxima, len(valor))
        hoja.column_dimensions[letra_columna].width = min(
            max(longitud_maxima + 2, 12),
            60
        )

    libro.save(ruta_informe)
    return ruta_informe


def crear_informe_inventario(productos):
    """Crea en la carpeta App un Excel a partir del informe de inventario.

    ``productos`` debe contener las mismas claves que retorna
    ``obtener_informe_inventario``: código, movimientos y stock final.
    """
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Alignment, Font, PatternFill
        from openpyxl.utils import get_column_letter
    except ImportError as exc:
        raise RuntimeError("Falta instalar openpyxl para crear el informe.") from exc

    # InformeExcel.py está dentro de App/utils; su carpeta padre es App.
    carpeta_app = Path(__file__).resolve().parent.parent
    nombre_archivo = (
        f"informe_inventario_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    )
    ruta_informe = carpeta_app / nombre_archivo

    libro = Workbook()
    hoja = libro.active
    hoja.title = "Inventario"

    encabezados = [
        "Código", "Producto", "Entradas", "Compras",
        "Ventas", "Remisiones", "Stock final", "Unidad",
    ]
    hoja.append(["INFORME DE INVENTARIO"])
    hoja.append([f"Generado: {datetime.now().strftime('%d/%m/%Y %I:%M %p')}"])
    hoja.append(encabezados)

    # Estilo del título y de los encabezados.
    hoja.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(encabezados))
    hoja["A1"].font = Font(bold=True, size=14, color="FFFFFF")
    hoja["A1"].fill = PatternFill("solid", fgColor="1F4E78")
    hoja["A1"].alignment = Alignment(horizontal="center")

    for celda in hoja[3]:
        celda.font = Font(bold=True, color="FFFFFF")
        celda.fill = PatternFill("solid", fgColor="1F4E78")
        celda.alignment = Alignment(horizontal="center")

    for producto in productos:
        hoja.append([
            producto.get("codigo", ""),
            producto.get("nombre", ""),
            float(producto.get("entradas", 0)),
            float(producto.get("compras", 0)),
            float(producto.get("ventas", 0)),
            float(producto.get("remisiones", 0)),
            float(producto.get("stock_final", 0)),
            producto.get("unidad", "UND"),
        ])

    # Agrego filtro y ajusto el ancho para que sea cómodo de leer.
    hoja.auto_filter.ref = f"A3:{get_column_letter(len(encabezados))}{hoja.max_row}"
    hoja.freeze_panes = "A4"
    for columna in hoja.columns:
        letra = get_column_letter(columna[0].column)
        longitud = max(len(str(celda.value or "")) for celda in columna)
        hoja.column_dimensions[letra].width = min(max(longitud + 2, 12), 35)

    libro.save(ruta_informe)
    return ruta_informe
