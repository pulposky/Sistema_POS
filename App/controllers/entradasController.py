"""
Controlador de Entradas
========================
Módulo encargado de la lógica de negocio para registrar entradas de productos
al inventario. Las entradas son movimientos que aumentan el stock de productos
sin estar asociados a una compra (son registros manuales de entrada).

Responsabilidades principales:
- Preparar productos para la entrada (solo cantidad, sin precios ni descuentos).
- Validar que las cantidades sean mayores a cero.
- Guardar la entrada completa (cabecera + detalles) en la base de datos.

Diferencia con compras:
- Las entradas NO tienen proveedor asociado.
- Las entradas NO manejan precios ni descuentos (solo cantidad).
- Las entradas son registros simples de entrada de stock.
- El formulario de entrada pide: fecha, observación y productos con cantidades.
"""

from datetime import datetime
from models.entradasModel import guardar_entrada


def preparar_producto_entrada(producto, cantidad=None):
    """Copia el producto y conserva solamente la cantidad usada en la entrada.

    A diferencia de ventas y compras, las entradas NO calculan subtotal ni
    manejan descuento. Solo se conserva la cantidad que entra al inventario.

    Args:
        producto (dict): Producto del catálogo. Debe tener 'id_producto' y nombre.
        cantidad (int|float|None): Cantidad a ingresar. Si es None, usa la del dict.

    Returns:
        dict: Copia del producto solo con la cantidad actualizada.
    """
    producto_entrada = dict(producto)
    producto_entrada["cantidad"] = float(
        cantidad if cantidad is not None else producto_entrada.get("cantidad", 1)
    )
    return producto_entrada


def agregar_producto_a_entrada(productos, producto):
    """
    Agrega un producto a la lista de productos de la entrada actual.

    Llama a preparar_producto_entrada para calcular la cantidad
    antes de agregar a la lista.

    Args:
        productos (list[dict]): Lista acumulativa de productos de la entrada.
        producto (dict): Producto del catálogo a agregar.

    Returns:
        dict: El producto preparado que se agregó.
    """
    producto_entrada = preparar_producto_entrada(producto)
    productos.append(producto_entrada)
    return producto_entrada


def actualizar_cantidad_producto_entrada(producto, cantidad):
    """
    Actualiza la cantidad de un producto en la entrada.

    Valida que la cantidad sea mayor a cero. Si es menor o igual,
    lanza ValueError con un mensaje descriptivo.

    Args:
        producto (dict): Producto actual en la entrada (se modifica in-place).
        cantidad (int|float): Nueva cantidad a ingresar.

    Raises:
        ValueError: Si la cantidad es menor o igual a cero.
    """
    cantidad = float(cantidad)
    if cantidad <= 0:
        raise ValueError("La cantidad debe ser mayor que cero.")
    producto["cantidad"] = cantidad


def quitar_producto_de_entrada(productos, indice):
    """
    Elimina un producto de la lista de entrada por su índice.

    Valida que el índice esté en rango para evitar errores IndexError.

    Args:
        productos (list[dict]): Lista de productos de la entrada.
        indice (int): Posición del producto a eliminar (0-based).
    """
    if 0 <= indice < len(productos):
        productos.pop(indice)


def guardar_nueva_entrada(fecha, observacion, productos, usuario):
    """Valida los datos del formulario y delega la transacción al modelo.

    Esta función es el punto de entrada principal para guardar una entrada.
    Antes de guardar, realiza las siguientes validaciones:
    1. La lista de productos no puede estar vacía.
    2. Todos los productos deben tener cantidad mayor a cero.

    La fecha se parsea de 'YYYY-MM-DD' del formulario y se guarda con
    hora '00:00:00' (las entradas se registran como fechas sin hora específica).

    Args:
        fecha (str): Fecha de la entrada en formato 'YYYY-MM-DD'.
        observacion (str): Texto libre con observaciones sobre la entrada.
        productos (list[dict]): Lista de productos a ingresar. Cada uno debe
            tener 'cantidad' mayor a cero.
        usuario (dict): Usuario logueado. Debe tener 'id_usuario'.

    Raises:
        ValueError: Si no hay productos o si alguna cantidad es <= 0.

    Returns:
        int|None: ID de la entrada creada, o None si falla la inserción.
    """
    if not productos:
        raise ValueError("Agrega al menos un producto.")

    # Convierto la fecha del formulario al formato SQL con hora 00:00:00
    fecha_entrada = datetime.strptime(fecha, "%Y-%m-%d").strftime("%Y-%m-%d 00:00:00")
    for producto in productos:
        if float(producto.get("cantidad", 0)) <= 0:
            raise ValueError("Todas las cantidades deben ser mayores que cero.")

    # Delego la inserción al modelo (cabecera + detalles en transacción)
    return guardar_entrada(
        {
            "fecha": fecha_entrada,
            "observacion": observacion.strip(),
            "id_usuario": usuario.get("id_usuario", 1),
        },
        productos,
    )
