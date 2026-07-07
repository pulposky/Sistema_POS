from models.usuariosModel import crear_usuario


def guardar_usuario(nombre, usuario, password, rol):
    crear_usuario(nombre, usuario, password, rol)
    