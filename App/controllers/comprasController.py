from datetime import datetime
from models import comprasModel
from models.ventasModel import obtener_producto_por_id
from models.comprasModel import guardar_compra
from utils.generarFactura import generar_factura_pdf, imprimir_factura_datos


def calcular_total(productos):
    return sum(
        p.get("subtotal", 0)
        for p in productos
    )


def formatear_cantidad(cantidad):
    if float(cantidad).is_integer():
        return str(int(cantidad))
    return f"{cantidad:.3f}".rstrip("0").rstrip(".")


def confirmar_compra(proveedor, productos, usuario):

    total_valor = calcular_total(productos)
    compra_datos = {

        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total": total_valor,
        "id_proveedor": proveedor["id_proveedor"],
        "id_usuario": usuario.get("id_usuario", 1),
        "estado": "ACTIVA",
    }

    id_compra = guardar_compra(
        compra_datos,
        productos
    )

    if not id_compra:
        return None

    # GENERAR PDF
    ruta_pdf = generar_factura_pdf(
        id_factura=id_compra,
        cliente={
            "nombre": proveedor.get("nombre", "Proveedor"),
            "documento": proveedor.get("nit", "-")
        },

        usuario=usuario,
        productos=list(productos),
        total=total_valor,
        metodo_pago="COMPRA",
        dinero_recibido=total_valor,
        cambio=0,
        abrir=True,
        titulo_documento="FACTURA DE COMPRA",
        prefijo_archivo="compra",
    )

    return {
        "id_compra": id_compra,
        "ruta_pdf": ruta_pdf,
        "usuario_factura": {
            "nombre": compra_datos["nombre_usuario"]
        }
    }


def imprimir_compra_consultada(id_compra, usuario):
    datos = cargar_compra(id_compra)
    if not datos:
        return None

    compra = datos["compra"]
    proveedor = datos.get("proveedor") or {}

    if imprimir_factura_datos(
        id_factura=id_compra,
        cliente={
            "nombre": proveedor.get("nombre", "Proveedor"),
            "documento": proveedor.get("nit", "-")
        },
        usuario={
            "nombre": compra["nombre_usuario"]
        },
        productos=datos["productos"],
        total=compra.get("total", 0),
        metodo_pago="COMPRA",
        dinero_recibido=compra.get("total", 0),
        cambio=0,
        efectivo=0,
        transferencia=0,
        titulo_documento="FACTURA DE COMPRA",
        mostrar_precios=True,
        fecha_actual=compra.get("fecha"),
        es_copia=True,
    ):
        return True
    return None


def obtener_producto_stock(id_producto):
    return comprasModel.obtener_producto_stock(id_producto)


def listar_compras():
    return comprasModel.obtener_todas_compras()


def cargar_compra(id_compra):
    compra = comprasModel.obtener_compra_por_id(id_compra)
    if not compra:
        return None

    detalles = comprasModel.obtener_detalles_compra(id_compra)
    productos = []
    for detalle in detalles:
        producto = obtener_producto_por_id(detalle["id_producto"])
        productos.append({
            "id": detalle["id_producto"],
            "nombre": producto["nombre"] if producto else "Sin nombre",
            "cantidad": detalle["cantidad"],
            "unidad": producto["unidad"] if producto else "UND",
            "precio": detalle["precio_unitario"],
            "subtotal": detalle["subtotal"],
            "lugar": producto["lugar"] if producto else "-",
        })

    proveedor = None
    if compra.get("id_proveedor"):
        proveedor = comprasModel.obtener_proveedor_por_id(compra.get("id_proveedor"))

    return {
        "compra": compra,
        "proveedor": proveedor,
        "productos": productos,
    }


def anular_compra(id_compra):
    return comprasModel.anular_compra(id_compra)
