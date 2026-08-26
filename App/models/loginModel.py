"""
Módulo de autenticación de usuarios.
Contiene la lógica para validar credenciales de acceso al sistema POS.
Se conecta a la tabla 'usuarios' de la base de datos para verificar
que el nombre de usuario y la contraseña coincidan con un registro existente.
"""

# Importa la función de conexión a la base de datos MySQL
from database.bd import conectar

# Modelo para autenticación de usuarios.

# Esta función verifica si el usuario existe en la base de datos
def iniciar_sesion(usuario, password):
    """
    Valida las credenciales de un usuario contra la base de datos.

    Parámetros:
        usuario (str): Nombre de usuario ingresado por el usuario.
        password (str): Contraseña ingresada por el usuario.

    Retorna:
        dict o None: Un diccionario con los datos del usuario si las
        credenciales son correctas (incluye id_usuario, nombre, rol, etc.),
        o None si no se encontró ningún registro que coincida.
    """

    # Conecto a la base de datos
    # Establece conexión con MySQL usando la función auxiliar de bd.py
    conexion = conectar()

    # Cursor tipo diccionario
    # Se usa dictionary=True para que cada fila se devuelva como un diccionario
    # en lugar de una tupla, permitiendo acceder a las columnas por nombre
    cursor = conexion.cursor(dictionary=True)

    # Consulta SQL
    # Busca un registro en la tabla 'usuarios' donde el nombre de usuario
    # Y la contraseña coincidan exactamente con los parámetros recibidos.
    # Se usa %s como placeholder para prevenir inyección SQL
    sql = """SELECT * FROM usuarios WHERE usuario = %s AND password = %s"""

    # Ejecuto la consulta
    # Se pasan los parámetros de forma segura como tupla para que MySQL
    # los escape correctamente y se evite la inyección SQL
    cursor.execute(
        sql,
        (usuario, password)
    )

    # Obtengo un solo resultado
    # fetchone() retorna solo la primera fila encontrada o None si no hay
    # coincidencias. Se usa fetchone() porque solo puede existir un usuario
    # con ese nombre y contraseña
    resultado = cursor.fetchone()

    cursor.close()
    conexion.close()

    # Retorno el usuario encontrado
    # Si las credenciales son correctas, retorna un diccionario con los
    # datos del usuario. Si son incorrectas, retorna None
    return resultado
