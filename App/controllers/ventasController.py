from datetime import datetime
from models.ventasModel import (
    obtener_todas_facturas,
    obtener_factura_por_id,
    obtener_detalles_factura,
    obtener_cliente_por_id,
    obtener_producto_por_id,
    eliminar_factura,
    guardar_factura,
)
from utils.generarFactura import generar_factura_pdf


# ---------------------------------------------------
# Calcula el total general sumando los subtotales
# de todos los productos agregados a la venta
# ---------------------------------------------------
def calcular_total(productos):

    return sum(
        p.get("subtotal", 0)
        for p in productos
    )


# ---------------------------------------------------
# Formatea la cantidad para que si es un número entero
# no muestre decimales innecesarios
# ---------------------------------------------------
def formatear_cantidad(cantidad):

    if isinstance(cantidad, float) and cantidad.is_integer():
        return str(int(cantidad))
    
    if isinstance(cantidad, int):
        return str(cantidad)

    return str(cantidad)


# ---------------------------------------------------
# Guarda la factura en la base de datos
# y genera automáticamente el PDF
# ---------------------------------------------------
def confirmar_factura(pago, productos, cliente, usuario):

    # Calculo el total final de la venta
    total_valor = calcular_total(productos)

    # Diccionario con los datos principales
    # que se guardarán en la factura
    factura_datos = {

        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total": total_valor,
        "metodo_pago": pago["metodo_pago"],
        "id_cliente": cliente["id_cliente"] if cliente else 1,
        "id_usuario": usuario.get("id_usuario", 1),
        "dinero_recibido": pago["dinero_recibido"],
        "cambio": pago["cambio"],
    }

    id_factura = guardar_factura(
        factura_datos,
        productos
    )

    if not id_factura:
        return None

    # Genero automáticamente el PDF
    ruta_pdf = generar_factura_pdf(

        id_factura=id_factura,
        cliente=cliente,
        usuario=usuario,
        productos=list(productos),
        total=total_valor,
        metodo_pago=pago["metodo_pago"],
        dinero_recibido=pago["dinero_recibido"],
        cambio=pago["cambio"],
        efectivo=pago.get("efectivo", 0),
        transferencia=pago.get("transferencia", 0),
        abrir=True,
    )

    return {
        "id_factura": id_factura,
        "ruta_pdf": ruta_pdf,
    }


# ---------------------------------------------------
# Carga una factura específica desde la base de datos
# junto con sus productos y cliente
# ---------------------------------------------------
def cargar_factura(id_venta):

    factura = obtener_factura_por_id(id_venta)

    if not factura:
        return None

    detalles = obtener_detalles_factura(id_venta)

    cliente = obtener_cliente_por_id(
        factura["id_cliente"]
    )

    productos = []

    for detalle in detalles:

        producto = obtener_producto_por_id(
            detalle["id_producto"]
        )
        productos.append({

            "id": detalle["id_producto"],
            "nombre": (
                producto["nombre"]
                if producto else "Sin nombre"
            ),
            "cantidad": detalle["cantidad"],
            "unidad": (
                producto["unidad"]
                if producto else "UND"
            ),
            "precio": detalle["precio_unitario"],
            "subtotal": detalle["subtotal"],
            "lugar": (
                producto["lugar"]
                if producto else "-"
            ),
        })
    return {

        "factura": factura,
        "cliente": cliente,
        "productos": productos,
    }


# ---------------------------------------------------
# Retorna todas las facturas registradas
# ---------------------------------------------------
def listar_facturas():
    return obtener_todas_facturas()


# ---------------------------------------------------
# Elimina una factura usando su ID
# ---------------------------------------------------
def borrar_factura(id_venta):
    return eliminar_factura(id_venta)