from database.bd import conectar
# =====================================================
# GUARDAR REMISION
# =====================================================
def guardar_remision(remision_datos, detalles):
    conexion = conectar()
    cursor = conexion.cursor()

    try:
        sql_remision = """
            INSERT INTO remision (fecha, tipo_remision, id_cliente, id_usuario, notas)
            VALUES (%s, %s, %s, %s, %s)
        """

        cursor.execute(sql_remision, (
            remision_datos.get("fecha"),
            remision_datos.get("tipo_remision"),
            remision_datos.get("id_cliente"),
            remision_datos.get("id_usuario", 1),
            remision_datos.get("notas", ""),
        ))

        id_remision = cursor.lastrowid

        sql_detalle = """
            INSERT INTO detalle_remision (id_remision, id_producto, cantidad)
            VALUES (%s, %s, %s)
        """

        for detalle in detalles:
            id_producto = detalle.get("id_producto") or detalle.get("id")
            cantidad = detalle.get("cantidad", 1)
            cursor.execute(sql_detalle, (
                id_remision,
                id_producto,
                cantidad,
            ))

            sql_actualizar_stock = """UPDATE producto SET stock = stock - %s WHERE id_producto = %s"""
            cursor.execute(sql_actualizar_stock, (cantidad, id_producto))

        conexion.commit()
        cursor.close()
        conexion.close()
        return id_remision
    except Exception as err:
        conexion.rollback()
        cursor.close()
        conexion.close()
        print(f"Error al guardar remision: {err}")
        return None

# =====================================================
# OBTENER REMISIONES
# =====================================================
def obtener_todas_remisiones():
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    sql = """
        SELECT id_remision, fecha, tipo_remision, id_cliente, id_usuario, notas
        FROM remision
        ORDER BY id_remision DESC
    """

    cursor.execute(sql)
    resultado = cursor.fetchall()

    cursor.close()
    conexion.close()
    return resultado

# =====================================================
# OBTENER REMISION POR ID
# =====================================================
def obtener_remision_por_id(id_remision):
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    sql = """
        SELECT id_remision, fecha, tipo_remision, id_cliente, id_usuario, notas
        FROM remision
        WHERE id_remision = %s
    """

    cursor.execute(sql, (id_remision,))
    resultado = cursor.fetchone()

    cursor.close()
    conexion.close()
    return resultado

# =====================================================
# OBTENER DETALLES DE REMISION
# =====================================================
def obtener_detalles_remision(id_remision):
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    sql = """
        SELECT id_detalle_remision, id_remision, id_producto, cantidad
        FROM detalle_remision
        WHERE id_remision = %s
    """

    cursor.execute(sql, (id_remision,))
    resultado = cursor.fetchall()

    cursor.close()
    conexion.close()
    return resultado

# =====================================================
# ELIMINAR REMISION
# =====================================================
def eliminar_remision(id_remision):
    conexion = conectar()
    cursor = conexion.cursor()

    try:
        # SOLO CAMBIA EL ESTADO
        cursor.execute(
            """
            UPDATE remision
            SET estado = 'ANULADA'
            WHERE id_remision = %s
            """,
            (id_remision,)
        )
        conexion.commit()
        cursor.close()
        conexion.close()
        return True

    except Exception as err:
        conexion.rollback()
        cursor.close()
        conexion.close()
        print(f"Error al anular remision: {err}")

        return False