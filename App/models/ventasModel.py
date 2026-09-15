"""
Módulo de ventas del sistema POS.
Este archivo contiene todas las operaciones de base de datos relacionadas con
la gestión de ventas, incluyendo:
  - Búsqueda de productos y clientes
  - Creación y actualización de clientes y productos
  - Guardado de facturas (ventas) con sus detalles
  - Anulación de facturas
  - Consulta de facturas, detalles, clientes y productos

Todas las funciones manejan sus propias conexiones a la base de datos MySQL
y utilizan transacciones para garantizar la integridad de los datos.
"""

# Importa la función de conexión a la base de datos MySQL
from database.bd import conectar


# =====================================================
# BUSCAR PRODUCTOS
# =====================================================

def buscar_producto(nombre):
    """
    Busca productos por nombre o código en la base de datos.
    Utiliza coincidencia parcial (LIKE) para encontrar productos cuyo
    nombre O código contenga el texto de búsqueda.

    Parámetros:
        nombre (str): Texto de búsqueda para filtrar productos.

    Retorna:
        list[dict]: Lista de diccionarios, cada uno con los datos de un
        producto encontrado. Retorna lista vacía si no hay coincidencias
        o si la conexión a la base de datos falla.
    """

    # Establece la conexión a la base de datos
    conexion = conectar()

    # Si la conexión falla (retorna None o False), retorna lista vacía
    # como medida de seguridad para evitar errores en la capa superior
    if not conexion:
        return []

    # Cursor tipo diccionario para acceder a las columnas por nombre
    cursor = conexion.cursor(dictionary=True)

    # Consulta SQL que busca productos cuyo nombre O código contengan
    # el texto de búsqueda. Se usa OR para buscar en ambos campos.
    # LIKE con % permite coincidencia parcial en cualquier posición
    sql = """
        SELECT *
        FROM producto
        WHERE nombre LIKE %s OR codigo LIKE %s
    """

    # Ejecuta la consulta con los parámetros de búsqueda
    # f"%{nombre}%" envuelve el texto con % para que coincida con
    # cualquier texto antes o después del término buscado
    cursor.execute(sql, (f"%{nombre}%", f"%{nombre}%"))

    # fetchall() retorna todas las filas encontradas como lista de diccionarios
    resultado = cursor.fetchall()

    # Cierra cursor y conexión para liberar recursos del servidor
    cursor.close()
    conexion.close()

    # Retorna la lista de productos encontrados (puede ser lista vacía)
    return resultado


# =====================================================
# VERIFICAR SI EXISTE CÓDIGO DE PRODUCTO
# =====================================================

def existe_codigo_producto(codigo, id_producto=None):
    """
    Verifica si un código de producto ya existe en la base de datos.
    Se usa para validar que no se dupliquen códigos al crear o editar productos.

    Parámetros:
        codigo (str): El código del producto a verificar.
        id_producto (int, optional): Si se proporciona, excluye este ID de la
        búsqueda. Útil al editar un producto para no considerar su propio código
        como duplicado.

    Retorna:
        bool: True si el código ya existe en otro producto, False si está
        disponible o si la conexión falla.
    """

    # Conecta a la base de datos
    conexion = conectar()

    # Si la conexión falla, retorna False como valor seguro
    if not conexion:
        return False

    # Cursor tipo diccionario para verificar existencia
    cursor = conexion.cursor(dictionary=True)

    # Bloque try/finally para garantizar que cursor y conexión se cierren
    # incluso si ocurre una excepción
    try:
        # Si se proporcionó un ID de producto (modo edición), se excluye
        # ese producto de la búsqueda para permitir mantener su propio código
        if id_producto:
            # Busca si otro producto (diferente al actual) ya usa ese código
            sql = "SELECT id_producto FROM producto WHERE codigo = %s AND id_producto != %s"
            cursor.execute(sql, (codigo, id_producto))
        else:
            # Modo creación: simplemente verifica si el código ya existe
            sql = "SELECT id_producto FROM producto WHERE codigo = %s"
            cursor.execute(sql, (codigo,))

        # Retorna True si se encontró al menos un registro, False si no
        return cursor.fetchone() is not None
    finally:
        # Se ejecuta siempre, con o sin excepción
        cursor.close()
        conexion.close()

# =====================================================
# BUSCAR CLIENTES
# =====================================================

def buscar_cliente(nombre):
    """
    Busca clientes por nombre o número de documento.
    Usa coincidencia parcial (LIKE) para encontrar clientes cuyo nombre
    O documento contenga el texto de búsqueda.

    Parámetros:
        nombre (str): Texto de búsqueda para filtrar clientes.

    Retorna:
        list[dict]: Lista de diccionarios con los datos de cada cliente
        encontrado. Retorna lista vacía si no hay coincidencias.
    """

    # Conecta a la base de datos
    conexion = conectar()

    # Cursor tipo diccionario para acceder a columnas por nombre
    cursor = conexion.cursor(dictionary=True)

    # Consulta SQL que busca en dos campos: nombre y documento
    # Esto permite al usuario buscar tanto por nombre del cliente
    # como por su número de cédula, NIT u otro documento
    sql = """
        SELECT *
        FROM clientes
        WHERE nombre LIKE %s
        OR documento LIKE %s
    """

    # Ejecuta la consulta con texto envuelto en % para coincidencia parcial
    cursor.execute(
        sql,
        (f"%{nombre}%", f"%{nombre}%")
    )

    # Obtiene todos los resultados como lista de diccionarios
    resultado = cursor.fetchall()

    # Libera los recursos de conexión
    cursor.close()
    conexion.close()

    # Retorna la lista de clientes encontrados
    return resultado


# =====================================================
# ACTUALIZAR CLIENTE
# =====================================================

def actualizar_cliente(cliente_datos):
    """
    Actualiza los datos de un cliente existente en la base de datos.
    Sobrescribe nombre, documento, dirección, teléfono y rol del cliente
    identificado por su ID.

    Parámetros:
        cliente_datos (dict): Diccionario con los campos a actualizar.
        Debe contener 'id_cliente' y al menos un campo a modificar.
        Campos soportados: nombre, documento, direccion, telefono, rol.

    Retorna:
        bool: True siempre que la operación se ejecute (no valida errores).
    """

    # Conecta a la base de datos
    conexion = conectar()

    # Crea cursor estándar para operación UPDATE
    cursor = conexion.cursor()

    # Consulta SQL UPDATE que modifica los cinco campos del cliente
    # Se usa WHERE id_cliente para asegurar que solo se actualice
    # el registro específico y no todos los clientes
    sql = """
        UPDATE clientes
        SET
            nombre=%s,
            documento=%s,
            direccion=%s,
            telefono=%s,
            rol=%s
        WHERE id_cliente=%s
    """

    # Ejecuta el UPDATE con los valores del diccionario
    # Se usa .get() con valor por defecto para evitar KeyError
    # si algún campo no está presente en el diccionario
    cursor.execute(sql, (
        cliente_datos.get('nombre', ''),
        cliente_datos.get('documento', ''),
        cliente_datos.get('direccion', ''),
        cliente_datos.get('telefono', ''),
        cliente_datos.get('rol', ''),
        cliente_datos.get('id_cliente')

    ))

    # Confirma la transacción para persistir los cambios
    conexion.commit()

    # Libera recursos
    cursor.close()
    conexion.close()

    # Retorna True indicando que la operación se ejecutó
    return True


# =====================================================
# ACTUALIZAR PRODUCTO
# =====================================================

def actualizar_producto(producto_datos):
    """
    Actualiza todos los campos de un producto existente en la base de datos.
    Modifica código, nombre, unidad, lugar, precio, stock, descripción y categoría.

    Parámetros:
        producto_datos (dict): Diccionario con los datos del producto.
        Debe contener 'id_producto' (o 'id') para identificar el registro.
        Campos soportados: codigo, nombre, unidad, lugar, precio, stock,
        descripcion, categoria.

    Retorna:
        bool: True siempre que la operación se ejecute.
    """

    # Conecta a la base de datos
    conexion = conectar()

    # Crea cursor estándar para UPDATE
    cursor = conexion.cursor()

    # Consulta SQL UPDATE que sobrescribe todos los campos del producto
    # WHERE id_producto asegura que solo se modifique el producto específico
    sql = """
        UPDATE producto
        SET
            codigo=%s,
            nombre=%s,
            unidad=%s,
            lugar=%s,
            precio=%s,
            stock=%s,
            descripcion=%s,
            categoria=%s
        WHERE id_producto=%s
    """

    # Ejecuta el UPDATE con valores del diccionario
    # Se usa .get() con valores por defecto para robustez
    # Para 'id_producto' se acepta también la key 'id' por compatibilidad
    cursor.execute(sql, (
        producto_datos.get('codigo', ''),
        producto_datos.get('nombre', ''),
        producto_datos.get('unidad', ''),
        producto_datos.get('lugar', ''),
        producto_datos.get('precio', 0),
        producto_datos.get('stock', 0),
        producto_datos.get('descripcion', ''),
        producto_datos.get('categoria', 'Abonos y Sustratos'),
        producto_datos.get('id_producto') or producto_datos.get('id')
    ))

    # Confirma la transacción
    conexion.commit()

    # Libera recursos
    cursor.close()
    conexion.close()

    return True


# =====================================================
# OBTENER TODAS LAS FACTURAS
# =====================================================

def obtener_todas_facturas():
    """
    Recupera todas las facturas (ventas) registradas en el sistema.
    Las ordena por ID descendente para que las más recientes aparezcan primero.

    Retorna:
        list[dict]: Lista de diccionarios, cada uno con los campos:
        id_venta, fecha, total, metodo_pago, estado, id_cliente,
        id_usuario, dinero_recibido, cambio, notas.
    """

    # Conecta a la base de datos
    conexion = conectar()

    # Cursor diccionario para acceder a columnas por nombre
    cursor = conexion.cursor(dictionary=True)

    # Consulta SQL que obtiene todos los campos relevantes de la tabla 'venta'
    # ORDER BY id_venta DESC ordena de la más reciente a la más antigua
    sql = """
        SELECT
            id_venta,
            fecha,
            total,
            metodo_pago,
            estado,
            id_cliente,
            id_usuario,
            dinero_recibido,
            cambio,
            notas
        FROM venta
        ORDER BY id_venta DESC
    """

    # Ejecuta la consulta (sin parámetros porque no hay filtros)
    cursor.execute(sql)

    # Obtiene todas las filas como lista de diccionarios
    resultado = cursor.fetchall()

    # Libera recursos
    cursor.close()
    conexion.close()

    # Retorna la lista completa de facturas
    return resultado


# =====================================================
# OBTENER FACTURA POR ID
# =====================================================

def obtener_factura_por_id(id_venta):
    """
    Obtiene los datos completos de una factura específica por su ID.
    Incluye el nombre del usuario que realizó la venta mediante un JOIN
    con la tabla 'usuarios'.

    Parámetros:
        id_venta (int): ID de la factura a buscar.

    Retorna:
        dict o None: Diccionario con todos los campos de la factura
        más el nombre del usuario, o None si no se encuentra.
    """

    # Conecta a la base de datos
    conexion = conectar()

    # Cursor diccionario
    cursor = conexion.cursor(dictionary=True)

    # Consulta SQL con INNER JOIN entre venta y usuarios
    # El JOIN permite obtener el nombre del vendedor sin necesidad de
    # una segunda consulta. Se usa alias (v, u) para brevedad
    sql = """
        SELECT
            v.id_venta,
            v.fecha,
            v.total,
            v.metodo_pago,
            v.estado,
            v.id_cliente,
            v.id_usuario,
            u.nombre AS nombre_usuario,
            v.dinero_recibido,
            v.cambio,
            v.notas
        FROM venta v
        INNER JOIN usuarios u
            ON v.id_usuario = u.id_usuario
        WHERE v.id_venta = %s
    """

    # Ejecuta con el ID de la factura como parámetro
    cursor.execute(sql, (id_venta,))

    # fetchone() retorna un solo diccionario o None
    resultado = cursor.fetchone()

    # Libera recursos
    cursor.close()
    conexion.close()

    # Retorna los datos de la factura o None si no existe
    return resultado


# =====================================================
# OBTENER DETALLES FACTURA
# =====================================================

def obtener_detalles_factura(id_venta):
    """
    Obtiene todos los ítems (detalles) de una factura específica.
    Cada detalle representa un producto vendido con su cantidad y precio.

    Parámetros:
        id_venta (int): ID de la factura cuyos detalles se desean obtener.

    Retorna:
        list[dict]: Lista de diccionarios con los campos: id_detalle,
        id_venta, id_producto, cantidad, precio_unitario, subtotal.
    """

    # Conecta a la base de datos
    conexion = conectar()

    # Cursor diccionario
    cursor = conexion.cursor(dictionary=True)

    # Consulta SQL que obtiene los detalles de venta para una factura específica
    # La tabla 'detalle_venta' almacena cada línea de producto de cada venta
    sql = """
        SELECT
            id_detalle,
            id_venta,
            id_producto,
            cantidad,
            precio_unitario,
            subtotal
        FROM detalle_venta
        WHERE id_venta = %s
    """

    # Ejecuta la consulta con el ID de la factura
    cursor.execute(sql, (id_venta,))

    # fetchall() retorna todos los detalles como lista
    resultado = cursor.fetchall()

    # Libera recursos
    cursor.close()
    conexion.close()

    # Retorna la lista de detalles de la factura
    return resultado


# =====================================================
# OBTENER CLIENTE POR ID
# =====================================================

def obtener_cliente_por_id(id_cliente):
    """
    Obtiene los datos completos de un cliente específico por su ID.

    Parámetros:
        id_cliente (int): ID del cliente a buscar.

    Retorna:
        dict o None: Diccionario con los campos: id_cliente, nombre,
        documento, direccion, telefono, rol. O None si no se encuentra.
    """

    # Conecta a la base de datos
    conexion = conectar()

    # Cursor diccionario
    cursor = conexion.cursor(dictionary=True)

    # Consulta SQL que obtiene los datos de un cliente por su ID
    # Se seleccionan solo los campos necesarios (no se usa SELECT *)
    sql = """
        SELECT
            id_cliente,
            nombre,
            documento,
            direccion,
            telefono,
            rol
        FROM clientes
        WHERE id_cliente = %s
    """

    # Ejecuta con el ID del cliente
    cursor.execute(sql, (id_cliente,))

    # Retorna un solo registro o None
    resultado = cursor.fetchone()

    # Libera recursos
    cursor.close()
    conexion.close()

    # Retorna los datos del cliente o None
    return resultado


# =====================================================
# OBTENER PRODUCTO POR ID
# =====================================================

def obtener_producto_por_id(id_producto):
    """
    Obtiene los datos básicos de un producto específico por su ID.
    Retorna solo los campos necesarios para mostrar en facturas y detalles.

    Parámetros:
        id_producto (int): ID del producto a buscar.

    Retorna:
        dict o None: Diccionario con: id_producto, nombre, precio,
        unidad, lugar. O None si no se encuentra.
    """

    # Conecta a la base de datos
    conexion = conectar()

    # Cursor diccionario
    cursor = conexion.cursor(dictionary=True)

    # Consulta SQL que obtiene los campos esenciales de un producto
    # No se traen todos los campos porque solo se necesitan estos
    # para la lógica de ventas y facturación
    sql = """
        SELECT
            id_producto,
            nombre,
            precio,
            unidad,
            lugar
        FROM producto
        WHERE id_producto = %s
    """

    # Ejecuta con el ID del producto
    cursor.execute(sql, (id_producto,))

    # Retorna un solo producto o None
    resultado = cursor.fetchone()

    # Libera recursos
    cursor.close()
    conexion.close()

    # Retorna los datos del producto o None
    return resultado


# =====================================================
# ANULAR FACTURA
# =====================================================

def eliminar_factura(id_venta):
    """
    Anula una factura cambiando su estado a 'ANULADA'.
    NO elimina físicamente el registro de la base de datos,
    solo cambia su estado para mantener el historial de auditoría.

    Parámetros:
        id_venta (int): ID de la factura a anular.

    Retorna:
        bool: True si se anuló correctamente, False si ocurrió un error.
    """

    # Conecta a la base de datos
    conexion = conectar()

    # Crea cursor estándar para UPDATE
    cursor = conexion.cursor()

    # Bloque try/except para manejar errores y hacer rollback si falla
    try:

        # Consulta SQL que cambia el estado de la factura a 'ANULADA'
        # Es un UPDATE, no un DELETE, para preservar el registro histórico
        sql = """
            UPDATE venta
            SET estado = 'ANULADA'
            WHERE id_venta = %s
        """

        # Ejecuta el UPDATE con el ID de la factura
        cursor.execute(sql, (id_venta,))

        # Confirma la transacción para persistir el cambio de estado
        conexion.commit()

        # Libera recursos
        cursor.close()
        conexion.close()

        # Retorna True indicando éxito
        return True

    except Exception as e:
        # Si ocurre cualquier error, revierte todos los cambios de la transacción
        # para mantener la integridad de la base de datos
        conexion.rollback()

        # Libera recursos incluso en caso de error
        cursor.close()
        conexion.close()

        # Imprime el error en consola para depuración
        print(f"Error al anular factura: {e}")

        # Retorna False indicando que la operación falló
        return False


# =====================================================
# GUARDAR FACTURA
# =====================================================

def guardar_factura(factura_datos, detalles):
    """
    Guarda una factura completa (venta) con todos sus detalles en una
    transacción atómica. Si cualquier parte falla, se revierten todos
    los cambios.

    Esta función realiza las siguientes operaciones:
    1. Inserta la cabecera de la venta (con su id_apartado si aplica).
    2. Inserta cada producto vendido en 'detalle_venta'.
    3. Descuenta el stock de cada producto vendido.
    4. Según el tipo de venta:
       - VENTA DIRECTA (id_apartado IS NULL): también descuenta
         `limite_venta` y desactiva el producto si queda en 0.
       - ENTREGA DE APARTADO WEB (id_apartado NOT NULL): NO toca
         `limite_venta` (ya se restó en la web al apartar) y marca el
         apartado como 'entregado'.

    Parámetros:
        factura_datos (dict): Datos de la cabecera de la venta.
            Claves esperadas: fecha, total, metodo_pago, id_cliente,
            id_usuario, dinero_recibido, cambio, notas, id_apartado.
        detalles (list[dict]): Lista de productos vendidos.
            Cada dict debe tener: id_producto (o id), cantidad, precio, subtotal.

    Retorna:
        int o None: El ID de la venta creada, o None si ocurrió un error.
    """

    # Conecta a la base de datos
    conexion = conectar()

    # Crea cursor estándar para operaciones de escritura
    cursor = conexion.cursor()

    # Tipo de venta: None = directa de pasillo; entero = entrega de apartado web
    id_apartado = factura_datos.get('id_apartado')
    es_entrega_apartado = id_apartado is not None

    # Bloque try/except para manejo de errores y rollback
    try:

        # Consulta SQL para insertar la cabecera de la venta
        # El estado se establece como 'ACTIVA' por defecto
        sql_venta = """
            INSERT INTO venta (
                fecha,
                total,
                metodo_pago,
                estado,
                id_cliente,
                id_usuario,
                dinero_recibido,
                cambio,
                notas,
                id_apartado
            )

            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        # Ejecuta el INSERT con los datos de la venta
        cursor.execute(sql_venta, (
            factura_datos.get('fecha'),
            factura_datos.get('total', 0),
            factura_datos.get('metodo_pago'),
            "ACTIVA",
            factura_datos.get('id_cliente'),
            factura_datos.get('id_usuario', 1),
            factura_datos.get('dinero_recibido', 0),
            factura_datos.get('cambio', 0),
            factura_datos.get('notas', ''),
            id_apartado

        ))

        # Obtiene el ID auto-generado de la venta recién insertada
        id_venta = cursor.lastrowid

        # ------------------------------------
        # GUARDAR DETALLES
        # ------------------------------------

        # Itera sobre cada producto vendido para insertarlo como detalle
        for detalle in detalles:

            # Obtiene el ID del producto, aceptando ambas claves posibles
            id_producto = (
                detalle.get('id_producto')
                or detalle.get('id')
            )

            # Cantidad de este producto en la venta
            cantidad = detalle.get('cantidad')

            # Indica si esta línea es el producto reservado del apartado web.
            # Solo esa línea va en UNIDADES y sin descontar limite_venta (ya
            # se restó al apartar en la web). Las líneas adicionales de pasillo
            # que el cajero agregue durante una entrega se tratan como venta
            # directa (conversión por si son huevos y descuento de limite_venta).
            es_apartado = bool(detalle.get('es_apartado'))

            # -----------------------------------------
            # CANTIDAD A DESCONTAR DEL STOCK (en UNIDADES)
            # -----------------------------------------
            # - Línea de apartado web: la cantidad ya viene en UNIDADES (la
            #   web guardó el apartado convertido a unidades), por lo que
            #   se usa tal cual, sin conversión.
            # - Línea de pasillo (venta directa o extra en entrega de
            #   apartado): la cantidad puede ser en CUBETAS (huevos), por lo
            #   que se convierte a unidades (x30).
            if es_apartado:
                # Unidades ya reservadas en la web
                cantidad_unidades = float(cantidad or 0)
                # El detalle se registra en las mismas unidades reservadas
                cantidad_detalle = cantidad_unidades
                # No se descuenta limite_venta ni se toca el estado del
                # producto aquí (ya se gestionó al apartar en la web)
                descontar_limite = False
            else:
                # Detecta huevos por nombre o unidad (1 cubeta = 30 unidades)
                nombre_producto = str(detalle.get('nombre') or '').lower()
                unidad_producto = str(detalle.get('unidad') or '').lower()
                es_huevo = 'huevo' in nombre_producto or 'cubeta' in unidad_producto

                # Unidades a descontar del inventario
                cantidad_unidades = cantidad * 30 if es_huevo else cantidad
                # Cantidad física que se muestra en el detalle
                # (en cubetas para huevos)
                cantidad_detalle = cantidad
                descontar_limite = True

            # Consulta SQL para insertar cada línea de detalle de venta
            sql_detalle = """
                INSERT INTO detalle_venta (

                    id_venta,
                    id_producto,
                    cantidad,
                    precio_unitario,
                    subtotal

                )

                VALUES (%s, %s, %s, %s, %s)
            """

            # Ejecuta el INSERT del detalle con los datos del producto
            cursor.execute(sql_detalle, (
                id_venta,
                id_producto,
                cantidad_detalle,
                detalle.get('precio'),
                detalle.get('subtotal')
            ))

            # --------------------------------
            # DESCONTAR STOCK
            # --------------------------------
            # En ambos tipos de venta se descuenta stock físico del producto
            sql_actualizar_stock = """
                UPDATE producto
                SET stock = stock - %s
                WHERE id_producto = %s
            """
            cursor.execute(sql_actualizar_stock, (
                cantidad_unidades,
                id_producto
            ))

            # --------------------------------
            # VENTA DIRECTA: DESCONTAR LIMITE_VENTA
            # --------------------------------
            # Solo en ventas directas de pasillo se descuenta el cupo en
            # línea. En la entrega de un apartado web NO se toca, porque ya
            # se restó cuando el cliente apartó el producto en la web.
            if descontar_limite:
                # Se descuenta limite_venta en unidades. Se hace en DOS
                # pasos para evitar la ambigüedad de MySQL (dentro de un
                # mismo UPDATE las referencias pueden tomar el valor ya
                # actualizado y falsear la condición de desactivación).
                sql_actualizar_limite = """
                    UPDATE producto
                    SET limite_venta = limite_venta - %s
                    WHERE id_producto = %s
                      AND limite_venta > 0
                """
                cursor.execute(sql_actualizar_limite, (
                    cantidad_unidades,
                    id_producto
                ))

                # Si limite_venta quedó en 0 o menos, se desactiva el producto
                # (igual que hace la web al agotar el cupo)
                sql_desactivar = """
                    UPDATE producto
                    SET estado = 'inactivo'
                    WHERE id_producto = %s
                      AND limite_venta <= 0
                """
                cursor.execute(sql_desactivar, (id_producto,))

        # --------------------------------
        # ENTREGA DE APARTADO: MARCAR COMO ENTREGADO
        # --------------------------------
        if es_entrega_apartado:
            sql_entregar_apartado = """
                UPDATE apartados
                SET estado = 'entregado'
                WHERE id_apartado = %s
            """
            cursor.execute(sql_entregar_apartado, (id_apartado,))

        # Confirma TODAS las inserciones y actualizaciones en una sola transacción
        conexion.commit()

        # Libera recursos
        cursor.close()
        conexion.close()

        # Retorna el ID de la venta creada
        return id_venta

    except Exception as e:
        # Si ocurre cualquier error, revierte TODA la transacción
        conexion.rollback()

        # Libera recursos
        cursor.close()
        conexion.close()

        # Imprime el error para depuración
        print(f"Error al guardar factura: {e}")

        # Retorna None indicando fallo
        return None

# =====================================================
# CREAR CLIENTE
# =====================================================

def crear_cliente(datos):
    """
    Crea un nuevo cliente en la base de datos.
    Inserta nombre, documento, dirección, teléfono y rol del cliente.

    Parámetros:
        datos (dict): Diccionario con los campos del cliente.
            Claves requeridas: nombre, documento, direccion, telefono, rol.

    Retorna:
        int o None: El ID del cliente creado, o None si ocurrió un error.
    """

    # Conecta a la base de datos
    conexion = conectar()

    # Crea cursor estándar para INSERT
    cursor = conexion.cursor()

    # Consulta SQL para insertar un nuevo cliente
    # Los campos son: nombre, documento (cédula/NIT), dirección, teléfono y rol
    sql = """
        INSERT INTO clientes (

            nombre,
            documento,
            direccion,
            telefono,
            rol
        )
        VALUES (%s, %s, %s,, %s, %s)
    """

    # Bloque try/except/finally para manejo seguro de la conexión
    try:

        # Ejecuta el INSERT con los datos del cliente
        # Se accede directamente con ['clave'] porque se asume
        # que el diccionario siempre contiene estos campos
        cursor.execute(sql, (
            datos['nombre'],
            datos['documento'],
            datos['direccion'],
            datos['telefono'],
            datos['rol']
        ))

        # Confirma la transacción
        conexion.commit()

        # Retorno el ID creado
        # Retorna el ID auto-generado del nuevo cliente
        return cursor.lastrowid

    except Exception as err:

        # Imprime el error para depuración
        print(f"Error al crear cliente: {err}")

        # Revierte la transacción si falla la inserción
        conexion.rollback()

        # Retorna None indicando fallo
        return None

    finally:
        # Bloque finally: se ejecuta SIEMPRE, tanto si hay error como si no
        # Garantiza que los recursos se liberen adecuadamente
        cursor.close()
        conexion.close()


# =====================================================
# CREAR PRODUCTO
# =====================================================

def crear_producto(datos):
    """
    Crea un nuevo producto en la base de datos.
    El producto se crea con estado 'inactivo' por defecto, lo que significa
    que no aparecerá en la búsqueda de ventas hasta que sea activado manualmente.

    Parámetros:
        datos (dict): Diccionario con los campos del producto.
            Claves: codigo, nombre, unidad, lugar, precio, stock,
            descripcion (opcional), categoria (opcional).

    Retorna:
        int o None: El ID del producto creado, o None si ocurrió un error.
    """

    # Conecta a la base de datos
    conexion = conectar()

    # Crea cursor estándar
    cursor = conexion.cursor()

    # Consulta SQL para insertar un nuevo producto
    # El estado se establece como 'inactivo' hardcoded porque los productos
    # nuevos requieren revisión antes de estar disponibles para ventas
    sql = """
        INSERT INTO producto (
            codigo,
            nombre,
            unidad,
            lugar,
            precio,
            stock,
            descripcion,
            categoria,
            estado
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'inactivo')
    """
    try:

        # Ejecuta el INSERT con los datos del producto
        # Para campos opcionales se usa .get() con valor por defecto:
        # - codigo: cadena vacía si no se proporciona
        # - descripcion: cadena vacía
        # - categoria: 'Abonos y Sustratos' (categoría predeterminada)
        cursor.execute(sql, (
            datos.get('codigo', ''),
            datos['nombre'],
            datos['unidad'],
            datos['lugar'],
            datos['precio'],
            datos['stock'],
            datos.get('descripcion', ''),
            datos.get('categoria', 'Abonos y Sustratos')
        ))

        # Confirma la transacción para persistir el producto
        conexion.commit()

        # Retorno el ID del producto creado
        # Retorna el ID auto-generado del nuevo producto
        return cursor.lastrowid

    except Exception as err:

        # Imprime el error para depuración
        print(f"Error al crear producto: {err}")

        # Revierte la transacción si falla
        conexion.rollback()

        # Retorna None indicando fallo
        return None

    finally:
        # Garantiza la liberación de recursos siempre
        cursor.close()
        conexion.close()


# =====================================================
# OBTENER APARTADOS PENDIENTES (ENTREGAS WEB)
# =====================================================

def obtener_apartados_pendientes():
    """
    Obtiene los apartados web que están a la espera de ser entregados en
    el punto de venta (estado 'pendiente' o 'confirmado').

    Se unen con la tabla 'producto' para mostrar el nombre, la unidad y el
    precio del artículo apartado. La cantidad propia del apartado se guarda
    en UNIDADES (la web convierte cubetas a unidades al reservar).

    Retorna:
        list[dict]: Lista de apartados pendientes con los datos del producto.
        Retorna lista vacía si no hay resultados o si falla la conexión.
    """

    # Establece la conexión a la base de datos
    conexion = conectar()

    # Si la conexión falla, retorna lista vacía como valor seguro
    if not conexion:
        return []

    # Cursor tipo diccionario para acceder a las columnas por nombre
    cursor = conexion.cursor(dictionary=True)

    # Bloque try/finally para garantizar el cierre de recursos
    try:

        # Consulta que une apartados pendientes/confirmados con su producto
        # Ordena por fecha ascendente: los más antiguos primero (FIFO)
        sql = """
            SELECT
                ap.id_apartado,
                ap.nombre_cliente,
                ap.cantidad,
                ap.fecha,
                ap.precio_aplicado,
                p.id_producto,
                p.codigo,
                p.nombre,
                p.unidad,
                p.precio
            FROM apartados ap
            JOIN producto p ON p.id_producto = ap.producto
            WHERE ap.estado IN ('pendiente', 'confirmado')
            ORDER BY ap.fecha ASC
        """

        # Ejecuta la consulta
        cursor.execute(sql)

        # Obtiene todas las filas como lista de diccionarios
        resultado = cursor.fetchall()

        # Retorna la lista de apartados pendientes (puede ser vacía)
        return resultado

    except Exception as err:
        # Imprime el error para depuración
        print(f"Error al obtener apartados pendientes: {err}")

        # Retorna lista vacía en caso de error
        return []

    finally:
        # Garantiza la liberación de recursos siempre
        cursor.close()
        conexion.close()
