"""
Controlador de Usuarios
========================
Módulo encargado de la lógica de negocio para la gestión de usuarios del sistema.
Actualmente solo soporta la creación de nuevos usuarios.

Este es un controlador simple que actúa como puente entre la vista de
registro de usuarios y el modelo de persistencia. La validación de datos
(su inputs) y el hash de contraseña se realizan en el modelo.
"""

from models.usuariosModel import crear_usuario

# Controlador para la gestión de usuarios.
# Se encarga de recibir los datos de la vista y enviarlos al modelo.

def guardar_usuario(nombre, usuario, password, rol):
    """
    Guarda un nuevo usuario en la base de datos.

    Recibe los datos del formulario de registro y los delega al modelo
    crear_usuario, que se encarga de validar, hashear la contraseña
    y persistir el registro.

    Args:
        nombre (str): Nombre completo del usuario (se muestra en facturas, etc.).
        usuario (str): Nombre de usuario para iniciar sesión (debe ser único).
        password (str): Contraseña en texto plano (el modelo la hashea antes de guardar).
        rol (str): Rol del usuario ('ADMIN', 'CAJERO', etc.).

    Returns:
        bool: True si el usuario se creó correctamente, False si hubo error
            (por ejemplo, nombre de usuario duplicado).
    """
    return crear_usuario(nombre, usuario, password, rol)
