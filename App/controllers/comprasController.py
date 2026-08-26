"""
Controlador de Compras
=======================
Módulo encargado de la lógica de negocio del módulo de compras al proveedor.
Gestiona la creación, consulta, edición y anulación de órdenes de compra.

Responsabilidades principales:
- Preparar y validar productos para la compra.
- Calcular subtotales, descuentos y totales de la compra.
- Confirmar una compra: guardar en BD y generar el PDF.
- Cargar compras existentes para consulta o reimpresión.
- Listar y anular compras registradas.
- Consultar stock de productos.

Diferencia con ventasController:
- Las compras se asocian a un proveedor (no a un cliente).
- Las compras generan un movimiento de entrada de stock.
- El estado de una compra puede ser "ACTIVA" o "ANULADA".
- No maneja dinero recibido/cambio ya que es una compra a crédito o-transferencia.
"""

from datetime import datetime
from models import comprasModel

# Controlador de compras.
# Se encarga de preparar datos, calcular totales y gestionar la lógica de compra.
from models.ventasModel import obtener_producto_por_id
from models.comprasModel import guardar_compra
from utils.generarFactura import generar_factura_pdf, imprimir_factura_datos


def calcular_total(productos):
    """
    Suma el campo 'subtotal' de cada producto para obtener el total de la compra.

    Args:
        productos (list[dict]): Lista de productos en la compra.

    Returns:
        float: Total de la compra (suma de subtotales).
    """
    return sum(
        p.get("subtotal", 0)
        for p in productos
    )


def formatear_cantidad(cantidad):
    """
    Formatea una cantidad numérica para mostrarla sin decimales innecesarios.

    Si es entero (5.0), retorna '5'. Si tiene decimales, muestra hasta 3
    cifras decimales eliminando ceros a la derecha.

    Args:
        cantidad (int|float): Cantidad a formatear.

    Returns:
        str: Cantidad formateada como cadena.
    """
    if float(cantidad).is_integer():
        return str(int(cantidad))
    return f"{cantidad:.3f}".rstrip("0").rstrip(".")


def preparar_producto_compra(producto, cantidad=None):
    """
    Prepara un producto del catálogo para ser incluido en una compra.

    Crea una copia del producto y calcula:
    - 'cantidad': la cantidad a comprar (parámetro o valor del dict, default 1).
    - 'descuento': porcentaje de descuento recortado al rango [0, 100].
    - 'subtotal': cantidad * precio * (1 - descuento/100), mínimo 0.

    Esta función es el punto de entrada para agregar productos a la compra.

    Args:
        producto (dict): Producto del catálogo. Debe tener 'precio'.
        cantidad (int|float|None): Cantidad a comprar. Si es None, usa la del dict.

    Returns:
        dict: Copia del producto con cantidad, descuento y subtotal calculados.
    """
    producto_compra = dict(producto)
    cantidad_valor = float(cantidad if cantidad is not None else producto_compra.get("cantidad", 1))
    producto_compra["cantidad"] = cantidad_valor
    producto_compra["descuento"] = max(
        0,
        min(100, float(producto_compra.get("descuento", 0)))
    )
    producto_compra["subtotal"] = max(
        0,
        cantidad_valor * float(producto_compra.get("precio", 0))
        * (1 - producto_compra["descuento"] / 100)
    )
    return producto_compra


def actualizar_cantidad_producto_compra(producto, nueva_cantidad):
    """
    Actualiza la cantidad de un producto en la compra y recalcula su subtotal.

    Se usa cuando el usuario modifica la cantidad desde la interfaz de compra.

    Args:
        producto (dict): Producto actual en la compra (se modifica in-place).
        nueva_cantidad (int|float): Nueva cantidad ingresada.

    Returns:
        dict: El mismo diccionario 'producto' modificado.
    """
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
def actualizar_descuento_producto_compra(producto, nuevo_descuento):
    """
    Actualiza el porcentaje de descuento de un producto en la compra
    y recalcula su subtotal.

    El descuento se valida en el rango [0, 100]. Valores fuera de rango
    se ajustan automáticamente.

    Args:
        producto (dict): Producto actual en la compra (se modifica in-place).
        nuevo_descuento (int|float): Nuevo porcentaje de descuento.

    Returns:
        dict: El mismo diccionario 'producto' modificado.
    """
    producto["descuento"] = max(0, min(100, float(nuevo_descuento)))
    producto["subtotal"] = max(
        0,
        float(producto.get("cantidad", 0)) * float(producto.get("precio", 0))
        * (1 - producto["descuento"] / 100)
    )
    return producto


def calcular_resumen_compra(productos):
    """
    Calcula el resumen financiero de la compra actual.

    Desglose:
    - subtotal: suma de (cantidad * precio) de todos los productos, sin descuento.
    - descuento: suma del valor del descuento aplicado a cada producto.
    - total: subtotal - descuento.

    Se muestra en el panel lateral de la vista de compras.

    Args:
        productos (list[dict]): Lista de productos en la compra.

    Returns:
        dict: {'subtotal': float, 'descuento': float, 'total': float}
    """
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


def agregar_producto_a_compra(productos, producto):
    """
    Agrega un producto a la lista de productos de la compra actual.

    Llama internamente a preparar_producto_compra para calcular
    cantidad, descuento y subtotal antes de agregar a la lista.

    Args:
        productos (list[dict]): Lista acumulativa de productos de la compra.
        producto (dict): Producto del catálogo a agregar.

    Returns:
        dict: El producto preparado que se agregó.
    """
    producto_preparado = preparar_producto_compra(producto)
    productos.append(producto_preparado)
    return producto_preparado


def quitar_producto_de_compra(productos, index):
    """
    Elimina un producto de la lista de compra por su índice.

    Valida que el índice esté en rango para evitar errores.

    Args:
        productos (list[dict]): Lista de productos de la compra.
        index (int): Posición del producto a eliminar (0-based).

    Returns:
        list[def]: La misma lista modificada.
    """
    if 0 <= index < len(productos):
        productos.pop(index)
    return productos


def confirmar_compra(proveedor, productos, usuario):
    """
    Confirma y guarda una compra completa en la base de datos.

    Flujo:
    1. Calcula el total de la compra.
    2. Arma el diccionario de cabecera con fecha, total, proveedor, usuario y estado.
    3. Llama a guardar_compra para persistir cabecera y detalles en BD.
    4. Si fue exitoso, genera el PDF de la factura de compra.
    5. Retorna el ID de la compra, la ruta del PDF y datos del usuario.

    El estado inicial de toda compra es "ACTIVA".
    Se puede anular después con anular_compra.

    Args:
        proveedor (dict): Datos del proveedor. Debe tener 'id_proveedor',
            'nombre' y 'nit'.
        productos (list[dict]): Productos de la compra con subtotal calculado.
        usuario (dict): Usuario logueado. Debe tener 'id_usuario'.

    Returns:
        dict|None: {'id_compra': int, 'ruta_pdf': str, 'usuario_factura': dict}
            o None si falla la inserción.
    """

    total_valor = calcular_total(productos)
    compra_datos = {

        # Fecha actual en formato SQL
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total": total_valor,
        "id_proveedor": proveedor["id_proveedor"],
        "id_usuario": usuario.get("id_usuario", 1),
        # Toda compra inicia como ACTIVA, puede anularse después
        "estado": "ACTIVA",
    }

    # Persisto la compra en la BD (cabecera + detalles)
    id_compra = guardar_compra(
        compra_datos,
        productos
    )

    if not id_compra:
        return None

    # GENERAR PDF
    # Se adapta la interfaz del PDF de ventas para compras:
    # el proveedor se pasa como si fuera un 'cliente' y el método de pago es "COMPRA"
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
            # El nombre pertenece a la sesión del usuario, no a los datos
            # almacenados de la compra.
            "nombre": (
                usuario.get("nombre")
                or usuario.get("nombre_usuario")
                or "Usuario"
            )
        }
    }


def imprimir_compra_consultada(id_compra, usuario):
    """
    Reimprime una compra que ya fue guardada previamente.

    Carga la compra desde la BD y genera la impresión con imprimir_factura_datos.
    Se marca como 'es_copia=True' en el documento impreso.

    Args:
        id_compra (int): ID de la compra a imprimir.
        usuario (dict): Datos del usuario actual.

    Returns:
        bool|None: True si la impresión fue exitosa, None si falló.
    """
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
    """
    Consulta el stock actual de un producto específico en la BD.

    Se usa para mostrar el stock disponible antes de agregar un producto
    a la compra o para validaciones en tiempo real.

    Args:
        id_producto (int): ID del producto a consultar.

    Returns:
        float: Stock actual del producto.
    """
    return comprasModel.obtener_producto_stock(id_producto)


def listar_compras():
    """
    Obtiene la lista de todas las compras registradas en la BD.

    Se usa en la pantalla de consulta de compras (tecla F6/F7).

    Returns:
        list[dict]: Lista de compras con sus datos de cabecera.
    """
    return comprasModel.obtener_todas_compras()


def cargar_compra(id_compra):
    """
    Carga una compra completa desde la base de datos por su ID.

    Flujo:
    1. Busca la cabecera de la compra.
    2. Obtiene los detalles (productos) de la compra.
    3. Para cada detalle, busca la info del producto en el catálogo.
    4. Busca los datos del proveedor asociado.

    Se usa para consultar compras existentes, reimpresión o edición.

    Args:
        id_compra (int): ID de la compra a cargar.

    Returns:
        dict|None: Diccionario con:
            - 'compra': dict con datos de la cabecera.
            - 'proveedor': dict con datos del proveedor (o None).
            - 'productos': list[dict] con los productos de la compra.
          Retorna None si no se encuentra la compra.
    """
    compra = comprasModel.obtener_compra_por_id(id_compra)
    if not compra:
        return None

    detalles = comprasModel.obtener_detalles_compra(id_compra)
    productos = []
    for detalle in detalles:
        # Busco el producto en el catálogo para obtener nombre, unidad y lugar
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

    # Busco los datos del proveedor si la compra tiene uno asociado
    proveedor = None
    if compra.get("id_proveedor"):
        proveedor = comprasModel.obtener_proveedor_por_id(compra.get("id_proveedor"))

    return {
        "compra": compra,
        "proveedor": proveedor,
        "productos": productos,
    }


def anular_compra(id_compra):
    """
    Anula una compra existente en la base de datos.

    La anulación cambia el estado de la compra de "ACTIVA" a "ANULADA".
    Esto es una operación lógica, no elimina el registro de la BD.

    Se usa desde la pantalla de consulta cuando el usuario selecciona
    una compra y presiona el botón de anular.

    Args:
        id_compra (int): ID de la compra a anular.

    Returns:
        bool: True si se anuló correctamente, False si hubo error.
    """
    return comprasModel.anular_compra(id_compra)
