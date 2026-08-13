from datetime import datetime
from models.ventasModel import (

# Controlador de ventas.
# Aquí van las reglas de negocio relacionadas con facturas, totales y carga de datos.    
    obtener_todas_facturas,
    obtener_factura_por_id,
    obtener_detalles_factura,
    obtener_cliente_por_id,
    obtener_producto_por_id,
    eliminar_factura,
    guardar_factura,
)
from utils.generarFactura import generar_factura_pdf, imprimir_factura_datos


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
    if float(cantidad).is_integer():
        return str(int(cantidad))
    return f"{cantidad:.3f}".rstrip("0").rstrip(".")


# ---------------------------------------------------
# Devuelve un resumen sencillo de los totales de la venta
# ---------------------------------------------------
def calcular_resumen_venta(productos):
    subtotal_total = sum(
        float(p.get("cantidad", 0)) * float(p.get("precio", 0))
        for p in productos
    )
    descuento_valor = sum(
        (float(p.get("cantidad", 0)) * float(p.get("precio", 0)))
        * (float(p.get("descuento", 0)) / 100)
        for p in productos
    )
    return {
        "subtotal": subtotal_total,
        "descuento": descuento_valor,
        "total": subtotal_total - descuento_valor,
    }


# ---------------------------------------------------
# Prepara un producto para agregarse a la venta con
# cantidad, descuento y subtotal calculados
# ---------------------------------------------------
def preparar_producto_venta(producto, cantidad=None):
    producto_venta = dict(producto)
    cantidad_valor = float(cantidad if cantidad is not None else producto_venta.get("cantidad", 1))
    producto_venta["cantidad"] = cantidad_valor
    producto_venta["descuento"] = max(
        0,
        min(100, float(producto_venta.get("descuento", 0)))
    )
    producto_venta["subtotal"] = max(
        0,
        cantidad_valor * float(producto_venta.get("precio", 0))
        * (1 - producto_venta["descuento"] / 100)
    )
    return producto_venta


# ---------------------------------------------------
# Actualiza la cantidad y el subtotal de un producto
# ---------------------------------------------------
def actualizar_cantidad_producto(producto, nueva_cantidad):
    producto["cantidad"] = float(nueva_cantidad)
    producto["subtotal"] = max(
        0,
        float(producto["cantidad"]) * float(producto.get("precio", 0))
        * (1 - float(producto.get("descuento", 0)) / 100)
    )
    return producto


# ---------------------------------------------------
# Actualiza el descuento y el subtotal de un producto
# ---------------------------------------------------
def actualizar_descuento_producto(producto, nuevo_descuento):
    producto["descuento"] = max(0, min(100, float(nuevo_descuento)))
    producto["subtotal"] = max(
        0,
        float(producto.get("cantidad", 0)) * float(producto.get("precio", 0))
        * (1 - producto["descuento"] / 100)
    )
    return producto


# ---------------------------------------------------
# Agrega un producto a la lista de venta
# ---------------------------------------------------
def agregar_producto_a_venta(productos, producto):
    producto_preparado = preparar_producto_venta(producto)
    productos.append(producto_preparado)
    return producto_preparado


# ---------------------------------------------------
# Elimina un producto de la lista de venta
# ---------------------------------------------------
def quitar_producto_de_venta(productos, index):
    if 0 <= index < len(productos):
        productos.pop(index)
    return productos


# ---------------------------------------------------
# Calcula el stock restante luego de agregar una cantidad
# ---------------------------------------------------
def obtener_stock_restante(producto):
    try:
        return float(producto.get("stock", 0)) - float(producto.get("cantidad", 0))
    except (TypeError, ValueError):
        return 0


# ---------------------------------------------------
# Formatea el stock para mostrarlo sin decimales innecesarios
# ---------------------------------------------------
def formatear_stock(stock):
    if isinstance(stock, float) and stock.is_integer():
        return str(int(stock))
    return str(stock)


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
        "notas": pago.get("notas", ""),
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
        "usuario_factura": {
            "nombre": factura["nombre_usuario"]
        }
    }


def imprimir_factura_consultada(id_venta, usuario):
    datos = cargar_factura(id_venta)
    if not datos:
        return None

    factura = datos["factura"]

    if imprimir_factura_datos(
        id_factura=id_venta,
        cliente=datos["cliente"],
        usuario=datos["usuario_factura"],
        productos=datos["productos"],
        total=factura.get("total", 0),
        metodo_pago=factura.get("metodo_pago", ""),
        dinero_recibido=factura.get("dinero_recibido", 0),
        cambio=factura.get("cambio", 0),
        titulo_documento="FACTURA DE VENTA",
        mostrar_precios=True,
        fecha_actual=factura.get("fecha"),
        es_copia=True,
    ):
        return True
    return None


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
