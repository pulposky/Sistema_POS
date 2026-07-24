import os
import mysql.connector


# Configuración de conexión a la base de datos MySQL.
# Los valores se pueden definir mediante variables de entorno o ajustar directamente aquí.
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "sena_pdv")
DB_PORT = int(os.getenv("DB_PORT", "3306"))


def conectar():
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
        print(f"Error de conexión a la base de datos: {err}")
        return None
