import os
import sys
import subprocess
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle,
    Paragraph, Spacer, Image
)


ANCHO_TICKET = 58 * mm


def _carpeta_facturas():
    # Carpeta donde se guardan todos los PDF generados por el sistema
    base = os.path.join(
        os.path.expanduser("~"),
        "OneDrive",
        "Documents",
        "Proyecto",
        "Facturas"
    )
    os.makedirs(base, exist_ok=True)
    return base


def _abrir_archivo(ruta):
    # Abre el PDF automaticamente
    try:
        if sys.platform.startswith("win"):
            os.startfile(ruta)
    except Exception as err:
        print(f"No se pudo abrir el PDF: {err}")


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
    logo_path="App/assets/Logo_sena.png",
    efectivo=None,
    transferencia=None,
    titulo_documento="FACTURA DE VENTA",
    prefijo_archivo="factura",
    mostrar_precios=True,
):
    try:
        carpeta = _carpeta_facturas()
        ruta_pdf = os.path.join(carpeta, f"{prefijo_archivo}_{id_factura:04d}.pdf")

        # Alto dinamico aproximado segun cantidad de productos
        alto_ticket = max(160 * mm, (120 + len(productos) * 18) * mm)

        doc = SimpleDocTemplate(
            ruta_pdf,
            pagesize=(ANCHO_TICKET, alto_ticket),
            leftMargin=3 * mm,
            rightMargin=3 * mm,
            topMargin=4 * mm,
            bottomMargin=4 * mm,
        )

        estilos = getSampleStyleSheet()

        # ---------------- ESTILOS ----------------

        estilo_titulo = ParagraphStyle(
            "titulo_ticket",
            parent=estilos["Title"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=10,
            alignment=1,
            spaceAfter=2,
        )

        estilo_centro = ParagraphStyle(
            "centro_ticket",
            parent=estilos["Normal"],
            fontName="Helvetica",
            fontSize=7,
            leading=8,
            alignment=1,
        )

        estilo_normal = ParagraphStyle(
            "normal_ticket",
            parent=estilos["Normal"],
            fontName="Helvetica",
            fontSize=7,
            leading=8,
        )

        estilo_bold = ParagraphStyle(
            "bold_ticket",
            parent=estilo_normal,
            fontName="Helvetica-Bold",
        )

        elementos = []

        # ---------------- ENCABEZADO ----------------

        # Logo pequeño
        if os.path.exists(logo_path):
            try:
                elementos.append(Image(logo_path, width=18 * mm, height=18 * mm, hAlign="CENTER"))
                elementos.append(Spacer(1, 2 * mm))
            except Exception:
                pass

        elementos.append(Paragraph(titulo_documento, estilo_titulo))
        elementos.append(Paragraph("Sistema POS - SENAEMPRESA", estilo_centro))
        elementos.append(Paragraph("-" * 32, estilo_centro))

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

        elementos.append(Paragraph("-" * 32, estilo_centro))
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

            cantidad_txt = (
                str(int(cantidad))
                if isinstance(cantidad, (int, float)) and cantidad == int(cantidad)
                else str(cantidad)
            )

            elementos.append(Spacer(1, 1 * mm))
            elementos.append(Paragraph(f"<b>{nombre}</b>", estilo_normal))
            elementos.append(Paragraph(f"Cod: {p.get('id', '-')}", estilo_normal))
            if mostrar_precios:
                elementos.append(Paragraph(f"{cantidad_txt} {unidad} x {_moneda(precio)}", estilo_normal))
            else:
                elementos.append(Paragraph(f"Cantidad: {cantidad_txt} {unidad}", estilo_normal))
            elementos.append(Paragraph(f"Empresa: {empresa}", estilo_normal))

            if mostrar_precios:
                fila_subtotal = Table(
                    [["Subtotal", _moneda(subtotal)]],
                    colWidths=[25 * mm, 24 * mm],
                )
                fila_subtotal.setStyle(TableStyle([
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 7),
                    ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                    ("TOPPADDING", (0, 0), (-1, -1), 1),
                ]))
                elementos.append(fila_subtotal)

        elementos.append(Paragraph("-" * 32, estilo_centro))

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
                    colWidths=[28 * mm, 21 * mm],
                )
                tabla_empresa.setStyle(TableStyle([
                    ("FONTSIZE", (0, 0), (-1, -1), 7),
                    ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                    ("TOPPADDING", (0, 0), (-1, -1), 1),
                ]))
                elementos.append(tabla_empresa)

            elementos.append(Paragraph("-" * 32, estilo_centro))

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
                colWidths=[27 * mm, 22 * mm],
            )
            tabla_totales.setStyle(TableStyle([
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold"),
                ("FONTSIZE", (0, 2), (-1, 2), 10),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("LINEABOVE", (0, 2), (-1, 2), 0.7, colors.black),
                ("LINEBELOW", (0, 2), (-1, 2), 0.7, colors.black),
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
            _abrir_archivo(ruta_pdf)

        return ruta_pdf

    except Exception as err:
        print(f"Error generando PDF: {err}")
        import traceback
        traceback.print_exc()
        return None
