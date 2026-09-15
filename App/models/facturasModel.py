"""
Módulo de consulta de documentos del sistema POS.
Este archivo genera informes consolidados de todos los documentos
comerciales del sistema (ventas, compras y remisiones) en una lista
unificada para su visualización en la interfaz.

Funcionalidades:
  - obtener_documentos(): Lista consolidada de ventas, compras y remisiones
  - obtener_ventas_detalladas(): Lista desglosada de ventas con productos

Ambas funciones construyen diccionarios con un formato estándar para
que la capa de presentación pueda mostrar los datos de forma homogénea,
independientemente del tipo de documento.
"""

# Importa la función de conexión a la base de datos MySQL
from database.bd import conectar


def _notas_legible(notas):
    """
    Convierte las notas de una venta a texto legible.

    Las notas nuevas pueden guardarse como JSON por empresa:
        {"SenaEmpresa": "...", "Campesena": "..."}
    Las notas antiguas son texto plano. Esta función normaliza
    ambas a una cadena legible para los reportes.

    Args:
        notas: Contenido de la columna notas (o None).

    Returns:
        str: Texto legible de las notas.
    """
    if not notas:
        return ""
    texto = str(notas).strip()
    if not texto:
        return ""
    try:
        data = __import__("json").loads(texto)
        if isinstance(data, dict):
            return " | ".join(
                f"{k}: {v}" for k, v in data.items() if str(v).strip()
            )
    except (ValueError, TypeError):
        pass
    return texto

# Modelo para consultar documentos y movimientos del sistema.

def obtener_documentos():
    """
    Genera una lista consolidada y ordenada de todos los documentos
    comerciales del sistema: ventas, compras y remisiones.

    Este método consulta las tres tablas de documentos principales,
    construye un diccionario estándar para cada uno con los campos:
      tipo, numero, fecha, tercero, usuario, total, productos

    Donde:
      - tipo: 'VENTA', 'COMPRA' o 'REMISION'
      - numero: ID del documento
      - tercero: nombre del cliente o proveedor (según tipo)
      - usuario: nombre del usuario que creó el documento
      - productos: lista de nombres de productos separados por coma

    Los documentos se ordenan por fecha descendente (más recientes primero).

    Retorna:
        list[dict]: Lista de diccionarios con los documentos ordenados.
        Retorna lista vacía si hay error de conexión o si no hay documentos.
    """

    # Inicializa la lista de documentos como vacía
    documentos = []

    # Inicializa conexión y cursor como None para manejo seguro en finally
    conexion = None
    cursor = None

    # Bloque try/except/finally para manejo robusto de errores
    try:
        # Conecta a la base de datos
        conexion = conectar()

        # Si la conexión falla, retorna lista vacía con mensaje de error
        if conexion is None:
            print("[ERROR] conectar() devolvió None")
            return documentos

        # Cursor diccionario para acceder a columnas por nombre
        cursor = conexion.cursor(dictionary=True)

        # Obtener clientes, proveedores y usuarios
        # Se consultan las tablas de catálogo para construir diccionarios
        # de búsqueda rápida (mapeo ID -> nombre) que se usan después
        # para resolver los nombres de los terceros y usuarios

        # Diccionario de clientes: {id_cliente: nombre}
        cursor.execute("SELECT id_cliente, nombre FROM clientes")
        clientes = {c['id_cliente']: c['nombre'] for c in cursor.fetchall()}

        # Diccionario de proveedores: {id_proveedor: nombre}
        cursor.execute("SELECT id_proveedor, nombre FROM proveedores")
        proveedores = {p['id_proveedor']: p['nombre'] for p in cursor.fetchall()}

        # Diccionario de usuarios: {id_usuario: nombre}
        cursor.execute("SELECT id_usuario, nombre FROM usuarios")
        usuarios = {u['id_usuario']: u['nombre'] for u in cursor.fetchall()}

        # ========== VENTAS ==========
        # Consulta todas las ventas con sus campos principales
        cursor.execute("SELECT id_venta, fecha, total, id_cliente, id_usuario, notas FROM venta")
        ventas = cursor.fetchall()

        # Para cada venta, se consultan los productos asociados
        for venta in ventas:
            # Consulta SQL con JOIN para obtener los nombres de los productos
            # vendidos en esta factura específica
            cursor.execute("""
                SELECT p.nombre
                FROM detalle_venta dv
                JOIN producto p ON p.id_producto = dv.id_producto
                WHERE dv.id_venta = %s
            """, (venta['id_venta'],))

            # Extrae solo los nombres de los productos en una lista
            productos = [p['nombre'] for p in cursor.fetchall()]

            # Construye el diccionario estándar para esta venta
            # Se usa .get() con valor por defecto '-' por si no se encuentra
            # el cliente o usuario en el diccionario de catálogo
            documentos.append({
                'tipo':      'VENTA',
                'numero':    venta['id_venta'],
                'fecha':     venta['fecha'],
                'tercero':   clientes.get(venta['id_cliente'], '-'),
                'usuario':   usuarios.get(venta['id_usuario'], '-'),
                'total':     venta['total'],
                'productos': ', '.join(productos) if productos else '-',
                'notas':     _notas_legible(venta.get('notas', '')),
            })

        # ========== COMPRAS ==========
        # Consulta todas las compras con sus campos principales
        cursor.execute("SELECT id_compra, fecha, total, id_proveedor, id_usuario FROM compras")
        compras = cursor.fetchall()

        # Para cada compra, se consultan los productos asociados
        for compra in compras:
            # Consulta SQL con JOIN para obtener los nombres de los productos
            # comprados en esta orden específica
            cursor.execute("""
                SELECT p.nombre
                FROM detalle_compras dc
                JOIN producto p ON p.id_producto = dc.id_producto
                WHERE dc.id_compra = %s
            """, (compra['id_compra'],))

            # Extrae los nombres de los productos
            productos = [p['nombre'] for p in cursor.fetchall()]

            # Construye el diccionario estándar para esta compra
            # Para compras, el tercero es el proveedor (no el cliente)
            documentos.append({
                'tipo':      'COMPRA',
                'numero':    compra['id_compra'],
                'fecha':     compra['fecha'],
                'tercero':   proveedores.get(compra['id_proveedor'], '-'),
                'usuario':   usuarios.get(compra['id_usuario'], '-'),
                'total':     compra['total'],
                'productos': ', '.join(productos) if productos else '-',
                'notas':     ''
            })

        # ========== REMISIONES ==========
        # Consulta todas las remisiones con sus campos principales
        # Las remisiones no tienen campo 'total' en la tabla base
        cursor.execute("SELECT id_remision, fecha, id_cliente, id_usuario FROM remision")
        remisiones = cursor.fetchall()

        # Para cada remisión, se consultan los productos asociados
        for remision in remisiones:
            # Consulta SQL con JOIN para obtener los nombres de los productos
            # remitidos en esta remisión específica
            cursor.execute("""
                SELECT p.nombre
                FROM detalle_remision dr
                JOIN producto p ON p.id_producto = dr.id_producto
                WHERE dr.id_remision = %s
            """, (remision['id_remision'],))

            # Extrae los nombres de los productos
            productos = [p['nombre'] for p in cursor.fetchall()]

            # Construye el diccionario estándar para esta remisión
            # Las remisiones no tienen total, se establece en 0
            # El tercero es el cliente al que se le remitió
            documentos.append({
                'tipo':      'REMISION',
                'numero':    remision['id_remision'],
                'fecha':     remision['fecha'],
                'tercero':   clientes.get(remision['id_cliente'], '-'),
                'usuario':   usuarios.get(remision['id_usuario'], '-'),
                'total':     0,
                'productos': ', '.join(productos) if productos else '-',
                'notas':     ''
            })

        # Ordena todos los documentos por fecha descendente
        # reverse=True pone los más recientes primero
        documentos.sort(key=lambda x: x['fecha'], reverse=True)

    except Exception as err:
        # Si ocurre cualquier error, imprime el traceback completo
        # para facilitar la depuración del error
        import traceback
        traceback.print_exc()
        print(f"[ERROR obtener_documentos] {err}")

    finally:
        # Bloque finally: se ejecuta SIEMPRE para garantizar
        # la liberación de recursos de la base de datos
        try:
            # Verifica que cursor y conexión existan antes de cerrarlos
            # para evitar errores si la conexión falló al inicio
            if cursor:
                cursor.close()
            if conexion:
                conexion.close()
        except Exception:
            # Si incluso el cierre falla, simplemente se ignora
            # para no enmascarar el error original
            pass

    # SIEMPRE retorna lista (nunca None)
    # Incluso si hubo error, retorna la lista vacía inicial
    return documentos



def obtener_ventas_detalladas():
    """
    Genera una lista desglosada de ventas con cada producto como ítem separado.
    A diferencia de obtener_documentos() que agrupa productos en una cadena,
    esta función crea un registro por cada producto vendido, mostrando
    cantidad, precio unitario y subtotal de cada uno.

    Ideal para generar reportes detallados de ventas o exportar datos
    a hojas de cálculo donde cada línea representa un producto vendido.

    Retorna:
        list[dict]: Lista de diccionarios, uno por cada producto vendido,
        con los campos: tipo, numero, fecha, tercero, usuario, producto,
        cantidad, precio_unitario, subtotal.
        Retorna lista vacía si hay error.
    """

    # Inicializa la lista de documentos
    documentos = []

    # Inicializa conexión y cursor como None
    conexion = None
    cursor = None

    # Bloque try/except/finally para manejo seguro de errores
    try:
        # Conecta a la base de datos
        conexion = conectar()

        # Si la conexión falla, retorna lista vacía
        if conexion is None:
            print("[ERROR] conectar() devolvió None")
            return documentos

        # Cursor diccionario
        cursor = conexion.cursor(dictionary=True)

        # Construye diccionarios de búsqueda para resolver nombres
        # de clientes y usuarios por su ID

        # Diccionario de clientes: {id_cliente: nombre}
        cursor.execute("SELECT id_cliente, nombre FROM clientes")
        clientes = {c['id_cliente']: c['nombre'] for c in cursor.fetchall()}

        # Diccionario de usuarios: {id_usuario: nombre}
        cursor.execute("SELECT id_usuario, nombre FROM usuarios")
        usuarios = {u['id_usuario']: u['nombre'] for u in cursor.fetchall()}

        # Consulta SQL compleja con múltiples JOINs que cruza:
        # - venta (cabecera de la venta)
        # - detalle_venta (productos de cada venta)
        # - producto (datos del producto)
        # Esto retorna UNA FILA POR CADA PRODUCTO VENDIDO, no una fila por venta
        cursor.execute("""
            SELECT
                v.id_venta,
                v.fecha,
                v.id_cliente,
                v.id_usuario,
                v.notas,
                p.nombre           AS producto,
                dv.cantidad        AS cantidad,
                dv.precio_unitario AS precio_unitario,
                dv.subtotal        AS subtotal
            FROM venta v
            JOIN detalle_venta dv ON dv.id_venta = v.id_venta
            JOIN producto p       ON p.id_producto = dv.id_producto
            ORDER BY v.fecha DESC, v.id_venta DESC, p.nombre ASC
        """)

        # Itera sobre cada fila del resultado (cada producto vendido)
        for r in cursor.fetchall():
            # Construye un diccionario con el formato estándar expandido
            # que incluye información del producto a nivel de línea
            documentos.append({
                'tipo':            'VENTA DETALLADA',
                'numero':          r['id_venta'],
                'fecha':           r['fecha'],
                'tercero':         clientes.get(r['id_cliente'], '-'),
                'usuario':         usuarios.get(r['id_usuario'], '-'),
                'producto':        r['producto'],
                'cantidad':        r['cantidad'],
                'precio_unitario': r['precio_unitario'],
                'subtotal':        r['subtotal'],
                'notas':   _notas_legible(r.get('notas', '')),
            })

    except Exception as err:
        # Imprime el traceback completo para depuración
        import traceback
        traceback.print_exc()
        print(f"[ERROR obtener_ventas_detalladas] {err}")

    finally:
        # Garantiza la liberación de recursos siempre
        try:
            if cursor:
                cursor.close()
            if conexion:
                conexion.close()
        except Exception:
            # Ignora errores al cerrar para no enmascarar errores previos
            pass

    # Retorna la lista de documentos detallados (puede ser vacía)
    return documentos
