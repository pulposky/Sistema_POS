from datetime import datetime
from models.entradasModel import guardar_entrada


def preparar_producto_entrada(producto, cantidad=None):
    """Copia el producto y conserva solamente la cantidad usada en la entrada."""
    producto_entrada = dict(producto)
    producto_entrada["cantidad"] = float(
        cantidad if cantidad is not None else producto_entrada.get("cantidad", 1)
    )
    return producto_entrada


def agregar_producto_a_entrada(productos, producto):
    producto_entrada = preparar_producto_entrada(producto)
    productos.append(producto_entrada)
    return producto_entrada


def actualizar_cantidad_producto_entrada(producto, cantidad):
    cantidad = float(cantidad)
    if cantidad <= 0:
        raise ValueError("La cantidad debe ser mayor que cero.")
    producto["cantidad"] = cantidad


def quitar_producto_de_entrada(productos, indice):
    if 0 <= indice < len(productos):
        productos.pop(indice)


def guardar_nueva_entrada(fecha, observacion, productos, usuario):
    """Valida los datos del formulario y delega la transacción al modelo."""
    if not productos:
        raise ValueError("Agrega al menos un producto.")

    fecha_entrada = datetime.strptime(fecha, "%Y-%m-%d").strftime("%Y-%m-%d 00:00:00")
    for producto in productos:
        if float(producto.get("cantidad", 0)) <= 0:
            raise ValueError("Todas las cantidades deben ser mayores que cero.")

    return guardar_entrada(
        {
            "fecha": fecha_entrada,
            "observacion": observacion.strip(),
            "id_usuario": usuario.get("id_usuario", 1),
        },
        productos,
    )
