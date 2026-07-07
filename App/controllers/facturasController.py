from models.facturasModel import obtener_documentos, obtener_ventas_detalladas
from datetime import datetime

def listar_documentos():
    return obtener_documentos()


def filtrar_documentos(
    numero="", tercero="", usuario="", tipo="TODOS",
    fecha_inicio="", fecha_fin="", producto=""
):
    # --- MODO DETALLADO ---
    if tipo == "VENTAS DETALLADAS":
        documentos = obtener_ventas_detalladas()
    else:
        documentos = obtener_documentos()

    resultado = []
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
            dt_fin = dt_fin.replace(hour=23, minute=59, second=59)
        except ValueError:
            pass

    for doc in documentos:
        if numero and numero not in str(doc["numero"]):
            continue
        if tercero and tercero.lower() not in str(doc.get("tercero", "")).lower():
            continue
        if usuario and usuario.lower() not in str(doc.get("usuario", "")).lower():
            continue

        # Solo aplicar filtro de tipo cuando NO es detallado
        if tipo not in ("TODOS", "VENTAS DETALLADAS"):
            if doc["tipo"] != tipo:
                continue

        if dt_inicio and doc["fecha"] < dt_inicio:
            continue
        if dt_fin and doc["fecha"] > dt_fin:
            continue

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