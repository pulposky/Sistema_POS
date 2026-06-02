from database.bd import conectar


# =====================================================
# BUSCAR PRODUCTOS
# =====================================================

def buscar_producto():
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    sql = """
        SELECT *
        FROM producto
        WHERE stock <= 0
    """
    cursor.execute(sql)
    resultado = cursor.fetchall()
    cursor.close()
    conexion.close()

    return resultado