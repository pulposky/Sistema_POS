from datetime import datetime
from pathlib import Path

import flet as ft

# ============================================================================
# MÓDULO DE GENERACIÓN DE INFORMES EXCEL
# ============================================================================
# Contiene funciones para exportar datos de tablas y listas a archivos
# Excel (.xlsx) usando la librería openpyxl.
#
# Tipos de informes soportados:
#   1. Informe desde DataTable: extrae los datos visibles de una tabla Flet
#      y los exporta directamente a Excel (usado en consultas).
#   2. Informe de inventario: genera un reporte estructurado con código,
#      producto, entradas, compras, ventas, remisiones y stock final.
#
# Los archivos se guardan en:
#   - OneDrive/GA BD Soft Factinven/Informes/Inventario/ (para DataTable)
#   - App/ (para informes de inventario)
#
# Dependencia:
#   - openpyxl: para crear y manipular archivos Excel.
# ============================================================================


def mostrar_mensaje(pagina, mensaje, color=ft.Colors.GREEN):
    """
    Muestra una notificación SnackBar breve en la parte inferior de la pantalla.

    Parámetros:
        pagina (ft.Page): Página de Flet donde se mostrará la notificación.
        mensaje (str): Texto de la notificación.
        color: Color de fondo del SnackBar (verde por defecto, rojo para errores).
    """
    snack = ft.SnackBar(
        content=ft.Text(mensaje),
        bgcolor=color,
        duration=3000
    )
    pagina.overlay.append(snack)
    snack.open = True
    pagina.update()


def obtener_texto_control(control):
    """
    Extrae el texto de un control de Flet de forma genérica.
    Maneja diferentes tipos de controles: TextField (value), Text (text),
    u objetos con str() directo.

    Parámetros:
        control: Componente de Flet del cual extraer el texto.

    Retorna:
        str: Texto extraído del control, o "" si es None.
    """
    if control is None:
        return ""
    if hasattr(control, "value"):
        return str(control.value)
    if hasattr(control, "text"):
        return str(control.text)
    return str(control)


def obtener_datos_tabla(tabla_documentos):
    """
    Extrae los encabezados y filas de una DataTable de Flet para
    exportarlos a Excel.

    Parámetros:
        tabla_documentos (ft.DataTable): Tabla de Flet de la cual extraer datos.

    Retorna:
        tuple: (encabezados, filas) donde:
            - encabezados (list[str]): Lista de nombres de columnas.
            - filas (list[list[str]]): Lista de filas, cada una con sus celdas.
    """
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
    """
    Crea un archivo Excel a partir de los datos visibles en una DataTable.
    Muestra una notificación con el resultado.

    Parámetros:
        pagina (ft.Page): Página para mostrar notificaciones.
        tabla_documentos (ft.DataTable): Tabla de Flet con los datos a exportar.
    """
    try:
        ruta_informe = crear_informe_facturas(tabla_documentos)
        mostrar_mensaje(pagina, f"Informe creado: {ruta_informe}")
    except Exception as e:
        print(f"Error al crear informe: {e}")
        mostrar_mensaje(pagina, f"Error al crear informe: {e}", ft.Colors.RED)


def crear_informe_facturas(tabla_documentos):
    """
    Crea un archivo Excel con formato profesional a partir de una DataTable.
    Incluye encabezados con fondo azul, filtros automáticos y ancho
    de columnas ajustado al contenido.

    Parámetros:
        tabla_documentos (ft.DataTable): Tabla de Flet con los datos.

    Retorna:
        Path: Ruta del archivo Excel creado.

    Raises:
        RuntimeError: Si openpyxl no está instalado.
    """
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill
        from openpyxl.utils import get_column_letter
    except ImportError as exc:
        raise RuntimeError("Falta instalar openpyxl para crear el informe.") from exc

    # Creo la carpeta de destino si no existe
    carpeta_informes = Path.home() / "OneDrive" / "GA BD Soft Factinven" / "Informes" / "Inventario"
    carpeta_informes.mkdir(parents=True, exist_ok=True)

    # Nombre de archivo con marca de tiempo para evitar sobreescribir
    nombre_archivo = (
        f"informe_inventario_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    )
    ruta_informe = carpeta_informes / nombre_archivo

    # Extraigo los datos de la tabla
    encabezados, filas = obtener_datos_tabla(tabla_documentos)

    # Creo el libro de Excel
    libro = Workbook()
    hoja = libro.active
    hoja.title = "Informe"

    # Agrego los encabezados como primera fila
    hoja.append(encabezados)

    # Estilo de los encabezados: texto blanco y fondo azul oscuro
    for celda in hoja[1]:
        celda.font = Font(color="FFFFFF")
        celda.fill = PatternFill(
            start_color="1F4E78",
            end_color="1F4E78",
            fill_type="solid"
        )

    # Agrego filtro automático a los encabezados
    hoja.auto_filter.ref = f"A1:{get_column_letter(len(encabezados))}1"

    # Agrego todas las filas de datos
    for fila in filas:
        hoja.append(fila)

    # Ajusto el ancho de cada columna al contenido máximo
    for columna in hoja.columns:
        longitud_maxima = 0
        letra_columna = get_column_letter(columna[0].column)
        for celda in columna:
            valor = "" if celda.value is None else str(celda.value)
            longitud_maxima = max(longitud_maxima, len(valor))
        # Ancho mínimo 12, máximo 60 para que sea cómodo de leer
        hoja.column_dimensions[letra_columna].width = min(
            max(longitud_maxima + 2, 12),
            60
        )

    libro.save(ruta_informe)
    return ruta_informe


def crear_informe_inventario(productos):
    """
    Crea un archivo Excel con un informe de inventario estructurado.
    Incluye título, fecha de generación, encabezados de columna, datos
    de productos y formato profesional (fondo azul, filtros, freeze panes).

    Parámetros:
        productos (list[dict]): Lista de productos con las claves:
            - codigo (str): Código del producto.
            - nombre (str): Nombre del producto.
            - entradas (float): Cantidad de entradas.
            - compras (float): Cantidad de compras.
            - ventas (float): Cantidad de ventas.
            - remisiones (float): Cantidad de remisiones.
            - stock_final (float): Stock final calculado.
            - unidad (str): Unidad de medida.

    Retorna:
        Path: Ruta del archivo Excel creado.

    Raises:
        RuntimeError: Si openpyxl no está instalado.
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

    # Defino los encabezados de columna del informe
    encabezados = [
        "Código", "Producto", "Entradas", "Compras",
        "Ventas", "Remisiones", "Stock final", "Unidad",
    ]

    # Fila 1: Título del informe
    hoja.append(["INFORME DE INVENTARIO"])
    # Fila 2: Fecha y hora de generación
    hoja.append([f"Generado: {datetime.now().strftime('%d/%m/%Y %I:%M %p')}"])
    # Fila 3: Encabezados de columna
    hoja.append(encabezados)

    # Estilo del título: merge de celdas, fondo azul, texto blanco, centrado
    hoja.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(encabezados))
    hoja["A1"].font = Font(bold=True, size=14, color="FFFFFF")
    hoja["A1"].fill = PatternFill("solid", fgColor="1F4E78")
    hoja["A1"].alignment = Alignment(horizontal="center")

    # Estilo de los encabezados de columna (fila 3): fondo azul, texto blanco
    for celda in hoja[3]:
        celda.font = Font(bold=True, color="FFFFFF")
        celda.fill = PatternFill("solid", fgColor="1F4E78")
        celda.alignment = Alignment(horizontal="center")

    # Agrego los datos de cada producto
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

    # Agrego filtro automático y congelo las filas superiores
    hoja.auto_filter.ref = f"A3:{get_column_letter(len(encabezados))}{hoja.max_row}"
    hoja.freeze_panes = "A4"  # Congelo desde la fila 4 para que los encabezados siempre sean visibles

    # Ajusto el ancho de cada columna al contenido máximo
    for columna in hoja.columns:
        letra = get_column_letter(columna[0].column)
        longitud = max(len(str(celda.value or "")) for celda in columna)
        # Ancho mínimo 12, máximo 35
        hoja.column_dimensions[letra].width = min(max(longitud + 2, 12), 35)

    libro.save(ruta_informe)
    return ruta_informe
