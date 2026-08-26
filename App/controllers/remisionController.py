"""
Controlador de Remisiones
==========================
Módulo encargado de la lógica de negocio del módulo de remisiones de salida.
Las remisiones son documentos que registran la salida de productos sin generar
una venta (no hay cobro). Se usan para retiros por transformación, deterioro,
consumo interno o donación.

Responsabilidades principales:
- Preparar y validar productos para la remisión.
- Calcular resumen de cantidades (sin totales monetarios en la mayoría de casos).
- Confirmar una remisión: guardar en BD y generar el PDF.
- Cargar remisiones existentes para consulta o reimpresión.
- Listar y eliminar remisiones.

Diferencia con ventas:
- Las remisiones NO generan cobro (total siempre es 0).
- Se asocian a un tipo de retiro (transformación, deterioro, etc.).
- El PDF se genera sin precios visibles (mostrar_precios=False).
- No maneja dinero recibido ni cambio.
"""

from datetime import datetime
from models.remisionesModel import (
    guardar_remision,
    obtener_todas_remisiones,
    obtener_remision_por_id,
    obtener_detalles_remision,
    eliminar_remision,
)

# Controlador de remisiones.
# Mantiene la lógica de preparación, resumen y generación de remisiones.
from models.ventasModel import obtener_cliente_por_id, obtener_producto_por_id
from utils.generarFactura import generar_factura_pdf, imprimir_factura_datos


# Guardo aqui las opciones para no repetirlas en la vista.
def obtener_opciones_remision():
    """
    Retorna la lista de tipos de remisión disponibles.

    Estas opciones se usan para llenar el selector de tipo de remisión
    en la vista. Cada opción representa una razón de salida de productos.

    Returns:
        list[str]: Lista de tipos de remisión válidos:
            - 'Retiro Transformacion'
            - 'Retiro por Deterioro'
            - 'Retiro Para Consumo internos - Degustacion'
            - 'Retiro por Donacion'
    """
    return [
        "Retiro Transformacion",
        "Retiro por Deterioro",
        "Retiro Para Consumo internos - Degustacion",
        "Retiro por Donacion",
    ]


# Formateo la cantidad para que si es entero no salga con .0.
def formatear_cantidad(cantidad):
    """
    Formatea una cantidad numérica eliminando decimales innecesarios.

    Si es un entero (por ejemplo 5.0), retorna '5'. Si tiene decimales
    relevantes, muestra hasta 3 cifras decimales sin ceros a la derecha.

    Args:
        cantidad (int|float): Cantidad a formatear.

    Returns:
        str: Cantidad formateada como cadena.
    """
    if float(cantidad).is_integer():
        return str(int(cantidad))
    return f"{cantidad:.3f}".rstrip("0").rstrip(".")


# Calculo el resumen que se muestra en el panel derecho.
def calcular_resumen(productos):
    """
    Calcula el resumen de la remisión para el panel lateral derecho.

    A diferencia de ventas/compras, el resumen de remisiones solo muestra:
    - Cantidad de productos distintos.
    - Cantidad total de unidades (suma de todas las cantidades).

    NO calcula totales monetarios porque las remisiones no generan cobro.

    Args:
        productos (list[dict]): Lista de productos en la remisión.

    Returns:
        dict: {'productos': int, 'cantidad_total': str}
    """
    cantidad_total = sum(float(p.get("cantidad", 0) or 0) for p in productos)

    return {
        "productos": len(productos),
        "cantidad_total": formatear_cantidad(cantidad_total),
    }


# Preparo el producto para remision, manteniendo el precio y subtotal
# cuando la vista lo requiera.
def preparar_producto_remision(producto, incluir_precios=True):
    """
    Prepara un producto del catálogo para ser incluido en una remisión.

    Crea una copia del producto y calcula el subtotal basado en cantidad * precio.

    El parámetro 'incluir_precios' controla si se muestran precios en la remisión:
    - True: se calcula subtotal = cantidad * precio (el precio viene del catálogo).
    - False: se fuerza precio y subtotal a 0 (para remisiones sin valor monetario).

    Args:
        producto (dict): Producto del catálogo.
        incluir_precios (bool): Si True, incluye precio y subtotal calculados.
            Default es True.

    Returns:
        dict: Copia del producto adaptada para la remisión.
    """
    producto_remision = producto.copy()
    if incluir_precios:
        cantidad = float(producto_remision.get("cantidad", 1))
        producto_remision["subtotal"] = cantidad * float(producto_remision.get("precio", 0))
    else:
        producto_remision["precio"] = 0
        producto_remision["subtotal"] = 0
    return producto_remision


# Actualiza la cantidad y el subtotal del producto en la remision.
def actualizar_cantidad_producto_remision(producto, nueva_cantidad):
    """
    Actualiza la cantidad de un producto en la remisión y recalcula su subtotal.

    Se usa cuando el usuario modifica la cantidad desde la interfaz.

    Args:
        producto (dict): Producto actual en la remisión (se modifica in-place).
        nueva_cantidad (int|float): Nueva cantidad ingresada.

    Returns:
        dict: El mismo diccionario 'producto' modificado.
    """
    producto["cantidad"] = float(nueva_cantidad)
    producto["subtotal"] = float(producto["cantidad"]) * float(producto.get("precio", 0))
    return producto


# Agrega un producto organizado a la lista de remision.
def agregar_producto_a_remision(productos, producto):
    """
    Agrega un producto a la lista de productos de la remisión actual.

    Llama a preparar_producto_remision con incluir_precios=True para
    calcular el subtotal antes de agregar a la lista.

    Args:
        productos (list[dict]): Lista acumulativa de productos de la remisión.
        producto (dict): Producto del catálogo a agregar.

    Returns:
        dict: El producto preparado que se agregó.
    """
    producto_preparado = preparar_producto_remision(producto, incluir_precios=True)
    productos.append(producto_preparado)
    return producto_preparado


# Elimina un producto de la lista de remision.
def quitar_producto_de_remision(productos, index):
    """
    Elimina un producto de la lista de remisión por su índice.

    Valida que el índice esté en rango para evitar errores.

    Args:
        productos (list[dict]): Lista de productos de la remisión.
        index (int): Posición del producto a eliminar (0-based).

    Returns:
        list[dict]: La misma lista modificada.
    """
    if 0 <= index < len(productos):
        productos.pop(index)
    return productos


# Guardo la remision y genero el PDF.
def confirmar_remision(tipo_remision, productos, cliente, usuario, notas=""):
    """
    Confirma y guarda una remisión completa en la base de datos.

    Flujo:
    1. Arma el diccionario de cabecera con fecha, tipo, cliente, usuario y notas.
    2. Llama a guardar_remision para persistir cabecera y detalles en BD.
    3. Si fue exitoso, genera el PDF de la remisión.
    4. Retorna el ID de la remisión y la ruta del PDF.

    El PDF se genera con:
    - titulo_documento="REMISION"
    - mostrar_precios=False (no se ven precios en la remisión)
    - total=0 (no hay cobro)
    - prefijo_archivo="remision" (para distinguir el nombre del archivo)

    Args:
        tipo_remision (str): Tipo de remisión (una de las opciones de
            obtener_opciones_remision).
        productos (list[dict]): Productos de la remisión.
        cliente (dict|None): Datos del cliente. Si es None, usa id=1 (genérico).
        usuario (dict): Usuario logueado. Debe tener 'id_usuario'.
        notas (str): Observaciones adicionales sobre la remisión. Default vacío.

    Returns:
        dict|None: {'id_remision': int, 'ruta_pdf': str} o None si falla.
    """
    remision_datos = {
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tipo_remision": tipo_remision,
        "id_cliente": cliente["id_cliente"] if cliente else 1,
        "id_usuario": usuario.get("id_usuario", 1),
        "notas": notas,
    }

    # Guardo la remisión en la BD
    id_remision = guardar_remision(remision_datos, productos)

    if not id_remision:
        return None

    # Genero el PDF sin precios visiblesm
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
    """
    Carga una remisión completa desde la base de datos por su ID.

    Flujo:
    1. Busca la cabecera de la remisión.
    2. Obtiene los detalles (productos) de la remisión.
    3. Busca los datos del cliente.
    4. Para cada detalle, busca la info del producto en el catálogo.

    A diferencia de ventas y compras, aquí NO se incluye precio ni subtotal
    en los productos cargados (ya que las remisiones no manejan precios).

    Args:
        id_remision (int): ID de la remisión a cargar.

    Returns:
        dict|None: Diccionario con:
            - 'remision': dict con datos de la cabecera.
            - 'cliente': dict con datos del cliente.
            - 'productos': list[dict] con los productos (sin precios).
          Retorna None si no se encuentra.
    """
    remision = obtener_remision_por_id(id_remision)
    if not remision:
        return None

    detalles = obtener_detalles_remision(id_remision)
    cliente = obtener_cliente_por_id(remision["id_cliente"])
    productos = []

    for detalle in detalles:
        # Busco el producto en el catálogo para nombre, unidad y lugar
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
    """
    Reimprime una remisión que ya fue guardada previamente.

    Carga la remisión desde la BD y genera la impresión.
    Se marca como 'es_copia=True' y no muestra precios.

    Args:
        id_remision (int): ID de la remisión a imprimir.
        usuario (dict): Datos del usuario actual.

    Returns:
        bool|None: True si la impresión fue exitosa, None si falló.
    """
    datos = cargar_remision(id_remision)
    if not datos:
        return None

    remision = datos["remision"]

    if imprimir_factura_datos(
        id_factura=id_remision,
        cliente=datos["cliente"],
        usuario={
            "nombre": remision["nombre_usuario"]
        },
        productos=datos["productos"],
        total=0,
        metodo_pago=remision.get("tipo_remision", "REMISION"),
        dinero_recibido=0,
        cambio=0,
        efectivo=0,
        transferencia=0,
        titulo_documento="REMISION",
        mostrar_precios=False,
        fecha_actual=remision.get("fecha"),
        es_copia=True,
    ):
        return True
    return None


# Listo todas las remisiones para consultar con F6 y F7.
def listar_remisiones():
    """
    Obtiene la lista de todas las remisiones registradas en la BD.

    Se usa en la pantalla de consulta de remisiones (teclas F6/F7).

    Returns:
        list[dict]: Lista de remisiones con sus datos de cabecera.
    """
    return obtener_todas_remisiones()


# Borro la remision actual junto con sus detalles.
def borrar_remision(id_remision):
    """
    Elimina una remisión de la base de datos por su ID.

    Elimina tanto la cabecera como los detalles asociados.
    Se usa desde la pantalla de consulta.

    Args:
        id_remision (int): ID de la remisión a eliminar.

    Returns:
        bool: True si se eliminó correctamente, False si hubo error.
    """
    return eliminar_remision(id_remision)
