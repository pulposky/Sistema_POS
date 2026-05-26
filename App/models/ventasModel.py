from database.bd import conectar


# =====================================================
# BUSCAR PRODUCTOS
# =====================================================

def buscar_producto(nombre):
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    sql = """
        SELECT *
        FROM producto
        WHERE nombre LIKE %s
    """
    cursor.execute(sql, (f"%{nombre}%",))
    resultado = cursor.fetchall()
    cursor.close()
    conexion.close()

    return resultado

# =====================================================
# BUSCAR CLIENTES
# =====================================================

def buscar_cliente(nombre):

    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    sql = """
        SELECT *
        FROM clientes
        WHERE nombre LIKE %s
        OR documento LIKE %s
    """
    cursor.execute(
        sql,
        (f"%{nombre}%", f"%{nombre}%")
    )
    resultado = cursor.fetchall()
    cursor.close()
    conexion.close()

    return resultado


# =====================================================
# ACTUALIZAR CLIENTE
# =====================================================

def actualizar_cliente(cliente_datos):

    conexion = conectar()
    cursor = conexion.cursor()
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
    cursor.execute(sql, (
        cliente_datos.get('nombre', ''),
        cliente_datos.get('documento', ''),
        cliente_datos.get('direccion', ''),
        cliente_datos.get('telefono', ''),
        cliente_datos.get('rol', ''),
        cliente_datos.get('id_cliente')

    ))

    conexion.commit()
    cursor.close()
    conexion.close()
    return True


# =====================================================
# OBTENER TODAS LAS FACTURAS
# =====================================================

def obtener_todas_facturas():

    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

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
            cambio
        FROM venta
        ORDER BY id_venta DESC
    """

    cursor.execute(sql)
    resultado = cursor.fetchall()
    cursor.close()
    conexion.close()

    return resultado


# =====================================================
# OBTENER FACTURA POR ID
# =====================================================

def obtener_factura_por_id(id_venta):

    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

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
            cambio
        FROM venta
        WHERE id_venta = %s
    """

    cursor.execute(sql, (id_venta,))
    resultado = cursor.fetchone()
    cursor.close()
    conexion.close()

    return resultado


# =====================================================
# OBTENER DETALLES FACTURA
# =====================================================

def obtener_detalles_factura(id_venta):

    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
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

    cursor.execute(sql, (id_venta,))
    resultado = cursor.fetchall()
    cursor.close()
    conexion.close()

    return resultado


# =====================================================
# OBTENER CLIENTE POR ID
# =====================================================

def obtener_cliente_por_id(id_cliente):

    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

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
    cursor.execute(sql, (id_cliente,))
    resultado = cursor.fetchone()
    cursor.close()
    conexion.close()

    return resultado


# =====================================================
# OBTENER PRODUCTO POR ID
# =====================================================

def obtener_producto_por_id(id_producto):

    conexion = conectar()

    cursor = conexion.cursor(dictionary=True)

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
    cursor.execute(sql, (id_producto,))
    resultado = cursor.fetchone()
    cursor.close()
    conexion.close()

    return resultado


# =====================================================
# ANULAR FACTURA
# =====================================================

def eliminar_factura(id_venta):

    conexion = conectar()
    cursor = conexion.cursor()

    try:

        sql = """
            UPDATE venta
            SET estado = 'ANULADA'
            WHERE id_venta = %s
        """

        cursor.execute(sql, (id_venta,))
        conexion.commit()
        cursor.close()
        conexion.close()

        return True

    except Exception as e:

        conexion.rollback()
        cursor.close()
        conexion.close()

        print(f"Error al anular factura: {e}")

        return False


# =====================================================
# GUARDAR FACTURA
# =====================================================

def guardar_factura(factura_datos, detalles):

    conexion = conectar()
    cursor = conexion.cursor()

    try:

        sql_venta = """
            INSERT INTO venta (
                fecha,
                total,
                metodo_pago,
                estado,
                id_cliente,
                id_usuario,
                dinero_recibido,
                cambio
            )

            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """

        cursor.execute(sql_venta, (
            factura_datos.get('fecha'),
            factura_datos.get('total', 0),
            factura_datos.get('metodo_pago'),
            "ACTIVA",
            factura_datos.get('id_cliente'),
            factura_datos.get('id_usuario', 1),
            factura_datos.get('dinero_recibido', 0),
            factura_datos.get('cambio', 0)

        ))
        id_venta = cursor.lastrowid

        # ------------------------------------
        # GUARDAR DETALLES
        # ------------------------------------

        for detalle in detalles:

            id_producto = (
                detalle.get('id_producto')
                or detalle.get('id')
            )
            cantidad = detalle.get('cantidad')
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
            cursor.execute(sql_detalle, (
                id_venta,
                id_producto,
                cantidad,
                detalle.get('precio'),
                detalle.get('subtotal')
            ))

            # --------------------------------
            # DESCONTAR STOCK
            # --------------------------------

            sql_actualizar_stock = """
                UPDATE producto
                SET stock = stock - %s
                WHERE id_producto = %s
            """
            cursor.execute(sql_actualizar_stock, (
                cantidad,
                id_producto
            ))

        conexion.commit()
        cursor.close()
        conexion.close()

        return id_venta

    except Exception as e:
        conexion.rollback()
        cursor.close()
        conexion.close()
        
        print(f"Error al guardar factura: {e}")
        return None
    
# =====================================================
# CREAR CLIENTE
# =====================================================

def crear_cliente(datos):

    conexion = conectar()
    cursor = conexion.cursor()
    sql = """
        INSERT INTO clientes (

            nombre,
            documento,
            direccion,
            telefono,
            rol
        )
        VALUES (%s, %s, %s, %s, %s)
    """

    try:

        cursor.execute(sql, (
            datos['nombre'],
            datos['documento'],
            datos['direccion'],
            datos['telefono'],
            datos['rol']
        ))

        conexion.commit()

        # Retorno el ID creado
        return cursor.lastrowid

    except Exception as err:

        print(f"Error al crear cliente: {err}")
        conexion.rollback()
        return None

    finally:
        cursor.close()
        conexion.close()


# =====================================================
# CREAR PRODUCTO
# =====================================================

def crear_producto(datos):

    conexion = conectar()
    cursor = conexion.cursor()

    sql = """
        INSERT INTO producto (
            nombre,
            unidad,
            lugar,
            precio,
            stock
        )
        VALUES (%s, %s, %s, %s, %s)
    """
    try:

        cursor.execute(sql, (
            datos['nombre'],
            datos['unidad'],
            datos['lugar'],
            datos['precio'],
            datos['stock']
        ))

        conexion.commit()

        # Retorno el ID del producto creado
        return cursor.lastrowid

    except Exception as err:

        print(f"Error al crear producto: {err}")
        conexion.rollback()
        return None

    finally:
        cursor.close()
        conexion.close()