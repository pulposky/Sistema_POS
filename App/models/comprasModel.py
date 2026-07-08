from database.bd import conectar

# Modelo de compras.
# Contiene las operaciones de base de datos para compras y proveedores.
def buscar_proveedor(texto):
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    sql = """
        SELECT *
        FROM proveedores
        WHERE nombre LIKE %s
        LIMIT 20
    """

    cursor.execute(sql, (f"%{texto}%",))

    resultados = cursor.fetchall()

    cursor.close()
    conexion.close()

    return resultados


def crear_proveedor(datos):
    conexion = conectar()
    cursor = conexion.cursor()

    try:
        sql = """
            INSERT INTO proveedores (nombre)
            VALUES (%s)
        """
        cursor.execute(sql, (datos.get("nombre", ""),))
        conexion.commit()
        id_nuevo = cursor.lastrowid

        cursor.close()
        conexion.close()

        return id_nuevo

    except Exception as e:
        conexion.rollback()
        cursor.close()
        conexion.close()
        print(f"Error al crear proveedor: {e}")
        return None

def guardar_compra(compra_datos, detalles):
    conexion = conectar()
    cursor = conexion.cursor()

    try:
        sql_compra = """
            INSERT INTO compras (
                fecha,
                total,
                id_proveedor,
                id_usuario,
                estado
            ) VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(sql_compra, (
            compra_datos.get('fecha'),
            compra_datos.get('total', 0),
            compra_datos.get('id_proveedor'),
            compra_datos.get('id_usuario', 1),
            compra_datos.get('estado', 'ACTIVA')
        ))
        id_compra = cursor.lastrowid

        for detalle in detalles:
            id_producto = detalle.get('id') or detalle.get('id_producto')
            cantidad = detalle.get('cantidad', 0)
            sql_detalle = """
                INSERT INTO detalle_compras (
                    id_compra,
                    id_producto,
                    cantidad,
                    precio_unitario,
                    subtotal
                ) VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(sql_detalle, (
                id_compra,
                id_producto,
                cantidad,
                detalle.get('precio'),
                detalle.get('subtotal')
            ))

            sql_actualizar_stock = """
                UPDATE producto
                SET stock = stock + %s
                WHERE id_producto = %s
            """
            cursor.execute(sql_actualizar_stock, (
                cantidad,
                id_producto
            ))

        conexion.commit()
        cursor.close()
        conexion.close()

        return id_compra

    except Exception as e:
        conexion.rollback()
        cursor.close()
        conexion.close()
        print(f"Error al guardar compra: {e}")
        return None


def obtener_producto_stock(id_producto):
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    sql = """
        SELECT id_producto, nombre, stock
        FROM producto
        WHERE id_producto = %s
    """
    cursor.execute(sql, (id_producto,))
    resultado = cursor.fetchone()
    cursor.close()
    conexion.close()
    return resultado


def obtener_proveedor_por_id(id_proveedor):
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    sql = """
        SELECT
            id_proveedor,
            nombre
        FROM proveedores
        WHERE id_proveedor = %s
    """
    cursor.execute(sql, (id_proveedor,))
    resultado = cursor.fetchone()
    cursor.close()
    conexion.close()
    return resultado


def anular_compra(id_compra):
    conexion = conectar()
    cursor = conexion.cursor()
    try:
        sql = """
            UPDATE compras
            SET estado = 'ANULADA'
            WHERE id_compra = %s
        """
        cursor.execute(sql, (id_compra,))
        conexion.commit()
        cursor.close()
        conexion.close()
        return True
    except Exception as e:
        conexion.rollback()
        cursor.close()
        conexion.close()
        print(f"Error al anular compra: {e}")
        return False


def obtener_todas_compras():
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
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
    cursor.execute(sql)
    resultado = cursor.fetchall()
    cursor.close()
    conexion.close()
    return resultado


def obtener_compra_por_id(id_compra):
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
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
    cursor.execute(sql, (id_compra,))
    resultado = cursor.fetchone()
    cursor.close()
    conexion.close()
    return resultado


def obtener_detalles_compra(id_compra):
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
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
    cursor.execute(sql, (id_compra,))
    resultado = cursor.fetchall()
    cursor.close()
    conexion.close()
    return resultado
