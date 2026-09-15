"""
Módulo de gestión de usuarios del sistema POS.
Proporciona funciones para crear nuevos usuarios en la base de datos.
Cada usuario tiene un nombre, nombre de usuario (login), contraseña y rol
que determina sus permisos dentro del sistema (administrador, vendedor, etc.).
"""

# Importa la función de conexión a la base de datos MySQL
from database.bd import conectar

# Librería para hashear contraseñas de forma segura
import bcrypt

# Modelo para gestionar usuarios del sistema.

#=====================================================
# CREAR USUARIO
#=====================================================

def crear_usuario(nombre, usuario, password, rol):
    """
    Inserta un nuevo usuario en la tabla 'usuarios' de la base de datos.

    Parámetros:
        nombre (str): Nombre completo del usuario (para mostrar en la interfaz).
        usuario (str): Nombre de usuario único para iniciar sesión.
        password (str): Contraseña del usuario (se almacena en texto plano,
                        se recomienda usar hash en producción).
        rol (str): Rol del usuario, define permisos (ej: 'admin', 'vendedor').

    Retorna:
        int: El ID del usuario recién creado (lastrowid), útil para
        operaciones posteriores que requieran referenciar al usuario.
    """

    # Establece conexión con la base de datos
    conexion = conectar()

    # Crea un cursor estándar (no diccionario) ya que solo necesitamos
    # ejecutar el INSERT y obtener el ID generado
    cursor = conexion.cursor()

    # Hashea la contraseña en texto plano antes de guardarla.
    # bcrypt añade una sal aleatoria, por lo que aunque dos usuarios tengan
    # la misma contraseña, sus hashes serán distintos. La contraseña nunca
    # se almacena en texto plano en la base de datos.
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    # Consulta SQL de inserción con placeholders %s para los valores
    # Inserta los cuatro campos requeridos: nombre, usuario, password y rol
    sql = "INSERT INTO usuarios (nombre, usuario, password, rol) VALUES (%s, %s, %s, %s)"

    # Tupla con los valores que reemplazarán los %s en la consulta SQL
    # Se guarda el hash en lugar de la contraseña en texto plano
    valores = (nombre, usuario, password_hash, rol)

    # Ejecuta la consulta INSERT en la base de datos
    cursor.execute(sql, valores)

    # Confirma la transacción para que los cambios se persistan en la base de datos
    # Sin commit(), los cambios serían temporales y se perderían al cerrar la conexión
    conexion.commit()

    # Obtiene el ID auto-generado por MySQL para el registro recién insertado
    # Esto funciona gracias al atributo AUTO_INCREMENT de la columna id_usuario
    id_usuario = cursor.lastrowid

    # Cierra el cursor para liberar memoria del lado del cliente
    cursor.close()

    # Cierra la conexión al servidor de base de datos
    conexion.close()

    # Retorna el ID del usuario creado para que la capa superior pueda
    # usarlo inmediatamente (por ejemplo, para mostrarlo o para otras operaciones)
    return id_usuario
