"""
Módulo de conexión a la base de datos MySQL.

Este archivo centraliza la configuración y el establecimiento de la
conexión con el servidor MySQL que almacena la información del sistema
POS (ventas, inventario, usuarios, facturas, etc.).

Los parámetros de conexión se leen desde variables de entorno para
facilitar el despliegue en diferentes entornos (desarrollo, producción),
pero también incluye valores por defecto para ejecución local.

Uso típico:
    from database.bd import conectar
    conexion = conectar()
    # ... usar la conexión ...
    conexion.close()
"""

import os
import mysql.connector


# Configuración de conexión a la base de datos MySQL.
# Los valores se pueden definir mediante variables de entorno o ajustar directamente aquí.

# Host: servidor donde se ejecuta MySQL. Por defecto es la máquina local.
DB_HOST = os.getenv("DB_HOST", "localhost")

# Usuario de MySQL con permisos para acceder a la base de datos del sistema.
DB_USER = os.getenv("DB_USER", "root")

# Contraseña del usuario de MySQL. En desarrollo local puede estar vacía.
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# Nombre de la base de datos que contiene las tablas del sistema POS.
DB_NAME = os.getenv("DB_NAME", "sena_pdv")

# Puerto de escucha de MySQL. El estándar es 3306.
# Se convierte a entero porque las variables de entorno siempre son strings.
DB_PORT = int(os.getenv("DB_PORT", "3306"))


def conectar():
    """
    Establece y retorna una conexión con la base de datos MySQL.

    Utiliza los parámetros globales DB_HOST, DB_USER, DB_PASSWORD,
    DB_NAME y DB_PORT para configurar la conexión.

    Retorna:
        mysql.connector.connection.MySQLConnection | None:
            Objeto de conexión válido si todo salió bien, o None
            si ocurrió un error al conectar.

    Ejemplo de uso:
        conexion = conectar()
        if conexion:
            cursor = conexion.cursor()
            cursor.execute("SELECT * FROM usuarios")
            ...
            conexion.close()
    """
    try:
        conexion = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            port=DB_PORT
        )
        return conexion
    except mysql.connector.Error as err:
        # Se imprime el error en consola para facilitar la depuración
        # en desarrollo. En producción se podría registrar en un archivo de log.
        print(f"Error de conexión a la base de datos: {err}")
        return None
