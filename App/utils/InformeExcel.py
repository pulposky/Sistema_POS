from datetime import datetime
from pathlib import Path

import flet as ft


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

    carpeta_informes = Path(__file__).resolve().parents[2] / "Informes"
    carpeta_informes.mkdir(exist_ok=True)

    nombre_archivo = (
        f"informe_facturas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
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
