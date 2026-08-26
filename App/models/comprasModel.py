"""
Módulo de compras del sistema POS.
Contiene las operaciones de base de datos para la gestión de compras
a proveedores, incluyendo:
  - Búsqueda y creación de proveedores
  - Guardado de compras con sus detalles y actualización de stock
  - Anulación de compras
  - Consulta de compras, detalles y datos de proveedores

Las compras representan la adquisición de productos al proveedor,
lo que incrementa el stock de los productos en el inventario.
"""

# Importa la función de conexión a la base de datos MySQL
from database.bd import conectar

# Modelo de compras.
# Contiene las operaciones de base de datos para compras y proveedores.

def buscar_proveedor(texto):
    """
    Busca proveedores por nombre usando coincidencia parcial.
    Limita los resultados a 20 registros para evitar sobrecarga
    cuando hay muchos proveedores en el sistema.

    Parámetros:
        texto (str): Texto de búsqueda para filtrar proveedores por nombre.

    Retorna:
        list[dict]: Lista de diccionarios con los datos de cada proveedor
        encontrado. Retorna lista vacía si no hay coincidencias.
    """

    # Conecta a la base de datos
    conexion = conectar()

    # Cursor diccionario para acceder a columnas por nombre
    cursor = conexion.cursor(dictionary=True)

    # Consulta SQL que busca proveedores cuyo nombre contenga el texto
    # LIMIT 20 restringe la cantidad de resultados para mejorar rendimiento
    sql = """
        SELECT *
        FROM proveedores
        WHERE nombre LIKE %s
        LIMIT 20
    """

    # Ejecuta la consulta con texto envuelto en % para coincidencia parcial
    # La coma al final de la tupla (f"%{texto}%",) es necesaria para que
    # Python la reconozca como tupla de un solo elemento
    cursor.execute(sql, (f"%{texto}%",))

    # Obtiene todos los resultados
    resultados = cursor.fetchall()

    # Libera recursos
    cursor.close()
    conexion.close()

    # Retorna la lista de proveedores encontrados
    return resultados


def crear_proveedor(datos):
    """
    Crea un nuevo proveedor en la base de datos.
    Solo requiere el nombre del proveedor como dato mínimo.

    Parámetros:
        datos (dict): Diccionario con los datos del proveedor.
            Clave esperada: nombre.

    Retorna:
        int o None: El ID del proveedor creado, o None si ocurrió un error.
    """

    # Conecta a la base de datos
    conexion = conectar()

    # Crea cursor estándar para INSERT
    cursor = conexion.cursor()

    # Bloque try/except para manejo de errores
    try:
        # Consulta SQL para insertar un nuevo proveedor
        # Solo se almacena el nombre; otros campos pueden agregarse después
        sql = """
            INSERT INTO proveedores (nombre)
            VALUES (%s)
        """

        # Ejecuta el INSERT con el nombre del proveedor
        # Se usa .get() con valor por defecto vacío por seguridad
        cursor.execute(sql, (datos.get("nombre", ""),))

        # Confirma la transacción
        conexion.commit()

        # Obtiene el ID auto-generado del nuevo proveedor
        id_nuevo = cursor.lastrowid

        # Libera recursos
        cursor.close()
        conexion.close()

        # Retorna el ID del proveedor creado
        return id_nuevo

    except Exception as e:
        # Revierte la transacción si ocurre un error
        conexion.rollback()

        # Libera recursos
        cursor.close()
        conexion.close()

        # Imprime el error para depuración
        print(f"Error al crear proveedor: {e}")

        # Retorna None indicando fallo
        return None

def guardar_compra(compra_datos, detalles):
    """
    Guarda una compra completa con todos sus detalles en una transacción
    atómica. Si cualquier parte falla, se revierten todos los cambios.

    Esta función realiza tres operaciones principales:
    1. Inserta la cabecera de la compra en la tabla 'compras'
    2. Inserta cada producto comprado en 'detalle_compras'
    3. Aumenta el stock de cada producto comprado

    A diferencia de las ventas (que descuentan stock), las compras
    INCREMENTAN el stock porque representan entrada de mercancía.

    Parámetros:
        compra_datos (dict): Datos de la cabecera de la compra.
            Claves: fecha, total, id_proveedor, id_usuario, estado.
        detalles (list[dict]): Lista de productos comprados.
            Cada dict debe tener: id (o id_producto), cantidad, precio, subtotal.

    Retorna:
        int o None: El ID de la compra creada, o None si ocurrió un error.
    """

    # Conecta a la base de datos
    conexion = conectar()

    # Crea cursor estándar para operaciones de escritura
    cursor = conexion.cursor()

    # Bloque try/except para manejo de errores
    try:
        # Consulta SQL para insertar la cabecera de la compra
        # Almacena fecha, total, proveedor, usuario y estado
        sql_compra = """
            INSERT INTO compras (
                fecha,
                total,
                id_proveedor,
                id_usuario,
                estado
            ) VALUES (%s, %s, %s, %s, %s)
        """

        # Ejecuta el INSERT con los datos de la compra
        # Estado default es 'ACTIVA', id_usuario default es 1 (admin)
        cursor.execute(sql_compra, (
            compra_datos.get('fecha'),
            compra_datos.get('total', 0),
            compra_datos.get('id_proveedor'),
            compra_datos.get('id_usuario', 1),
            compra_datos.get('estado', 'ACTIVA')
        ))

        # Obtiene el ID auto-generado de la compra
        id_compra = cursor.lastrowid

        # Itera sobre cada producto comprado para insertar su detalle
        for detalle in detalles:
            # Obtiene el ID del producto aceptando ambas claves posibles
            id_producto = detalle.get('id') or detalle.get('id_producto')

            # Cantidad comprada de este producto
            cantidad = detalle.get('cantidad', 0)

            # Consulta SQL para insertar cada línea de detalle de compra
            # Vincula el detalle con la compra padre mediante id_compra
            sql_detalle = """
                INSERT INTO detalle_compras (
                    id_compra,
                    id_producto,
                    cantidad,
                    precio_unitario,
                    subtotal
                ) VALUES (%s, %s, %s, %s, %s)
            """

            # Ejecuta el INSERT del detalle
            cursor.execute(sql_detalle, (
                id_compra,
                id_producto,
                cantidad,
                detalle.get('precio'),
                detalle.get('subtotal')
            ))

            # Consulta SQL que INCREMENTA el stock del producto
            # Se suma (+) la cantidad comprada al stock actual
            # Esto es lo opuesto a las ventas, que restan stock
            sql_actualizar_stock = """
                UPDATE producto
                SET stock = stock + %s
                WHERE id_producto = %s
            """

            # Ejecuta la actualización del stock
            cursor.execute(sql_actualizar_stock, (
                cantidad,
                id_producto
            ))

        # Confirma toda la transacción: compra + detalles + actualización de stock
        conexion.commit()

        # Libera recursos
        cursor.close()
        conexion.close()

        # Retorna el ID de la compra creada
        return id_compra

    except Exception as e:
        # Revierte TODA la transacción si algo falla
        conexion.rollback()

        # Libera recursos
        cursor.close()
        conexion.close()

        # Imprime el error para depuración
        print(f"Error al guardar compra: {e}")

        # Retorna None indicando fallo
        return None


def obtener_producto_stock(id_producto):
    """
    Obtiene el stock actual de un producto específico.
    Se usa para verificar disponibilidad antes de crear compras
    o para mostrar información en la interfaz.

    Parámetros:
        id_producto (int): ID del producto a consultar.

    Retorna:
        dict o None: Diccionario con: id_producto, nombre, stock.
        O None si el producto no existe.
    """

    # Conecta a la base de datos
    conexion = conectar()

    # Cursor diccionario
    cursor = conexion.cursor(dictionary=True)

    # Consulta SQL que obtiene solo los campos necesarios del producto:
    # ID, nombre y stock actual
    sql = """
        SELECT id_producto, nombre, stock
        FROM producto
        WHERE id_producto = %s
    """

    # Ejecuta con el ID del producto
    cursor.execute(sql, (id_producto,))

    # Retorna un solo registro o None
    resultado = cursor.fetchone()

    # Libera recursos
    cursor.close()
    conexion.close()

    # Retorna los datos del producto
    return resultado


def obtener_proveedor_por_id(id_proveedor):
    """
    Obtiene los datos de un proveedor específico por su ID.

    Parámetros:
        id_proveedor (int): ID del proveedor a buscar.

    Retorna:
        dict o None: Diccionario con: id_proveedor, nombre.
        O None si no se encuentra.
    """

    # Conecta a la base de datos
    conexion = conectar()

    # Cursor diccionario
    cursor = conexion.cursor(dictionary=True)

    # Consulta SQL que obtiene ID y nombre del proveedor
    sql = """
        SELECT
            id_proveedor,
            nombre
        FROM proveedores
        WHERE id_proveedor = %s
    """

    # Ejecuta con el ID del proveedor
    cursor.execute(sql, (id_proveedor,))

    # Retorna un solo registro o None
    resultado = cursor.fetchone()

    # Libera recursos
    cursor.close()
    conexion.close()

    # Retorna los datos del proveedor
    return resultado


def anular_compra(id_compra):
    """
    Anula una compra cambiando su estado a 'ANULADA'.
    NO elimina el registro físicamente para mantener el historial.

    Parámetros:
        id_compra (int): ID de la compra a anular.

    Retorna:
        bool: True si se anuló correctamente, False si ocurrió un error.
    """

    # Conecta a la base de datos
    conexion = conectar()

    # Crea cursor estándar
    cursor = conexion.cursor()

    # Bloque try/except para manejo de errores
    try:
        # Consulta SQL que cambia el estado de la compra a 'ANULADA'
        # Es un UPDATE, no un DELETE, para preservar el registro
        sql = """
            UPDATE compras
            SET estado = 'ANULADA'
            WHERE id_compra = %s
        """

        # Ejecuta el UPDATE con el ID de la compra
        cursor.execute(sql, (id_compra,))

        # Confirma la transacción
        conexion.commit()

        # Libera recursos
        cursor.close()
        conexion.close()

        # Retorna True indicando éxito
        return True
    except Exception as e:
        # Revierte la transacción si hay error
        conexion.rollback()

        # Libera recursos
        cursor.close()
        conexion.close()

        # Imprime el error para depuración
        print(f"Error al anular compra: {e}")

        # Retorna False indicando fallo
        return False


def obtener_todas_compras():
    """
    Recupera todas las compras registradas en el sistema.
    Las ordena por ID descendente (más recientes primero).

    Retorna:
        list[dict]: Lista de diccionarios con los campos: id_compra,
        fecha, total, estado, id_proveedor, id_usuario.
    """

    # Conecta a la base de datos
    conexion = conectar()

    # Cursor diccionario
    cursor = conexion.cursor(dictionary=True)

    # Consulta SQL que obtiene todos los campos relevantes de la tabla 'compras'
    # ORDER BY id_compra DESC muestra las compras más recientes primero
    sql = """
        SELECT
            id_compra,
            fecha,
            total,
            estado,
            id_proveedor,
            id_usuario
        FROM compras
        ORDER BY id_compra DESC
    """

    # Ejecuta la consulta sin parámetros
    cursor.execute(sql)

    # Obtiene todas las filas como lista de diccionarios
    resultado = cursor.fetchall()

    # Libera recursos
    cursor.close()
    conexion.close()

    # Retorna la lista de compras
    return resultado


def obtener_compra_por_id(id_compra):
    """
    Obtiene los datos completos de una compra específica por su ID.
    Incluye el nombre del usuario mediante un JOIN con 'usuarios'.

    Parámetros:
        id_compra (int): ID de la compra a buscar.

    Retorna:
        dict o None: Diccionario con todos los campos de la compra
        más el nombre del usuario, o None si no se encuentra.
    """

    # Conecta a la base de datos
    conexion = conectar()

    # Cursor diccionario
    cursor = conexion.cursor(dictionary=True)

    # Consulta SQL con INNER JOIN entre compras y usuarios
    # El JOIN trae el nombre del usuario que realizó la compra
    # Se usan alias (c, u) para abreviar la consulta
    sql = """
        SELECT
            c.id_compra,
            c.fecha,
            c.total,
            c.estado,
            c.id_proveedor,
            c.id_usuario,
            u.nombre AS nombre_usuario
        FROM compras c
        INNER JOIN usuarios u
            ON c.id_usuario = u.id_usuario
        WHERE c.id_compra = %s
    """

    # Ejecuta con el ID de la compra
    cursor.execute(sql, (id_compra,))

    # Retorna un solo registro o None
    resultado = cursor.fetchone()

    # Libera recursos
    cursor.close()
    conexion.close()

    # Retorna los datos de la compra
    return resultado


def obtener_detalles_compra(id_compra):
    """
    Obtiene todos los ítems (detalles) de una compra específica.
    Cada detalle representa un producto comprado con su cantidad y precio.

    Parámetros:
        id_compra (int): ID de la compra cuyos detalles se desean obtener.

    Retorna:
        list[dict]: Lista de diccionarios con: id_detalle, id_compra,
        id_producto, cantidad, precio_unitario, subtotal.
    """

    # Conecta a la base de datos
    conexion = conectar()

    # Cursor diccionario
    cursor = conexion.cursor(dictionary=True)

    # Consulta SQL que obtiene los detalles de compra para una compra específica
    # La tabla 'detalle_compras' almacena cada línea de producto de cada compra
    sql = """
        SELECT
            id_detalle,
            id_compra,
            id_producto,
            cantidad,
            precio_unitario,
            subtotal
        FROM detalle_compras
        WHERE id_compra = %s
    """

    # Ejecuta con el ID de la compra
    cursor.execute(sql, (id_compra,))

    # Obtiene todos los detalles
    resultado = cursor.fetchall()

    # Libera recursos
    cursor.close()
    conexion.close()

    # Retorna la lista de detalles
    return resultado
