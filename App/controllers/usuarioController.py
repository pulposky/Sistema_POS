from models.usuariosModel import crear_usuario

# Controlador para la gestión de usuarios.
# Se encarga de recibir los datos de la vista y enviarlos al modelo.

def guardar_usuario(nombre, usuario, password, rol):
    crear_usuario(nombre, usuario, password, rol)
    