from database.bd import conectar


#=====================================================
# CREAR USUARIO
#=====================================================

def crear_usuario(nombre, usuario, password, rol):
    conexion = conectar()
    cursor = conexion.cursor()
    sql = "INSERT INTO usuarios (nombre, usuario, password, rol) VALUES (%s, %s, %s, %s)"
    valores = (nombre, usuario, password, rol)
    cursor.execute(sql, valores)
    conexion.commit()
    cursor.close()
    conexion.close()