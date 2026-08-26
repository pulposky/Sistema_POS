"""
Módulo de remisiones del sistema POS.
Las remisiones son documentos de entrega de mercancía que no constituyen
una venta directa pero sí descuentan stock del inventario.
Se utilizan para registrar entregas a clientes como parte de pedidos
o acuerdos comerciales.

Este módulo maneja:
  - Guardado de remisiones con sus detalles
  - Consulta de remisiones y sus detalles
  - Anulación de remisiones
"""

# Importa la función de conexión a la base de datos MySQL
from database.bd import conectar

# =====================================================
# GUARDAR REMISION
# =====================================================

def guardar_remision(remision_datos, detalles):
    """
    Guarda una remisión completa con todos sus detalles en una transacción
    atómica. Si cualquier parte falla, se revierten todos los cambios.

    La remisión incluye:
    1. La cabecera con fecha, tipo, cliente, usuario y notas
    2. Cada producto remitido en 'detalle_remision'
    3. Descuento de stock para cada producto remitido

    Las remisiones siempre descuentan stock porque representan
    entrega física de mercancía al cliente.

    Parámetros:
        remision_datos (dict): Datos de la cabecera de la remisión.
            Claves: fecha, tipo_remision, id_cliente, id_usuario, notas.
        detalles (list[dict]): Lista de productos remitidos.
            Cada dict debe tener: id_producto (o id), cantidad.

    Retorna:
        int o None: El ID de la remisión creada, o None si ocurrió un error.
    """

    # Conecta a la base de datos
    conexion = conectar()

    # Crea cursor estándar para operaciones de escritura
    cursor = conexion.cursor()

    # Bloque try/except para manejo de errores y rollback
    try:
        # Consulta SQL para insertar la cabecera de la remisión
        # Almacena: fecha, tipo (ej: "venta", "pedido"), cliente, usuario y notas
        sql_remision = """
            INSERT INTO remision (fecha, tipo_remision, id_cliente, id_usuario, notas)
            VALUES (%s, %s, %s, %s, %s)
        """

        # Ejecuta el INSERT con los datos de la remisión
        # id_usuario default es 1 (administrador)
        # notas default es cadena vacía
        cursor.execute(sql_remision, (
            remision_datos.get("fecha"),
            remision_datos.get("tipo_remision"),
            remision_datos.get("id_cliente"),
            remision_datos.get("id_usuario", 1),
            remision_datetime.get("notas", ""),
        ))

        # Obtiene el ID auto-generado de la remisión recién insertada
        id_remision = cursor.lastrowid

        # Consulta SQL para insertar cada línea de detalle de remisión
        # Solo almacena: remisión padre, producto y cantidad (sin precio)
        sql_detalle = """
            INSERT INTO detalle_remision (id_remision, id_producto, cantidad)
            VALUES (%s, %s, %s)
        """

        # Itera sobre cada producto remitido
        for detalle in detalles:
            # Obtiene el ID del producto aceptando ambas claves posibles
            id_producto = detalle.get("id_producto") or detalle.get("id")

            # Cantidad remitida de este producto (default 1)
            cantidad = detalle.get("cantidad", 1)

            # Inserta el detalle de la remisión
            cursor.execute(sql_detalle, (
                id_remision,
                id_producto,
                cantidad,
            ))

            # Consulta SQL que descuenta la cantidad remitida del stock
            # Las remisiones RESTAN stock porque representan entrega de mercancía
            sql_actualizar_stock = """UPDATE producto SET stock = stock - %s WHERE id_producto = %s"""
            cursor.execute(sql_actualizar_stock, (cantidad, id_producto))

        # Confirma toda la transacción: remisión + detalles + descuento de stock
        conexion.commit()

        # Libera recursos
        cursor.close()
        conexion.close()

        # Retorna el ID de la remisión creada
        return id_remision
    except Exception as err:
        # Revierte TODA la transacción si algo falla
        conexion.rollback()

        # Libera recursos
        cursor.close()
        conexion.close()

        # Imprime el error para depuración
        print(f"Error al guardar remision: {err}")

        # Retorna None indicando fallo
        return None

# =====================================================
# OBTENER REMISIONES
# =====================================================

def obtener_todas_remisiones():
    """
    Recupera todas las remisiones registradas en el sistema.
    Las ordena por ID descendente (más recientes primero).

    Retorna:
        list[dict]: Lista de diccionarios con los campos: id_remision,
        fecha, tipo_remision, id_cliente, id_usuario, notas.
    """

    # Conecta a la base de datos
    conexion = conectar()

    # Cursor diccionario para acceder a columnas por nombre
    cursor = conexion.cursor(dictionary=True)

    # Consulta SQL que obtiene los campos relevantes de la tabla 'remision'
    # ORDER BY id_remision DESC ordena de la más reciente a la más antigua
    sql = """
        SELECT id_remision, fecha, tipo_remision, id_cliente, id_usuario, notas
        FROM remision
        ORDER BY id_remision DESC
    """

    # Ejecuta la consulta
    cursor.execute(sql)

    # Obtiene todas las filas
    resultado = cursor.fetchall()

    # Libera recursos
    cursor.close()
    conexion.close()

    # Retorna la lista de remisiones
    return resultado

# =====================================================
# OBTENER REMISION POR ID
# =====================================================

def obtener_remision_por_id(id_remision):
    """
    Obtiene los datos completos de una remisión específica por su ID.
    Incluye el nombre del usuario mediante un JOIN con 'usuarios'.

    Parámetros:
        id_remision (int): ID de la remisión a buscar.

    Retorna:
        dict o None: Diccionario con todos los campos de la remisión
        más el nombre del usuario, o None si no se encuentra.
    """

    # Conecta a la base de datos
    conexion = conectar()

    # Cursor diccionario
    cursor = conexion.cursor(dictionary=True)

    # Consulta SQL con INNER JOIN entre remision y usuarios
    # El JOIN trae el nombre del usuario que creó la remisión
    # Se incluye el campo 'estado' para verificar si está activa o anulada
    sql = """
        SELECT
            r.id_remision,
            r.fecha,
            r.tipo_remision,
            r.id_cliente,
            r.id_usuario,
            r.notas,
            r.estado,
            u.nombre AS nombre_usuario
        FROM remision r
        INNER JOIN usuarios u
            ON r.id_usuario = u.id_usuario
        WHERE r.id_remision = %s
    """

    # Ejecuta con el ID de la remisión
    cursor.execute(sql, (id_remision,))

    # Retorna un solo registro o None
    resultado = cursor.fetchone()

    # Libera recursos
    cursor.close()
    conexion.close()

    # Retorna los datos de la remisión
    return resultado

# =====================================================
# OBTENER DETALLES DE REMISION
# =====================================================

def obtener_detalles_remision(id_remision):
    """
    Obtiene todos los ítems (detalles) de una remisión específica.
    Cada detalle representa un producto remitido con su cantidad.

    Parámetros:
        id_remision (int): ID de la remisión cuyos detalles se desean obtener.

    Retorna:
        list[dict]: Lista de diccionarios con: id_detalle_remision,
        id_remision, id_producto, cantidad.
    """

    # Conecta a la base de datos
    conexion = conectar()

    # Cursor diccionario
    cursor = conexion.cursor(dictionary=True)

    # Consulta SQL que obtiene los detalles de remisión para una remisión específica
    # La tabla 'detalle_remision' almacena cada línea de producto de cada remisión
    sql = """
        SELECT id_detalle_remision, id_remision, id_producto, cantidad
        FROM detalle_remision
        WHERE id_remision = %s
    """

    # Ejecuta con el ID de la remisión
    cursor.execute(sql, (id_remision,))

    # Obtiene todos los detalles
    resultado = cursor.fetchall()

    # Libera recursos
    cursor.close()
    conexion.close()

    # Retorna la lista de detalles
    return resultado

# =====================================================
# ELIMINAR REMISION
# =====================================================

def eliminar_remision(id_remision):
    """
    Anula una remisión cambiando su estado a 'ANULADA'.
    NO elimina el registro físicamente para mantener el historial
    de auditoría del sistema.

    Parámetros:
        id_remision (int): ID de la remisión a anular.

    Retorna:
        bool: True si se anuló correctamente, False si ocurrió un error.
    """

    # Conecta a la base de datos
    conexion = conectar()

    # Crea cursor estándar
    cursor = conexion.cursor()

    # Bloque try/except para manejo de errores
    try:
        # SOLO CAMBIA EL ESTADO
        # Consulta SQL que cambia el estado de la remisión a 'ANULADA'
        # Es un UPDATE, no un DELETE, para preservar el registro histórico
        cursor.execute(
            """
            UPDATE remision
            SET estado = 'ANULADA'
            WHERE id_remision = %s
            """,
            (id_remision,)
        )

        # Confirma la transacción
        conexion.commit()

        # Libera recursos
        cursor.close()
        conexion.close()

        # Retorna True indicando éxito
        return True

    except Exception as err:
        # Revierte la transacción si hay error
        conexion.rollback()

        # Libera recursos
        cursor.close()
        conexion.close()

        # Imprime el error para depuración
        print(f"Error al anular remision: {err}")

        # Retorna False indicando fallo
        return False
