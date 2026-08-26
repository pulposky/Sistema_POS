import os
import sys
import textwrap
# Utilidad para generar PDFs y tickets de facturas, compras y remisiones.
from datetime import datetime

import win32print

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle,
    Paragraph, Spacer, Image
)

# ============================================================================
# MÓDULO DE GENERACIÓN DE FACTURAS, COMPRAS Y REMISIONES
# ============================================================================
# Este archivo se encarga de generar documentos (facturas de venta, compras,
# remisiones) en dos formatos:
#   1. PDF con formato de recibo/boleta de 58mm de ancho (usando ReportLab).
#   2. Ticket térmico RAW para impresoras XPrinter XP-58C (usando win32print).
#
# Flujo principal:
#   - generar_factura_pdf(): genera el PDF y opcionalmente imprime el ticket.
#   - imprimir_factura_datos(): imprime directamente el ticket térmico sin PDF.
#   - imprimir_ticket_termico(): bajo nivel, envía bytes RAW a la impresora.
#
# Dependencias externas:
#   - reportlab: para la generación del PDF.
#   - win32print: para la impresión directa en impresoras térmicas (Windows).
#
# Los documentos se guardan en OneDrive > GA BD Soft Factinven > Facturas.
# ============================================================================

# ---------------- CONSTANTES DE DISEÑO DEL TICKET ----------------
# Dimensiones físicas del ticket de 58mm
ANCHO_TICKET = 58 * mm          # Ancho total del papel térmico
MARGEN_TICKET = 5 * mm          # Margen izquierdo y derecho
ANCHO_CONTENIDO = ANCHO_TICKET - (MARGEN_TICKET * 2)  # Ancho útil para contenido

# Separadores visuales para imprimir en la térmica
LINEA_TICKET = "-" * 28         # Línea separadora para tickets de 28 caracteres
COLUMNAS_TERMICA = 32           # Ancho máximo en caracteres de la impresora
LINEA_TERMICA = "-" * COLUMNAS_TERMICA  # Línea separadora de 32 caracteres


def _ruta_recurso(ruta_relativa):
    """
    Resuelve la ruta absoluta de un recurso (ej. logo, imagen) buscándolo
    primero dentro de la carpeta App/ y luego en la raíz del proyecto.

    Parámetros:
        ruta_relativa (str): Ruta relativa al recurso (ej. "assets/Logo_sena.png").

    Retorna:
        str: Ruta absoluta si se encontró, o la ruta original como fallback.
    """
    # Primero busco dentro de la carpeta App/ (un nivel arriba de utils/)
    base_app = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ruta_app = os.path.join(base_app, ruta_relativa)
    if os.path.exists(ruta_app):
        return ruta_app

    # Si no está ahí, busco en la raíz del proyecto (dos niveles arriba)
    base_proyecto = os.path.dirname(base_app)
    ruta_proyecto = os.path.join(base_proyecto, ruta_relativa)
    if os.path.exists(ruta_proyecto):
        return ruta_proyecto

    # Si no se encontró en ningún lado, devuelvo la ruta tal cual
    return ruta_relativa


def _carpeta_facturas(tipo=None):
    """
    Obtiene o crea la carpeta donde se guardan los PDFs generados.
    Organiza por subcarpeta según el tipo de documento.

    Parámetros:
        tipo (str, optional): Tipo de documento. Puede ser "compra",
            "remision" o cualquier otra cosa (que se tratará como "ventas").

    Retorna:
        str: Ruta absoluta a la carpeta correspondiente.
    """
    # Carpeta base donde se guardan los PDF generados por el sistema
    base = os.path.join(
        os.path.expanduser("~"),
        "OneDrive",
        "GA BD Soft Factinven",
        "Facturas"
    )

    # Determino la subcarpeta según el tipo de documento
    subcarpeta = ""
    if tipo:
        tipo = tipo.lower()
        if "compra" in tipo:
            subcarpeta = "compras"
        elif "remision" in tipo:
            subcarpeta = "remisiones"
        else:
            subcarpeta = "ventas"

    carpeta = os.path.join(base, subcarpeta) if subcarpeta else base
    os.makedirs(carpeta, exist_ok=True)  # Creo la carpeta si no existe
    return carpeta


def _abrir_archivo(ruta):
    """Abre un archivo PDF con el visor predeterminado del sistema operativo."""
    try:
        if sys.platform.startswith("win"):
            os.startfile(ruta)
    except Exception as err:
        print(f"No se pudo abrir el PDF: {err}")


def _buscar_impresora_xprinter(nombre_preferido="XP-58C"):
    """
    Busca entre las impresoras instaladas una XPrinter compatible.
    Primero busca el nombre exacto preferido, luego cualquier impresora
    que contenga "XP-58" o "XPRINTER" en su nombre.

    Parámetros:
        nombre_preferido (str): Nombre exacto de la impresora a buscar primero.

    Retorna:
        str: Nombre de la impresora encontrada, o el nombre preferido como fallback.
    """
    try:
        # Obtengo la lista de todas las impresoras locales y de red
        impresoras = win32print.EnumPrinters(
            win32print.PRINTER_ENUM_LOCAL
            | win32print.PRINTER_ENUM_CONNECTIONS
        )
    except Exception:
        return nombre_preferido

    # Extraigo solo los nombres de las impresoras
    nombres = [impresora[2] for impresora in impresoras]

    # Busco primero la impresora con el nombre exacto
    if nombre_preferido in nombres:
        return nombre_preferido

    # Si no la encuentro, busco cualquier impresora XPrinter
    for nombre in nombres:
        if "XP-58" in nombre.upper() or "XPRINTER" in nombre.upper():
            return nombre

    return nombre_preferido


def _nombre_usuario(usuario):
    """
    Extrae el nombre del usuario desde distintos formatos posibles.
    El usuario puede llegar como string, diccionario con diversas claves,
    o None.

    Parámetros:
        usuario: Puede ser str, dict con claves como 'nombre', 'usuario',
                 'username', 'user', o None.

    Retorna:
        str: Nombre del usuario o "-" si no se pudo determinar.
    """
    # Obtengo el nombre del usuario aunque llegue como diccionario o texto
    if not usuario:
        return "-"
    if isinstance(usuario, dict):
        return (
            usuario.get("nombre")
            or usuario.get("usuario")
            or usuario.get("username")
            or usuario.get("user")
            or "-"
        )
    return str(usuario)


def _moneda(valor):
    """
    Formatea un valor numérico como moneda colombiana sin decimales
    para ahorrar espacio en el ticket de 58mm.

    Parámetros:
        valor: Número a formatear.

    Retorna:
        str: Valor formateado como "$1.234.567" o "$0" si hay error.
    """
    # Formato de dinero para ticket de 58mm, sin decimales para ahorrar espacio
    try:
        return f"${float(valor):,.0f}"
    except Exception:
        return "$0"


def _cantidad_texto(cantidad):
    """
    Convierte una cantidad a texto, mostrando sin decimales si es entero.
    Ejemplo: 5.0 → "5", 5.5 → "5.5".

    Parámetros:
        cantidad: Número a convertir.

    Retorna:
        str: Representación textual de la cantidad.
    """
    return (
        str(int(cantidad))
        if isinstance(cantidad, (int, float)) and cantidad == int(cantidad)
        else str(cantidad)
    )


def _envolver(texto, ancho=COLUMNAS_TERMICA):
    """
    Divide un texto en líneas de un ancho máximo dado, usando word-wrap.
    Útil para ajustar nombres largos de productos al ancho del ticket.

    Parámetros:
        texto (str): Texto a dividir.
        ancho (int): Número máximo de caracteres por línea.

    Retorna:
        list[str]: Lista de líneas envueltas.
    """
    return textwrap.wrap(str(texto), width=ancho) or [""]


def _campo_ticket(etiqueta, valor):
    """
    Formatea un campo con etiqueta y valor para el ticket.
    Ejemplo: "Cliente: Juan Pérez", envuelto si es muy largo.

    Parámetros:
        etiqueta (str): Nombre del campo.
        valor (str): Valor del campo.

    Retorna:
        list[str]: Líneas formateadas del campo.
    """
    return _envolver(f"{etiqueta}: {valor}")


def _dinero_ticket(etiqueta, valor):
    """
    Formatea una línea de dinero con la etiqueta a la izquierda y el
    monto alineado a la derecha. Esto crea el alineado típico de tickets.

    Parámetros:
        etiqueta (str): Nombre del concepto (ej. "TOTAL:").
        valor: Monto numérico a formatear.

    Retorna:
        list[str]: Línea(s) formateadas con alineación derecha.
    """
    etiqueta = str(etiqueta)
    monto = _moneda(valor)
    espacio = COLUMNAS_TERMICA - len(etiqueta) - len(monto)

    # Si la etiqueta + monto no caben en una línea, las pongo en líneas separadas
    if espacio < 1:
        return [etiqueta[:COLUMNAS_TERMICA], monto.rjust(COLUMNAS_TERMICA)]

    return [f"{etiqueta}{' ' * espacio}{monto}"]


def _centrar_ticket(texto):
    """Centra un texto dentro del ancho del ticket."""
    return str(texto).center(COLUMNAS_TERMICA)


def _crear_texto_ticket(
    id_factura,
    fecha_actual,
    etiqueta_documento,
    titulo_documento,
    nombre_cliente,
    doc_cliente,
    nombre_usuario,
    metodo_pago_txt,
    productos,
    total,
    dinero_recibido,
    cambio,
    mostrar_precios,
    es_mixto,
    efectivo=None,
    transferencia=None,
    es_copia=False,
):
    """
    Construye el texto completo del ticket térmico línea por línea.

    Este es el corazón de la impresión térmica: genera un bloque de texto
    formateado con los datos de la factura que se enviaráRAW a la impresora.

    Parámetros:
        id_factura (int): Número/ID de la factura.
        fecha_actual (str): Fecha formateada como "dd/mm/yyyy HH:MM AM/PM".
        etiqueta_documento (str): "Factura" o "Remision".
        titulo_documento (str): Título grande del documento.
        nombre_cliente (str): Nombre del cliente.
        doc_cliente (str): Número de documento del cliente.
        nombre_usuario (str): Nombre del cajero/vendedor.
        metodo_pago_txt (str): Texto del método de pago.
        productos (list[dict]): Lista de productos vendidos, cada uno con
            nombre, cantidad, unidad, precio, subtotal, lugar, id.
        total (float): Total de la venta.
        dinero_recibido (float): Dinero recibido del cliente.
        cambio (float): Cambio a devolver.
        mostrar_precios (bool): Si es False, oculta montos (usado en remisiones).
        es_mixto (bool): True si el pago es mixto (efectivo + transferencia).
        efectivo (float, optional): Monto pagado en efectivo.
        transferencia (float, optional): Monto pagado por transferencia.
        es_copia (bool): Si es True, agrega el sello "COPIA" al ticket.

    Retorna:
        str: Texto completo del ticket con saltos de línea \r\n.
    """
    lineas = [
        _centrar_ticket(titulo_documento),
    ]
    if es_copia:
        lineas.append(_centrar_ticket("COPIA"))
    lineas.extend([
        _centrar_ticket("Sistema POS - SENAEMPRESA"),
        LINEA_TERMICA,
    ])

    # --- Encabezado: datos del documento ---
    lineas.extend(_campo_ticket(etiqueta_documento, f"{id_factura:04d}"))
    lineas.extend(_campo_ticket("Fecha", fecha_actual))
    lineas.extend(_campo_ticket("Cliente", nombre_cliente))
    lineas.extend(_campo_ticket("Documento", doc_cliente))
    lineas.extend(_campo_ticket("Atendido por", nombre_usuario))

    # --- Método de pago ---
    if mostrar_precios:
        lineas.extend(_campo_ticket("Pago", metodo_pago_txt))
    elif metodo_pago_txt != "-":
        # En remisiones se muestra "Motivo" en vez de "Pago"
        lineas.extend(_campo_ticket("Motivo", metodo_pago_txt))

    # Si es pago mixto, muestro el desglose de efectivo y transferencia
    if mostrar_precios and es_mixto:
        lineas.extend(_dinero_ticket("Efectivo:", efectivo or 0))
        lineas.extend(_dinero_ticket("Transferencia:", transferencia or 0))

    # --- Lista de productos ---
    lineas.extend([LINEA_TERMICA, "PRODUCTOS"])

    for p in productos:
        nombre = str(p.get("nombre", "-"))
        cantidad = p.get("cantidad", 1)
        unidad = str(p.get("unidad", "UND"))
        precio = p.get("precio", 0)
        subtotal = p.get("subtotal", 0)
        empresa = str(p.get("lugar", "-"))

        lineas.append("")
        # Nombre del producto con su código
        lineas.extend(_envolver(f"{nombre} Cod: {p.get('id', '-')}") )

        if mostrar_precios:
            # Línea con cantidad x precio = subtotal
            cantidad_linea = f"{_cantidad_texto(cantidad)} {unidad} x {_moneda(precio)} = {_moneda(subtotal)}"
            lineas.extend(_envolver(cantidad_linea))
        else:
            # En remisiones solo muestro la cantidad
            lineas.extend(_campo_ticket("Cantidad", f"{_cantidad_texto(cantidad)} {unidad}"))

        lineas.extend(_campo_ticket("Empresa", empresa))

    # --- Desglose por empresa y totales (solo en ventas) ---
    if mostrar_precios:
        # Agrupo los subtotales por empresa/lugar
        desglose = {}
        for p in productos:
            empresa = str(p.get("lugar", "SenaEmpresa"))
            desglose[empresa] = desglose.get(empresa, 0) + p.get("subtotal", 0)

        lineas.extend([LINEA_TERMICA, "DESGLOSE POR EMPRESA"])
        for empresa, valor in desglose.items():
            lineas.extend(_dinero_ticket(f"{empresa[:16]}:", valor))

        # Totales
        subtotal_calc = sum(p.get("subtotal", 0) for p in productos)
        lineas.extend([LINEA_TERMICA])
        lineas.extend(_dinero_ticket("Subtotal:", subtotal_calc))
        lineas.extend(_dinero_ticket("Descuento:", 0))
        lineas.extend(_dinero_ticket("TOTAL:", total))

        # Desglose de pago mixto en la sección de totales
        if es_mixto:
            lineas.extend(_dinero_ticket("Efectivo:", efectivo or 0))
            lineas.extend(_dinero_ticket("Transferencia:", transferencia or 0))

        lineas.extend(_dinero_ticket("Recibido:", dinero_recibido))
        lineas.extend(_dinero_ticket("Cambio:", cambio))

    # --- Pie de página con datos de la empresa ---
    mensaje_final = "Gracias por su compra" if mostrar_precios else "Documento de remision"
    lineas.extend([
        LINEA_TERMICA,
        _centrar_ticket(mensaje_final),
        _centrar_ticket("Numero de atencion:"),
        _centrar_ticket("3125290330"),
        _centrar_ticket("HORARIO 8:00AM-3:30PM"),
        "",
        "",
        "",
    ])

    return "\r\n".join(lineas)


def imprimir_ticket_termico(texto_ticket, nombre_impresora=None):
    """
    Envía el texto del ticket como bytes RAW a una impresora térmica
    usando la API de Windows (win32print).

    Parámetros:
        texto_ticket (str): Texto del ticket generado por _crear_texto_ticket().
        nombre_impresora (str, optional): Nombre exacto de la impresora.
            Si no se provee, se busca automáticamente una XPrinter.

    Retorna:
        bool: True si la impresión fue exitosa, False si hubo error.
    """
    impresora = nombre_impresora or _buscar_impresora_xprinter()

    # Codifico el texto a cp850 (código de páginas para impresoras térmicas)
    # y agrego los bytes de inicialización ESC/POS: \x1b@ (init) \x1bt\x02 (codepage)
    datos = b"\x1b@\x1bt\x02" + texto_ticket.encode("cp850", errors="replace")

    try:
        manejador = win32print.OpenPrinter(impresora)
    except Exception as err:
        print(f"No se pudo abrir la impresora {impresora}: {err}")
        return False

    try:
        win32print.StartDocPrinter(manejador, 1, ("Factura POS", None, "RAW"))
        win32print.StartPagePrinter(manejador)
        win32print.WritePrinter(manejador, datos)
        win32print.EndPagePrinter(manejador)
        win32print.EndDocPrinter(manejador)
        return True
    except Exception as err:
        print(f"Error al imprimir ticket en {impresora}: {err}")
        return False
    finally:
        # Siempre cierro el manejador de la impresora para liberar recursos
        win32print.ClosePrinter(manejador)


def imprimir_factura_datos(
    id_factura,
    cliente,
    usuario,
    productos,
    total,
    metodo_pago,
    dinero_recibido,
    cambio,
    nombre_impresora=None,
    efectivo=None,
    transferencia=None,
    titulo_documento="FACTURA DE VENTA",
    mostrar_precios=True,
    fecha_actual=None,
    es_copia=False,
):
    """
    Punto de entrada principal para imprimir un ticket térmico directamente
    (sin generar PDF previo).

    Recibe todos los datos de la factura, los formatea en un ticket de texto
    y lo envía a la impresora térmica.

    Parámetros:
        id_factura (int): Número de la factura.
        cliente (dict): Datos del cliente (nombre, documento, etc.).
        usuario: Datos del vendedor/cajero.
        productos (list[dict]): Lista de productos vendidos.
        total (float): Total de la venta.
        metodo_pago: Método de pago (str o dict con tipo, efectivo, transferencia).
        dinero_recibido (float): Dinero recibido del cliente.
        cambio (float): Cambio a entregar.
        nombre_impresora (str, optional): Impresora a usar.
        efectivo (float, optional): Monto en efectivo (para pago mixto).
        transferencia (float, optional): Monto por transferencia.
        titulo_documento (str): Título del documento.
        mostrar_precios (bool): False para remisiones (oculta montos).
        fecha_actual (str, optional): Fecha personalizada en formato "%Y-%m-%d %H:%M:%S".
        es_copia (bool): True si es una copia del documento.

    Retorna:
        bool: True si se imprimió correctamente, False si hubo error.
    """
    # Proceso el método de pago: puede llegar como string o como diccionario
    metodo_pago_txt = str(metodo_pago) if metodo_pago is not None else "-"
    if isinstance(metodo_pago, dict):
        # Si no se pasaron montos por separado, los extraigo del diccionario
        if efectivo is None:
            efectivo = metodo_pago.get("efectivo")
        if transferencia is None:
            transferencia = metodo_pago.get("transferencia")
        metodo_pago_txt = metodo_pago.get("tipo", "Mixto")

    es_mixto = "mixto" in metodo_pago_txt.lower()

    # Proceso la fecha: la convierto de formato ISO a formato legible
    if fecha_actual:
        try:
            fecha_actual = datetime.strptime(str(fecha_actual), "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %I:%M %p")
        except Exception:
            fecha_actual = str(fecha_actual)
    else:
        fecha_actual = datetime.now().strftime("%d/%m/%Y %I:%M %p")

    # Extraigo los datos del cliente, con valores por defecto
    nombre_cliente = "Consumidor final"
    doc_cliente = "-"
    if cliente:
        nombre_cliente = cliente.get("nombre", "Consumidor final")
        doc_cliente = (
            cliente.get("documento")
            or cliente.get("cedula")
            or cliente.get("id_cliente")
            or "-"
        )

    # Genero el texto del ticket y lo envío a la impresora
    texto_ticket = _crear_texto_ticket(
        id_factura=id_factura,
        fecha_actual=fecha_actual,
        etiqueta_documento="Remision" if "remision" in titulo_documento.lower() else "Factura",
        titulo_documento=titulo_documento,
        nombre_cliente=nombre_cliente,
        doc_cliente=doc_cliente,
        nombre_usuario=_nombre_usuario(usuario),
        metodo_pago_txt=metodo_pago_txt,
        productos=productos,
        total=total,
        dinero_recibido=dinero_recibido,
        cambio=cambio,
        mostrar_precios=mostrar_precios,
        es_mixto=es_mixto,
        efectivo=efectivo,
        transferencia=transferencia,
        es_copia=es_copia,
    )
    return imprimir_ticket_termico(texto_ticket, nombre_impresora)


def generar_factura_pdf(
    id_factura,
    cliente,
    usuario,
    productos,
    total,
    metodo_pago,
    dinero_recibido,
    cambio,
    abrir=True,
    logo_path="assets/Logo_sena.png",
    efectivo=None,
    transferencia=None,
    titulo_documento="FACTURA DE VENTA",
    prefijo_archivo="factura",
    mostrar_precios=True,
):
    """
    Genera un PDF con formato de recibo/boleta de 58mm y opcionalmente
    imprime el ticket térmico.

    Este es el flujo principal de generación de documentos. Crea un PDF
    con ReportLab con todos los datos de la factura, y luego intenta
    imprimir el ticket térmico. Si la impresora no está disponible,
    abre el PDF en el visor del sistema.

    Parámetros:
        id_factura (int): Número de la factura.
        cliente (dict): Datos del cliente.
        usuario: Datos del vendedor/cajero.
        productos (list[dict]): Lista de productos vendidos.
        total (float): Total de la venta.
        metodo_pago: Método de pago (str o dict).
        dinero_recibido (float): Dinero recibido.
        cambio (float): Cambio a entregar.
        abrir (bool): Si True, intenta imprimir o abrir el PDF automáticamente.
        logo_path (str): Ruta relativa al logo de la empresa.
        efectivo (float, optional): Monto en efectivo.
        transferencia (float, optional): Monto por transferencia.
        titulo_documento (str): Título del documento.
        prefijo_archivo (str): Prefijo para el nombre del archivo PDF
            (ej. "factura", "compra", "remision").
        mostrar_precios (bool): False para remisiones.

    Retorna:
        str o None: Ruta del PDF generado, o None si hubo error.
    """
    try:
        # Creo la carpeta de destino si no existe
        carpeta = _carpeta_facturas(prefijo_archivo)
        ruta_pdf = os.path.join(carpeta, f"{prefijo_archivo}_{id_factura:04d}.pdf")

        # Alto dinamico aproximado segun cantidad de productos
        alto_ticket = max(160 * mm, (120 + len(productos) * 18) * mm)

        # Creo el documento PDF con dimensiones de ticket de 58mm
        doc = SimpleDocTemplate(
            ruta_pdf,
            pagesize=(ANCHO_TICKET, alto_ticket),
            leftMargin=MARGEN_TICKET,
            rightMargin=MARGEN_TICKET,
            topMargin=4 * mm,
            bottomMargin=4 * mm,
        )

        estilos = getSampleStyleSheet()

        # ---------------- ESTILOS DE PÁRRAFO ----------------
        # Estos estilos definen la tipografía y alineación de cada
        # tipo de texto en el PDF del ticket.

        estilo_titulo = ParagraphStyle(
            "titulo_ticket",
            parent=estilos["Title"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=9,
            alignment=1,           # 1 = centrado
            spaceAfter=2,
        )

        estilo_centro = ParagraphStyle(
            "centro_ticket",
            parent=estilos["Normal"],
            fontName="Helvetica",
            fontSize=6,
            leading=7,
            alignment=1,           # centrado
        )

        estilo_normal = ParagraphStyle(
            "normal_ticket",
            parent=estilos["Normal"],
            fontName="Helvetica",
            fontSize=6,
            leading=7,
        )

        estilo_bold = ParagraphStyle(
            "bold_ticket",
            parent=estilo_normal,
            fontName="Helvetica-Bold",
        )

        elementos = []

        # ---------------- ENCABEZADO DEL PDF ----------------

        # Logo pequeño centrado en la parte superior
        logo_resuelto = _ruta_recurso(logo_path)
        if os.path.exists(logo_resuelto):
            try:
                elementos.append(Image(logo_resuelto, width=18 * mm, height=18 * mm, hAlign="CENTER"))
                elementos.append(Spacer(1, 2 * mm))
            except Exception:
                pass

        # Título del documento y nombre del sistema
        elementos.append(Paragraph(titulo_documento, estilo_titulo))
        elementos.append(Paragraph("Sistema POS - SENAEMPRESA", estilo_centro))
        elementos.append(Paragraph(LINEA_TICKET, estilo_centro))

        fecha_actual = datetime.now().strftime("%d/%m/%Y %I:%M %p")

        # ---------------- DATOS DEL CLIENTE ----------------

        nombre_cliente = "Consumidor final"
        doc_cliente = "-"

        if cliente:
            nombre_cliente = cliente.get("nombre", "Consumidor final")
            doc_cliente = (
                cliente.get("documento")
                or cliente.get("cedula")
                or cliente.get("id_cliente")
                or "-"
            )

        # ---------------- DATOS DEL USUARIO ----------------

        nombre_usuario = _nombre_usuario(usuario)

        # ---------------- METODO DE PAGO ----------------

        metodo_pago_txt = str(metodo_pago) if metodo_pago is not None else "-"
        es_mixto = "mixto" in metodo_pago_txt.lower()

        # Si el metodo de pago llega como diccionario, saco los montos de ahi
        if isinstance(metodo_pago, dict):
            if efectivo is None:
                efectivo = metodo_pago.get("efectivo")
            if transferencia is None:
                transferencia = metodo_pago.get("transferencia")
            metodo_pago_txt = metodo_pago.get("tipo", "Mixto")
            es_mixto = True

        # Agrego los campos de encabezado al PDF
        etiqueta_documento = "Remision" if "remision" in titulo_documento.lower() else "Factura"
        elementos.append(Paragraph(f"<b>{etiqueta_documento}:</b> {id_factura:04d}", estilo_normal))
        elementos.append(Paragraph(f"<b>Fecha:</b> {fecha_actual}", estilo_normal))
        elementos.append(Paragraph(f"<b>Cliente:</b> {nombre_cliente}", estilo_normal))
        elementos.append(Paragraph(f"<b>Documento:</b> {doc_cliente}", estilo_normal))
        elementos.append(Paragraph(f"<b>Atendido por:</b> {nombre_usuario}", estilo_normal))
        if mostrar_precios:
            elementos.append(Paragraph(f"<b>Pago:</b> {metodo_pago_txt}", estilo_normal))
        elif metodo_pago_txt != "-":
            elementos.append(Paragraph(f"<b>Motivo:</b> {metodo_pago_txt}", estilo_normal))

        # Si es pago mixto, muestro el desglose de efectivo y transferencia
        if mostrar_precios and es_mixto:
            # En pago mixto muestro separado cuanto fue en efectivo y transferencia
            efectivo_val = float(efectivo) if efectivo is not None else 0.0
            transferencia_val = float(transferencia) if transferencia is not None else 0.0
            elementos.append(Paragraph(f"<b>Efectivo:</b> {_moneda(efectivo_val)}", estilo_normal))
            elementos.append(Paragraph(f"<b>Transferencia:</b> {_moneda(transferencia_val)}", estilo_normal))

        elementos.append(Paragraph(LINEA_TICKET, estilo_centro))
        elementos.append(Paragraph("PRODUCTOS", estilo_bold))

        # ---------------- SECCIÓN DE PRODUCTOS ----------------

        # Productos en formato angosto: cada producto ocupa 3 líneas
        for p in productos:
            # Tomo los mismos campos que se cargan desde vender.py y buscarProducto.py
            nombre = str(p.get("nombre", "-"))
            cantidad = p.get("cantidad", 1)
            unidad = str(p.get("unidad", "UND"))
            precio = p.get("precio", 0)
            subtotal = p.get("subtotal", 0)
            empresa = str(p.get("lugar", "-"))

            cantidad_txt = _cantidad_texto(cantidad)

            elementos.append(Spacer(1, 1 * mm))
            elementos.append(Paragraph(f"<b>{nombre}</b> Cod: {p.get('id', '-')}", estilo_normal))
            if mostrar_precios:
                elementos.append(Paragraph(f"{cantidad_txt} {unidad} x {_moneda(precio)} = {_moneda(subtotal)}", estilo_normal))
            else:
                elementos.append(Paragraph(f"Cantidad: {cantidad_txt} {unidad}", estilo_normal))
            elementos.append(Paragraph(f"Empresa: {empresa}", estilo_normal))


        elementos.append(Paragraph(LINEA_TICKET, estilo_centro))

        # ---------------- DESGLOSE POR EMPRESA ----------------

        # Desglose por empresa: agrupo los subtotales por lugar/proveedor
        desglose = {}
        for p in productos:
            # Agrupo el valor vendido por cada SenaEmpresa o lugar del producto
            empresa = str(p.get("lugar", "SenaEmpresa"))
            desglose[empresa] = desglose.get(empresa, 0) + p.get("subtotal", 0)

        if mostrar_precios:
            elementos.append(Paragraph("DESGLOSE POR EMPRESA", estilo_bold))

            # Renderizo cada empresa con su subtotal en una tabla de 2 columnas
            for empresa, valor in desglose.items():
                tabla_empresa = Table(
                    [[empresa[:18], _moneda(valor)]],
                    colWidths=[21 * mm, ANCHO_CONTENIDO - (21 * mm)],
                )
                tabla_empresa.setStyle(TableStyle([
                    ("FONTSIZE", (0, 0), (-1, -1), 6),
                    ("ALIGN", (1, 0), (1, 0), "RIGHT"),    # Monto alineado a la derecha
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                    ("TOPPADDING", (0, 0), (-1, -1), 1),
                ]))
                elementos.append(tabla_empresa)

            elementos.append(Paragraph(LINEA_TICKET, estilo_centro))

        # ---------------- SECCIÓN DE TOTALES ----------------

        if mostrar_precios:
            subtotal_calc = sum(p.get("subtotal", 0) for p in productos)

            # Armo la tabla de totales como lista de filas [etiqueta, valor]
            totales = [
                ["Subtotal:", _moneda(subtotal_calc)],
                ["Descuento:", "$0"],
                ["TOTAL:", _moneda(total)],
            ]

            # Si es pago mixto, agrego el desglose en la tabla de totales
            if es_mixto:
                efectivo_val = float(efectivo) if efectivo is not None else 0.0
                transferencia_val = float(transferencia) if transferencia is not None else 0.0
                totales.append(["Efectivo:", _moneda(efectivo_val)])
                totales.append(["Transferencia:", _moneda(transferencia_val)])

            totales.append(["Recibido:", _moneda(dinero_recibido)])
            totales.append(["Cambio:", _moneda(cambio)])

            # Creo la tabla de totales con formato destacado para el TOTAL
            tabla_totales = Table(
                totales,
                colWidths=[18 * mm, ANCHO_CONTENIDO - (18 * mm)],
            )
            tabla_totales.setStyle(TableStyle([
                ("FONTSIZE", (0, 0), (-1, -1), 6),
                ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold"),  # TOTAL en negrita
                ("FONTSIZE", (0, 2), (-1, 2), 8),                  # TOTAL más grande
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),               # Montos a la derecha
                ("LINEABOVE", (0, 2), (-1, 2), 0.7, colors.black), # Línea sobre TOTAL
                ("LINEBELOW", (0, 2), (-1, 2), 0.7, colors.black),# Línea bajo TOTAL
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]))
            elementos.append(tabla_totales)

        # ---------------- PIE DE PÁGINA ----------------

        elementos.append(Spacer(1, 4 * mm))
        mensaje_final = "Gracias por su compra" if mostrar_precios else "Documento de remision"
        elementos.append(Paragraph(mensaje_final, estilo_centro))
        elementos.append(Paragraph("Numeró de atencion: 3125290330", estilo_centro) )
        elementos.append(Paragraph("HORARIO DE ATENCION 8:00AM-3:30PM", estilo_centro))

        # Construyo el PDF
        doc.build(elementos)

        # Si se pidió abrir/imprimir, intento imprimir el ticket térmico
        if abrir:
            texto_ticket = _crear_texto_ticket(
                id_factura=id_factura,
                fecha_actual=fecha_actual,
                etiqueta_documento=etiqueta_documento,
                titulo_documento=titulo_documento,
                nombre_cliente=nombre_cliente,
                doc_cliente=doc_cliente,
                nombre_usuario=nombre_usuario,
                metodo_pago_txt=metodo_pago_txt,
                productos=productos,
                total=total,
                dinero_recibido=dinero_recibido,
                cambio=cambio,
                mostrar_precios=mostrar_precios,
                es_mixto=es_mixto,
                efectivo=efectivo,
                transferencia=transferencia,
            )
            # Si la impresión térmica falla, abro el PDF en el visor
            if not imprimir_ticket_termico(texto_ticket):
                _abrir_archivo(ruta_pdf)

        return ruta_pdf

    except Exception as err:
        print(f"Error generando PDF: {err}")
        import traceback
        traceback.print_exc()
        return None


def imprimir_factura(ruta_pdf, nombre_impresora=None):
    """
    Función de compatibilidad con llamadas antiguas al sistema.
    La impresión principal ahora se hace como ticket térmico RAW.
    Esta función simplemente abre el PDF en el visor del sistema.

    Parámetros:
        ruta_pdf (str): Ruta al archivo PDF a abrir.
        nombre_impresora (str, optional): No se usa, mantenido por compatibilidad.

    Retorna:
        bool: True si el archivo existía y se pudo abrir.
    """
    if not os.path.exists(ruta_pdf):
        print(f"No se encontró el archivo: {ruta_pdf}")
        return False

    _abrir_archivo(ruta_pdf)
    return True
