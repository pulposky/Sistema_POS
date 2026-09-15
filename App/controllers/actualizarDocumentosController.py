"""
Controlador de Actualización de Documentos
============================================
Módulo encargado de la lógica de negocio para cargar y actualizar documentos
ya existentes en el sistema (ventas, compras y remisiones).

Este controlador actúa como puente entre la vista de edición y los
controladores específicos de cada tipo de documento. Centraliza la
carga de documentos sin duplicar lógica en la vista.

Flujo típico:
1. La vista llama a cargar_documento(tipo, numero) para obtener los datos.
2. El usuario modifica los datos en la interfaz.
3. La vista llama a actualizar_documento(tipo, numero, cabecera, productos)
   para guardar los cambios en la BD.
"""

"""Reglas de negocio para cargar y actualizar ventas, compras y remisiones."""
from models.actualizarDocumentosModel import actualizar_documento as persistir_actualizacion
from controllers.ventasController import cargar_factura, parsear_notas_empresa
from controllers.comprasController import cargar_compra
from controllers.remisionController import cargar_remision


def cargar_documento(tipo, numero):
    """
    Carga un documento existente desde la BD según su tipo y número.

    Delega la carga al controlador específico del tipo de documento:
    - 'VENTA': usa cargar_factura() de ventasController.
    - 'COMPRA': usa cargar_compra() de comprasController.
    - 'REMISION': usa cargar_remision() de remisionController.

    Normaliza la respuesta a un formato unificado con las claves:
    - 'cabecera': datos de la cabecera del documento (factura, compra o remisión).
    - 'tercero': datos del cliente o proveedor asociado.
    - 'productos': lista de productos del documento.

    Esto permite que la vista de edición funcione de forma genérica
    para los tres tipos de documento sin necesidad de lógica condicional.

    Args:
        tipo (str|None): Tipo de documento ('VENTA', 'COMPRA', 'REMISION').
            Se normaliza a mayúsculas. Si es None o vacío, retorna None.
        numero (int|str): Número/ID del documento a cargar.

    Returns:
        dict|None: Diccionario con 'cabecera', 'tercero' y 'productos',
            o None si el tipo es inválido o no se encuentra el documento.
    """
    tipo = (tipo or "").upper()
    if tipo == "VENTA":
        datos = cargar_factura(numero)
        if datos:
            cabecera = datos["factura"]
            # Formateo las notas por empresa en texto legible para el campo editable
            notas = parsear_notas_empresa(cabecera.get("notas"))
            if notas:
                cabecera["notas"] = " | ".join(
                    f"{emp}: {txt}" for emp, txt in notas.items()
                )
            else:
                cabecera["notas"] = ""
            return {"cabecera": cabecera, "tercero": datos["cliente"], "productos": datos["productos"]}
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
    """
    Guarda los cambios realizados a un documento existente en la BD.

    Delega la persistencia al modelo actualizarDocumentosModel, que se
    encarga de actualizar tanto la cabecera como los detalles/productos
    del documento.

    Args:
        tipo (str): Tipo de documento ('VENTA', 'COMPRA', 'REMISION').
        numero (int|str): Número/ID del documento a actualizar.
        cabecera (dict): Datos actualizados de la cabecera del documento.
        productos (list[dict]): Lista actualizada de productos del documento.

    Returns:
        bool: True si la actualización fue exitosa, False si hubo error.
    """
    return persistir_actualizacion(tipo, numero, cabecera, productos)
