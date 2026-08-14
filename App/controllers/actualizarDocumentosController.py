"""Reglas de negocio para cargar y actualizar ventas, compras y remisiones."""
from models.actualizarDocumentosModel import actualizar_documento as persistir_actualizacion
from controllers.ventasController import cargar_factura
from controllers.comprasController import cargar_compra
from controllers.remisionController import cargar_remision


def cargar_documento(tipo, numero):
    tipo = (tipo or "").upper()
    if tipo == "VENTA":
        datos = cargar_factura(numero)
        if datos:
            return {"cabecera": datos["factura"], "tercero": datos["cliente"], "productos": datos["productos"]}
    elif tipo == "COMPRA":
        datos = cargar_compra(numero)
        if datos:
            return {"cabecera": datos["compra"], "tercero": datos["proveedor"], "productos": datos["productos"]}
    elif tipo == "REMISION":
        datos = cargar_remision(numero)
        if datos:
            return {"cabecera": datos["remision"], "tercero": datos["cliente"], "productos": datos["productos"]}
    return None


def actualizar_documento(tipo, numero, cabecera, productos):
    return persistir_actualizacion(tipo, numero, cabecera, productos)
