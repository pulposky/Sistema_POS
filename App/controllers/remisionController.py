from datetime import datetime
from models.remisionesModel import (
    guardar_remision,
    obtener_todas_remisiones,
    obtener_remision_por_id,
    obtener_detalles_remision,
    eliminar_remision,
)
from models.ventasModel import obtener_cliente_por_id, obtener_producto_por_id
from utils.generarFactura import generar_factura_pdf, imprimir_factura_datos


# Guardo aqui las opciones para no repetirlas en la vista.
def obtener_opciones_remision():
    return [
        "Retiro Transformacion",
        "Retiro por Deterioro",
        "Retiro Para Consumo internos - Degustacion",
        "Retiro por Donacion",
    ]


# Formateo la cantidad para que si es entero no salga con .0.
def formatear_cantidad(cantidad):
    if isinstance(cantidad, float) and cantidad.is_integer():
        return str(int(cantidad))
    if isinstance(cantidad, int):
        return str(cantidad)
    return str(cantidad)


# Calculo el resumen que se muestra en el panel derecho.
def calcular_resumen(productos):
    cantidad_total = sum(float(p.get("cantidad", 0) or 0) for p in productos)

    return {
        "productos": len(productos),
        "cantidad_total": formatear_cantidad(cantidad_total),
    }


# Preparo el producto para remision, sin precios ni subtotales.
def preparar_producto_remision(producto):
    producto_remision = producto.copy()
    producto_remision["precio"] = 0
    producto_remision["subtotal"] = 0
    return producto_remision


# Guardo la remision y genero el PDF.
def confirmar_remision(tipo_remision, productos, cliente, usuario, notas=""):
    remision_datos = {
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tipo_remision": tipo_remision,
        "id_cliente": cliente["id_cliente"] if cliente else 1,
        "id_usuario": usuario.get("id_usuario", 1),
        "notas": notas,
    }

    id_remision = guardar_remision(remision_datos, productos)

    if not id_remision:
        return None

    ruta_pdf = generar_factura_pdf(
        id_factura=id_remision,
        cliente=cliente,
        usuario=usuario,
        productos=list(productos),
        total=0,
        metodo_pago=tipo_remision,
        dinero_recibido=0,
        cambio=0,
        efectivo=0,
        transferencia=0,
        abrir=True,
        titulo_documento="REMISION",
        prefijo_archivo="remision",
        mostrar_precios=False,
    )

    return {
        "id_remision": id_remision,
        "ruta_pdf": ruta_pdf,
    }


# Cargo una remision guardada y dejo los datos listos para pintarlos en la tabla.
def cargar_remision(id_remision):
    remision = obtener_remision_por_id(id_remision)
    if not remision:
        return None

    detalles = obtener_detalles_remision(id_remision)
    cliente = obtener_cliente_por_id(remision["id_cliente"])
    productos = []

    for detalle in detalles:
        producto = obtener_producto_por_id(detalle["id_producto"])
        productos.append({
            "id": detalle["id_producto"],
            "nombre": producto["nombre"] if producto else "Sin nombre",
            "cantidad": detalle["cantidad"],
            "unidad": producto["unidad"] if producto else "UND",
            "lugar": producto["lugar"] if producto else "-",
        })

    return {
        "remision": remision,
        "cliente": cliente,
        "productos": productos,
    }


def imprimir_remision_consultada(id_remision, usuario):
    datos = cargar_remision(id_remision)
    if not datos:
        return None

    remision = datos["remision"]

    if imprimir_factura_datos(
        id_factura=id_remision,
        cliente=datos["cliente"],
        usuario=usuario,
        productos=datos["productos"],
        total=0,
        metodo_pago=remision.get("tipo_remision", "REMISION"),
        dinero_recibido=0,
        cambio=0,
        efectivo=0,
        transferencia=0,
        titulo_documento="REMISION",
        mostrar_precios=False,
    ):
        return True
    return None


# Listo todas las remisiones para consultar con F6 y F7.
def listar_remisiones():
    return obtener_todas_remisiones()


# Borro la remision actual junto con sus detalles.
def borrar_remision(id_remision):
    return eliminar_remision(id_remision)
