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


ANCHO_TICKET = 58 * mm
MARGEN_TICKET = 5 * mm
ANCHO_CONTENIDO = ANCHO_TICKET - (MARGEN_TICKET * 2)
LINEA_TICKET = "-" * 28
COLUMNAS_TERMICA = 32
LINEA_TERMICA = "-" * COLUMNAS_TERMICA


def _ruta_recurso(ruta_relativa):
    base_app = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ruta_app = os.path.join(base_app, ruta_relativa)
    if os.path.exists(ruta_app):
        return ruta_app

    base_proyecto = os.path.dirname(base_app)
    ruta_proyecto = os.path.join(base_proyecto, ruta_relativa)
    if os.path.exists(ruta_proyecto):
        return ruta_proyecto

    return ruta_relativa


def _carpeta_facturas(tipo=None):
    # Carpeta base donde se guardan los PDF generados por el sistema
    base = os.path.join(
        os.path.expanduser("~"),
        "OneDrive",
        "GA BD Soft Factinven",
        "Facturas"
    )

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
    os.makedirs(carpeta, exist_ok=True)
    return carpeta


def _abrir_archivo(ruta):
    # Abre el PDF automaticamente
    try:
        if sys.platform.startswith("win"):
            os.startfile(ruta)
    except Exception as err:
        print(f"No se pudo abrir el PDF: {err}")


def _buscar_impresora_xprinter(nombre_preferido="XP-58C"):
    try:
        impresoras = win32print.EnumPrinters(
            win32print.PRINTER_ENUM_LOCAL
            | win32print.PRINTER_ENUM_CONNECTIONS
        )
    except Exception:
        return nombre_preferido

    nombres = [impresora[2] for impresora in impresoras]
    if nombre_preferido in nombres:
        return nombre_preferido

    for nombre in nombres:
        if "XP-58" in nombre.upper() or "XPRINTER" in nombre.upper():
            return nombre

    return nombre_preferido


def _nombre_usuario(usuario):
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
    # Formato de dinero para ticket de 58mm, sin decimales para ahorrar espacio
    try:
        return f"${float(valor):,.0f}"
    except Exception:
        return "$0"


def _cantidad_texto(cantidad):
    return (
        str(int(cantidad))
        if isinstance(cantidad, (int, float)) and cantidad == int(cantidad)
        else str(cantidad)
    )


def _envolver(texto, ancho=COLUMNAS_TERMICA):
    return textwrap.wrap(str(texto), width=ancho) or [""]


def _campo_ticket(etiqueta, valor):
    return _envolver(f"{etiqueta}: {valor}")


def _dinero_ticket(etiqueta, valor):
    etiqueta = str(etiqueta)
    monto = _moneda(valor)
    espacio = COLUMNAS_TERMICA - len(etiqueta) - len(monto)

    if espacio < 1:
        return [etiqueta[:COLUMNAS_TERMICA], monto.rjust(COLUMNAS_TERMICA)]

    return [f"{etiqueta}{' ' * espacio}{monto}"]


def _centrar_ticket(texto):
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
    lineas = [
        _centrar_ticket(titulo_documento),
    ]
    if es_copia:
        lineas.append(_centrar_ticket("COPIA"))
    lineas.extend([
        _centrar_ticket("Sistema POS - SENAEMPRESA"),
        LINEA_TERMICA,
    ])

    lineas.extend(_campo_ticket(etiqueta_documento, f"{id_factura:04d}"))
    lineas.extend(_campo_ticket("Fecha", fecha_actual))
    lineas.extend(_campo_ticket("Cliente", nombre_cliente))
    lineas.extend(_campo_ticket("Documento", doc_cliente))
    lineas.extend(_campo_ticket("Atendido por", nombre_usuario))

    if mostrar_precios:
        lineas.extend(_campo_ticket("Pago", metodo_pago_txt))
    elif metodo_pago_txt != "-":
        lineas.extend(_campo_ticket("Motivo", metodo_pago_txt))

    if mostrar_precios and es_mixto:
        lineas.extend(_dinero_ticket("Efectivo:", efectivo or 0))
        lineas.extend(_dinero_ticket("Transferencia:", transferencia or 0))

    lineas.extend([LINEA_TERMICA, "PRODUCTOS"])

    for p in productos:
        nombre = str(p.get("nombre", "-"))
        cantidad = p.get("cantidad", 1)
        unidad = str(p.get("unidad", "UND"))
        precio = p.get("precio", 0)
        subtotal = p.get("subtotal", 0)
        empresa = str(p.get("lugar", "-"))

        lineas.append("")
        lineas.extend(_envolver(f"{nombre} Cod: {p.get('id', '-')}") )

        if mostrar_precios:
            cantidad_linea = f"{_cantidad_texto(cantidad)} {unidad} x {_moneda(precio)} = {_moneda(subtotal)}"
            lineas.extend(_envolver(cantidad_linea))
        else:
            lineas.extend(_campo_ticket("Cantidad", f"{_cantidad_texto(cantidad)} {unidad}"))

        lineas.extend(_campo_ticket("Empresa", empresa))

    if mostrar_precios:
        desglose = {}
        for p in productos:
            empresa = str(p.get("lugar", "SenaEmpresa"))
            desglose[empresa] = desglose.get(empresa, 0) + p.get("subtotal", 0)

        lineas.extend([LINEA_TERMICA, "DESGLOSE POR EMPRESA"])
        for empresa, valor in desglose.items():
            lineas.extend(_dinero_ticket(f"{empresa[:16]}:", valor))

        subtotal_calc = sum(p.get("subtotal", 0) for p in productos)
        lineas.extend([LINEA_TERMICA])
        lineas.extend(_dinero_ticket("Subtotal:", subtotal_calc))
        lineas.extend(_dinero_ticket("Descuento:", 0))
        lineas.extend(_dinero_ticket("TOTAL:", total))

        if es_mixto:
            lineas.extend(_dinero_ticket("Efectivo:", efectivo or 0))
            lineas.extend(_dinero_ticket("Transferencia:", transferencia or 0))

        lineas.extend(_dinero_ticket("Recibido:", dinero_recibido))
        lineas.extend(_dinero_ticket("Cambio:", cambio))

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
    impresora = nombre_impresora or _buscar_impresora_xprinter()
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
    metodo_pago_txt = str(metodo_pago) if metodo_pago is not None else "-"
    if isinstance(metodo_pago, dict):
        if efectivo is None:
            efectivo = metodo_pago.get("efectivo")
        if transferencia is None:
            transferencia = metodo_pago.get("transferencia")
        metodo_pago_txt = metodo_pago.get("tipo", "Mixto")

    es_mixto = "mixto" in metodo_pago_txt.lower()

    if fecha_actual:
        try:
            fecha_actual = datetime.strptime(str(fecha_actual), "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %I:%M %p")
        except Exception:
            fecha_actual = str(fecha_actual)
    else:
        fecha_actual = datetime.now().strftime("%d/%m/%Y %I:%M %p")

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
    try:
        carpeta = _carpeta_facturas(prefijo_archivo)
        ruta_pdf = os.path.join(carpeta, f"{prefijo_archivo}_{id_factura:04d}.pdf")

        # Alto dinamico aproximado segun cantidad de productos
        alto_ticket = max(160 * mm, (120 + len(productos) * 18) * mm)

        doc = SimpleDocTemplate(
            ruta_pdf,
            pagesize=(ANCHO_TICKET, alto_ticket),
            leftMargin=MARGEN_TICKET,
            rightMargin=MARGEN_TICKET,
            topMargin=4 * mm,
            bottomMargin=4 * mm,
        )

        estilos = getSampleStyleSheet()

        # ---------------- ESTILOS ----------------

        estilo_titulo = ParagraphStyle(
            "titulo_ticket",
            parent=estilos["Title"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=9,
            alignment=1,
            spaceAfter=2,
        )

        estilo_centro = ParagraphStyle(
            "centro_ticket",
            parent=estilos["Normal"],
            fontName="Helvetica",
            fontSize=6,
            leading=7,
            alignment=1,
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

        # ---------------- ENCABEZADO ----------------

        # Logo pequeño
        logo_resuelto = _ruta_recurso(logo_path)
        if os.path.exists(logo_resuelto):
            try:
                elementos.append(Image(logo_resuelto, width=18 * mm, height=18 * mm, hAlign="CENTER"))
                elementos.append(Spacer(1, 2 * mm))
            except Exception:
                pass

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

        if mostrar_precios and es_mixto:
            # En pago mixto muestro separado cuanto fue en efectivo y transferencia
            efectivo_val = float(efectivo) if efectivo is not None else 0.0
            transferencia_val = float(transferencia) if transferencia is not None else 0.0
            elementos.append(Paragraph(f"<b>Efectivo:</b> {_moneda(efectivo_val)}", estilo_normal))
            elementos.append(Paragraph(f"<b>Transferencia:</b> {_moneda(transferencia_val)}", estilo_normal))

        elementos.append(Paragraph(LINEA_TICKET, estilo_centro))
        elementos.append(Paragraph("PRODUCTOS", estilo_bold))

        # ---------------- PRODUCTOS ----------------

        # Productos en formato angosto
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

        # Desglose por empresa
        desglose = {}
        for p in productos:
            # Agrupo el valor vendido por cada SenaEmpresa o lugar del producto
            empresa = str(p.get("lugar", "SenaEmpresa"))
            desglose[empresa] = desglose.get(empresa, 0) + p.get("subtotal", 0)

        if mostrar_precios:
            elementos.append(Paragraph("DESGLOSE POR EMPRESA", estilo_bold))

            for empresa, valor in desglose.items():
                tabla_empresa = Table(
                    [[empresa[:18], _moneda(valor)]],
                    colWidths=[21 * mm, ANCHO_CONTENIDO - (21 * mm)],
                )
                tabla_empresa.setStyle(TableStyle([
                    ("FONTSIZE", (0, 0), (-1, -1), 6),
                    ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                    ("TOPPADDING", (0, 0), (-1, -1), 1),
                ]))
                elementos.append(tabla_empresa)

            elementos.append(Paragraph(LINEA_TICKET, estilo_centro))

        # ---------------- TOTALES ----------------

        if mostrar_precios:
            subtotal_calc = sum(p.get("subtotal", 0) for p in productos)

            totales = [
                ["Subtotal:", _moneda(subtotal_calc)],
                ["Descuento:", "$0"],
                ["TOTAL:", _moneda(total)],
            ]

            if es_mixto:
                efectivo_val = float(efectivo) if efectivo is not None else 0.0
                transferencia_val = float(transferencia) if transferencia is not None else 0.0
                totales.append(["Efectivo:", _moneda(efectivo_val)])
                totales.append(["Transferencia:", _moneda(transferencia_val)])

            totales.append(["Recibido:", _moneda(dinero_recibido)])
            totales.append(["Cambio:", _moneda(cambio)])

            tabla_totales = Table(
                totales,
                colWidths=[18 * mm, ANCHO_CONTENIDO - (18 * mm)],
            )
            tabla_totales.setStyle(TableStyle([
                ("FONTSIZE", (0, 0), (-1, -1), 6),
                ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold"),
                ("FONTSIZE", (0, 2), (-1, 2), 8),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("LINEABOVE", (0, 2), (-1, 2), 0.7, colors.black),
                ("LINEBELOW", (0, 2), (-1, 2), 0.7, colors.black),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]))
            elementos.append(tabla_totales)

        # ---------------- PIE DE PAGINA ----------------

        elementos.append(Spacer(1, 4 * mm))
        mensaje_final = "Gracias por su compra" if mostrar_precios else "Documento de remision"
        elementos.append(Paragraph(mensaje_final, estilo_centro))
        elementos.append(Paragraph("Numeró de atencion: 3125290330", estilo_centro) )
        elementos.append(Paragraph("HORARIO DE ATENCION 8:00AM-3:30PM", estilo_centro))

        doc.build(elementos)

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
    Mantiene compatibilidad con llamadas antiguas.
    La impresion principal ahora se hace como ticket termico RAW.
    """
    if not os.path.exists(ruta_pdf):
        print(f"No se encontró el archivo: {ruta_pdf}")
        return False

    _abrir_archivo(ruta_pdf)
    return True
