"""
Controlador de Ventas
======================
Módulo encargado de toda la lógica de negocio relacionada con el módulo de ventas
del punto de venta (POS). Gestiona la creación, consulta, edición y eliminación
de facturas de venta.

Responsabilidades principales:
- Preparar y validar productos antes de agregarlos a la venta.
- Calcular subtotales, descuentos y totales de la venta.
- Confirmar una venta: guardar en BD y generar el PDF de la factura.
- Cargar facturas existentes para consulta o reimpresión.
- Listar y eliminar facturas registradas.

Flujo típico de una venta:
1. El usuario agrega productos uno a uno (agregar_producto_a_venta).
2. Puede modificar cantidades y descuentos (actualizar_cantidad_producto,
   actualizar_descuento_producto).
3. Al confirmar, se llama a confirmar_factura que guarda en BD y genera el PDF.
4. La factura puede consultarse después con cargar_factura o imprimirse con
   imprimir_factura_consultada.
"""

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
    """
    Suma el campo 'subtotal' de cada producto en la lista.

    Args:
        productos (list[dict]): Lista de productos en la venta. Cada dict debe
            tener la clave 'subtotal' con el valor ya calculado.

    Returns:
        float: Suma de todos los subtotales (total de la venta antes de redondeos).
    """
    return sum(
        p.get("subtotal", 0)
        for p in productos
    )


# ---------------------------------------------------
# Formatea la cantidad para que si es un número entero
# no muestre decimales innecesarios
# ---------------------------------------------------
def formatear_cantidad(cantidad):
    """
    Convierte una cantidad numérica a string legible.

    Si la cantidad es un número entero (por ejemplo 5.0), retorna '5'.
    Si tiene decimales relevantes (por ejemplo 2.5), los muestra hasta 3
    decimales, eliminando ceros a la derecha.

    Args:
        cantidad (int|float): La cantidad a formatear.

    Returns:
        str: Cantidad formateada como cadena.
    """
    if float(cantidad).is_integer():
        return str(int(cantidad))
    return f"{cantidad:.3f}".rstrip("0").rstrip(".")


# ---------------------------------------------------
# Devuelve un resumen sencillo de los totales de la venta
# ---------------------------------------------------
def calcular_resumen_venta(productos):
    """
    Calcula el resumen financiero de la venta actual.

    Recorre todos los productos y calcula:
    - subtotal_total: suma de (cantidad * precio) de cada producto, sin descuento.
    - descuento_valor: suma del valor de descuento aplicado a cada producto.
    - total: subtotal_total - descuento_valor.

    Este resumen se muestra en el panel lateral derecho de la vista de ventas
    para que el cajero vea el desglose antes de confirmar.

    Args:
        productos (list[dict]): Lista de productos en la venta. Cada dict debe
            tener 'cantidad', 'precio' y 'descuento' (porcentaje, 0-100).

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


# ---------------------------------------------------
# Prepara un producto para agregarse a la venta con
# cantidad, descuento y subtotal calculados
# ---------------------------------------------------
def preparar_producto_venta(producto, cantidad=None):
    """
    Toma un producto del catálogo y lo adapta para la venta actual.

    Crea una copia del producto y le asigna:
    - 'cantidad': la que se pasa como parámetro o la que trae el dict (default 1).
    - 'descuento': se recorta al rango válido [0, 100] para evitar valores
      negativos o superiores al 100%.
    - 'subtotal': se calcula como cantidad * precio * (1 - descuento/100).
      Se fuerza a mínimo 0 para evitar subtotales negativos por datos erróneos.

    Esta función es el punto de entrada para agregar productos: tanto
    agregar_producto_a_venta como otros flujos la usan internamente.

    Args:
        producto (dict): Producto del catálogo. Debe tener 'precio'. Opcionalmente
            'cantidad', 'descuento'.
        cantidad (int|float|None): Cantidad a llevar. Si es None, se toma la del dict.

    Returns:
        dict: Copia del producto con cantidad, descuento y subtotal actualizados.
    """
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
    """
    Modifica la cantidad de un producto que ya está en la lista de venta
    y recalcula su subtotal.

    Se usa cuando el cajero cambia la cantidad desde la interfaz (campo editable
    en la tabla de productos).

    Fórmula del subtotal: cantidad * precio * (1 - descuento/100).
    El subtotal nunca puede ser negativo (mínimo 0).

    Args:
        producto (dict): Producto actual en la venta (se modifica in-place).
        nueva_cantidad (int|float): Nueva cantidad ingresada por el usuario.

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
def actualizar_descuento_producto(producto, nuevo_descuento):
    """
    Modifica el porcentaje de descuento de un producto en la venta
    y recalcula su subtotal.

    El descuento se valida para que esté en el rango [0, 100].
    Valores negativos se fuerzan a 0; valores mayores a 100 se fuerzan a 100.

    Se usa cuando el cajero cambia el descuento desde la interfaz.

    Args:
        producto (dict): Producto actual en la venta (se modifica in-place).
        nuevo_descuento (int|float): Porcentaje de descuento nuevo (0-100).

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


# ---------------------------------------------------
# Agrega un producto a la lista de venta
# ---------------------------------------------------
def agregar_producto_a_venta(productos, producto):
    """
    Agrega un producto a la lista de productos de la venta actual.

    Internamente llama a preparar_producto_venta para calcular cantidad,
    descuento y subtotal antes de insertarlo en la lista.

    La lista 'productos' se modifica in-place (se le hace append).

    Args:
        productos (list[dict]): Lista acumulativa de productos en la venta.
        producto (dict): Producto del catálogo a agregar.

    Returns:
        dict: El producto preparado que se agregó a la lista.
    """
    producto_preparado = preparar_producto_venta(producto)
    productos.append(producto_preparado)
    return producto_preparado


# ---------------------------------------------------
# Elimina un producto de la lista de venta
# ---------------------------------------------------
def quitar_producto_de_venta(productos, index):
    """
    Elimina un producto de la lista de venta por su índice.

    Se valida que el índice esté dentro del rango válido para evitar
    errores de IndexError. Si el índice es inválido, la lista no se modifica.

    Args:
        productos (list[dict]): Lista de productos de la venta.
        index (int): Posición del producto a eliminar (0-based).

    Returns:
        list[dict]: La misma lista 'productos' modificada.
    """
    if 0 <= index < len(productos):
        productos.pop(index)
    return productos


# ---------------------------------------------------
# Calcula el stock restante luego de agregar una cantidad
# ---------------------------------------------------
def obtener_stock_restante(producto):
    """
    Calcula cuánto stock queda de un producto después de vender la cantidad
    seleccionada.

    Fórmula: stock_del_producto - cantidad_seleccionada.

    Se usa en la vista para mostrar una advertencia visual cuando el stock
    restante es bajo o negativo (venta a crédito o sin stock suficiente).

    Args:
        producto (dict): Producto con claves 'stock' y 'cantidad'.

    Returns:
        float: Stock restante. Retorna 0 si hay error de conversión.
    """
    try:
        return float(producto.get("stock", 0)) - float(producto.get("cantidad", 0))
    except (TypeError, ValueError):
        return 0


# ---------------------------------------------------
# Formatea el stock para mostrarlo sin decimales innecesarios
# ---------------------------------------------------
def formatear_stock(stock):
    """
    Convierte el stock a string de forma legible.

    Si es un float entero (por ejemplo 10.0), lo muestra como '10'.
    Si tiene decimales reales, los mantiene.

    Args:
        stock (int|float): Valor de stock a formatear.

    Returns:
        str: Stock formateado.
    """
    if isinstance(stock, float) and stock.is_integer():
        return str(int(stock))
    return str(stock)


# ---------------------------------------------------
# Guarda la factura en la base de datos
# y genera automáticamente el PDF
# ---------------------------------------------------
def confirmar_factura(pago, productos, cliente, usuario):
    """
    Función principal que confirma y guarda una venta completa.

    Este es el flujo final de una venta. Hace lo siguiente:
    1. Calcula el total de la venta sumando subtotales.
    2. Arma el diccionario de datos de la cabecera (fecha, total, método de pago,
       cliente, usuario, dinero recibido, cambio y notas).
    3. Llama al modelo guardar_factura para persistir cabecera y detalles en BD.
    4. Si la inserción fue exitosa, genera automáticamente el PDF de la factura
       usando generar_factura_pdf.
    5. Retorna el ID de la factura y la ruta del PDF generado.

    Si la inserción falla (guardar_factura retorna None o 0), retorna None.

    Args:
        pago (dict): Datos del pago. Debe tener:
            - 'metodo_pago': str (ej: 'EFECTIVO', 'TARJETA', 'TRANSACCION')
            - 'dinero_recibido': float
            - 'cambio': float
            - 'notas': str (opcional)
            - 'efectivo': float (opcional, para pagos mixtos)
            - 'transferencia': float (opcional, para pagos mixtos)
        productos (list[dict]): Lista de productos vendidos con subtotal calculado.
        cliente (dict|None): Datos del cliente. Si es None, se usa id_cliente=1 (generico).
        usuario (dict): Datos del usuario logueado. Debe tener 'id_usuario'.

    Returns:
        dict|None: {'id_factura': int, 'ruta_pdf': str} o None si falla.
    """

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

    # Guardo la factura (cabecera + detalles) en la base de datos
    id_factura = guardar_factura(
        factura_datos,
        productos
    )

    if not id_factura:
        return None

    # Genero automáticamente el PDF
    # 'abrir=True' abre el PDF en el navegador después de generarlo
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
    """
    Carga una factura completa desde la base de datos por su ID.

    Este método se usa para:
    - Consultar una factura existente (pantalla de consulta con F5/F6).
    - Reimprimir una factura.
    - Editar una factura (carga los datos en la vista).

    El flujo es:
    1. Busca la cabecera de la factura (obtener_factura_por_id).
    2. Obtiene los detalles/productos de la factura (obtener_detalles_factura).
    3. Busca los datos del cliente (obtener_cliente_por_id).
    4. Para cada detalle, busca el nombre del producto en el catálogo
       para completar la información que no está en los detalles.

    Args:
        id_venta (int): ID de la factura a cargar.

    Returns:
        dict|None: Diccionario con:
            - 'factura': dict con datos de la cabecera.
            - 'cliente': dict con datos del cliente (o None).
            - 'productos': list[dict] con los productos de la factura.
            - 'usuario_factura': dict con el nombre del usuario que creó la factura.
          Retorna None si no se encuentra la factura.
    """

    # Busco la cabecera de la factura en la BD
    factura = obtener_factura_por_id(id_venta)

    if not factura:
        return None

    # Obtengo los detalles (líneas de productos) de la factura
    detalles = obtener_detalles_factura(id_venta)

    # Busco los datos del cliente asociado a la factura
    cliente = obtener_cliente_por_id(
        factura["id_cliente"]
    )

    # Armo la lista de productos completando info desde el catálogo
    productos = []

    for detalle in detalles:

        # Busco el producto original para obtener nombre, unidad y lugar
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
    """
    Reimprime una factura que ya fue guardada previamente.

    Carga la factura desde la BD con cargar_factura y luego llama a
    imprimir_factura_datos para generar la impresión física o vista previa.

    Se marca como 'es_copia=True' para que el documento impreso indique
    que es una copia, no el original.

    Args:
        id_venta (int): ID de la factura a imprimir.
        usuario (dict): Datos del usuario actual (para el encabezado del documento).

    Returns:
        bool|None: True si la impresión fue exitosa, None si falló.
    """
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
    """
    Obtiene la lista de todas las facturas de venta registradas en la BD.

    Se usa en la pantalla de consulta de facturas (tecla F5) para llenar
    la tabla con el historial de ventas.

    Returns:
        list[dict]: Lista de facturas con sus datos de cabecera.
    """
    return obtener_todas_facturas()


# ---------------------------------------------------
# Elimina una factura usando su ID
# ---------------------------------------------------
def borrar_factura(id_venta):
    """
    Elimina una factura de la base de datos por su ID.

    Elimina tanto la cabecera como los detalles asociados.
    Se usa desde la pantalla de consulta cuando el usuario selecciona
    una factura y presiona el botón de eliminar.

    Args:
        id_venta (int): ID de la factura a eliminar.

    Returns:
        bool: True si se eliminó correctamente, False si hubo error.
    """
    return eliminar_factura(id_venta)
