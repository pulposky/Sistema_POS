"""
Controlador de Consulta de Documentos
======================================
Módulo encargado de la lógica de negocio para consultar y filtrar documentos
del sistema (ventas, compras y remisiones). Proporciona una vista unificada
de todos los documentos emitidos.

Responsabilidades principales:
- Listar todos los documentos sin filtros.
- Aplicar filtros combinados por número, tercero, usuario, tipo, fechas y producto.
- Soportar un modo detallado que muestra ventas a nivel de línea de producto.

El modo detallado ("VENTAS DETALLADAS") usa obtener_ventas_detalladas() que
retorna una fila por cada producto vendido, a diferencia del modo normal que
retorna una fila por factura/documento.
"""

from models.facturasModel import obtener_documentos, obtener_ventas_detalladas
from datetime import datetime

# Controlador para consultas de documentos.
# Aplica filtros y organiza la información mostrada en la vista de facturas.
def listar_documentos():
    """
    Obtiene la lista completa de todos los documentos del sistema.

    Retorna documentos sin ningún filtro aplicado. Se usa como punto de
    partida antes de aplicar filtros en filtrar_documentos.

    Returns:
        list[dict]: Lista de documentos con campos como 'numero', 'tipo',
            'tercero', 'usuario', 'fecha', 'productos', etc.
    """
    return obtener_documentos()


def filtrar_documentos(
    numero="", tercero="", usuario="", tipo="TODOS",
    fecha_inicio="", fecha_fin="", producto=""
):
    """
    Filtra la lista de documentos según múltiples criterios de búsqueda.

    Todos los filtros son opcionales y se aplican de forma acumulativa (AND).
    Si no se pasa un filtro, ese criterio no se aplica.

    Filtros disponibles:
    - numero: busca coincidencia parcial en el número del documento.
    - tercero: busca coincidencia parcial (case-insensitive) en el nombre
      del cliente/proveedor.
    - usuario: busca coincidencia parcial (case-insensitive) en el nombre
      del usuario que creó el documento.
    - tipo: filtra por tipo exacto ('VENTA', 'COMPRA', 'REMISION') o 'TODOS'
      para no filtrar. 'VENTAS DETALLADAS' activa el modo detallado.
    - fecha_inicio/fecha_fin: rango de fechas en formato 'DD/MM/YYYY'.
      La fecha_fin se extiende a las 23:59:59 para incluir todo el día.
    - producto: busca coincidencia parcial (case-insensitive) en el nombre
      del producto asociado al documento.

    El modo detallado ("VENTAS DETALLADAS") cambia la fuente de datos:
    usa obtener_ventas_detalladas() que retorna filas por producto, no por factura.
    En este modo, el filtro de tipo no se aplica (ya que todas las filas son ventas),
    y el filtro de producto busca en el campo 'producto' en lugar de 'productos'.

    Args:
        numero (str): Número del documento a buscar.
        tercero (str): Nombre del cliente o proveedor.
        usuario (str): Nombre del usuario.
        tipo (str): Tipo de documento. Default 'TODOS'.
        fecha_inicio (str): Fecha de inicio en formato 'DD/MM/YYYY'.
        fecha_fin (str): Fecha de fin en formato 'DD/MM/YYYY'.
        producto (str): Nombre del producto a buscar.

    Returns:
        list[dict]: Lista de documentos que cumplen todos los filtros.
    """
    # --- MODO DETALLADO ---
    # Si el tipo es "VENTAS DETALLADAS", uso una fuente de datos diferente
    # que retorna una fila por cada producto vendido
    if tipo == "VENTAS DETALLADAS":
        documentos = obtener_ventas_detalladas()
    else:
        documentos = obtener_documentos()

    resultado = []
    # Parseo las fechas de inicio y fin de los filtros
    dt_inicio = None
    dt_fin = None
    if fecha_inicio:
        try:
            dt_inicio = datetime.strptime(fecha_inicio, "%d/%m/%Y")
        except ValueError:
            pass
    if fecha_fin:
        try:
            dt_fin = datetime.strptime(fecha_fin, "%d/%m/%Y")
            # Extiendo la fecha fin a las 23:59:59 para incluir todo el día
            dt_fin = dt_fin.replace(hour=23, minute=59, second=59)
        except ValueError:
            pass

    # Recorro cada documento y aplico los filtros secuencialmente
    for doc in documentos:
        # Filtro por número (coincidencia parcial)
        if numero and numero not in str(doc["numero"]):
            continue
        # Filtro por tercero (case-insensitive)
        if tercero and tercero.lower() not in str(doc.get("tercero", "")).lower():
            continue
        # Filtro por usuario (case-insensitive)
        if usuario and usuario.lower() not in str(doc.get("usuario", "")).lower():
            continue

        # Solo aplicar filtro de tipo cuando NO es detallado
        # En modo detallado todas las filas son ventas, no tiene sentido filtrar
        if tipo not in ("TODOS", "VENTAS DETALLADAS"):
            if doc["tipo"] != tipo:
                continue

        # Filtro por rango de fechas
        if dt_inicio and doc["fecha"] < dt_inicio:
            continue
        if dt_fin and doc["fecha"] > dt_fin:
            continue

        # Filtro por producto
        # En modo detallado busca en 'producto' (campo individual)
        # En modo normal busca en 'productos' (campo concatenado de todos)
        if producto:
            campo_producto = (
                doc.get("producto", "")
                if tipo == "VENTAS DETALLADAS"
                else doc.get("productos", "")
            )
            if producto.lower() not in str(campo_producto).lower():
                continue

        resultado.append(doc)

    return resultado
