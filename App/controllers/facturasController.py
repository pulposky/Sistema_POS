from models.facturasModel import obtener_documentos
from datetime import datetime


def listar_documentos():
    """Lista todos los documentos sin filtros"""
    return obtener_documentos()


def filtrar_documentos(
    numero="",
    tercero="",
    usuario="",
    tipo="TODOS",
    fecha_inicio="",
    fecha_fin="",
    producto=""
):
    """
    Filtra documentos según los parámetros proporcionados
    
    Args:
        numero: Número de documento
        tercero: Nombre del cliente o proveedor
        usuario: Nombre del usuario
        tipo: Tipo de documento (VENTA, COMPRA, REMISION, TODOS)
        fecha_inicio: Fecha inicio en formato DD/MM/YYYY
        fecha_fin: Fecha fin en formato DD/MM/YYYY
        producto: Nombre del producto
    """
    
    documentos = obtener_documentos()
    resultado = []

    # Convertir fechas de texto a datetime si se proporcionan
    dt_inicio = None
    dt_fin = None
    
    if fecha_inicio:
        try:
            dt_inicio = datetime.strptime(fecha_inicio, "%d/%m/%Y")
        except ValueError:
            print(f"Formato de fecha inicio incorrecto: {fecha_inicio}")
    
    if fecha_fin:
        try:
            # Agregar 23:59:59 para incluir todo el día
            dt_fin = datetime.strptime(fecha_fin, "%d/%m/%Y")
            dt_fin = dt_fin.replace(hour=23, minute=59, second=59)
        except ValueError:
            print(f"Formato de fecha fin incorrecto: {fecha_fin}")

    for doc in documentos:
        # Filtrar por número
        if numero:
            if numero not in str(doc["numero"]):
                continue

        # Filtrar por tercero (cliente/proveedor)
        if tercero:
            nombre = str(doc.get("tercero", "")).lower()
            if tercero.lower() not in nombre:
                continue

        # Filtrar por usuario
        if usuario:
            nombre_usuario = str(doc.get("usuario", "")).lower()
            if usuario.lower() not in nombre_usuario:
                continue

        # Filtrar por tipo de documento
        if tipo != "TODOS":
            if doc["tipo"] != tipo:
                continue

        # Filtrar por rango de fechas
        if dt_inicio:
            if doc["fecha"] < dt_inicio:
                continue
        
        if dt_fin:
            if doc["fecha"] > dt_fin:
                continue

        # Filtrar por producto
        if producto:
            productos_doc = str(doc.get("productos", "")).lower()
            if producto.lower() not in productos_doc:
                continue

        # Si pasó todos los filtros, agregarlo al resultado
        resultado.append(doc)

    return resultado