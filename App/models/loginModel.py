from database.bd import conectar


# Esta función verifica si el usuario existe en la base de datos
def iniciar_sesion(usuario, password):

    # Conecto a la base de datos
    conexion = conectar()

    # Cursor tipo diccionario
    cursor = conexion.cursor(dictionary=True)

    # Consulta SQL
    sql = """SELECT * FROM usuarios WHERE usuario = %s AND password = %s"""

    # Ejecuto la consulta
    cursor.execute(
        sql,
        (usuario, password)
    )

    # Obtengo un solo resultado
    resultado = cursor.fetchone()

    # Cierro conexión
    cursor.close()

    conexion.close()

    # Retorno el usuario encontrado
    return resultado