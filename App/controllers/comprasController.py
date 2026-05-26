from datetime import datetime
from models import comprasModel
from models.ventasModel import obtener_producto_por_id


def calcular_total(productos):
    return sum(
        p.get("subtotal", 0)
        for p in productos
    )


def formatear_cantidad(cantidad):
    if isinstance(cantidad, float) and cantidad.is_integer():
        return str(int(cantidad))
    if isinstance(cantidad, int):
        return str(cantidad)
    return str(cantidad)


def confirmar_compra(usuario, productos, proveedor=None):
    total_valor = calcular_total(productos)
    compra_datos = {
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total": total_valor,
        "id_proveedor": (
            proveedor.get("id_proveedor")
            if proveedor and proveedor.get("id_proveedor") is not None
            else proveedor.get("id_cliente")
            if proveedor
            else None
        ),
        "id_usuario": usuario.get("id_usuario", 1),
        "estado": "ACTIVA",
    }
    return comprasModel.guardar_compra(compra_datos, productos)


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
        "productos": productos,
        "proveedor": proveedor,
    }


def anular_compra(id_compra):
    return comprasModel.anular_compra(id_compra)
