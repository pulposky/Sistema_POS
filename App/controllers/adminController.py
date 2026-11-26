"""
Controlador del Panel de Administración
========================================
Módulo encargado de la lógica de negocio del módulo de administración:
gestión de usuarios, catálogo de productos, indicadores y respaldos.

Actúa como puente entre la vista del panel (views/adminPanel.py) y el
modelo de persistencia (models/adminModel.py). Todas las operaciones
levantan ValueError con un mensaje en español claro cuando los datos
no son válidos, para que la vista solo tenga que mostrarlo.
"""

from models import adminModel
from models.usuariosModel import crear_usuario
from utils.roles import es_administrador

# Longitud mínima aceptada para una contraseña.
LONGITUD_MINIMA_PASSWORD = 4

# Valores por defecto al crear un producto cuando el formulario no envía
# unidad, origen ni categoría.
UNIDAD_POR_DEFECTO = "UND"
EMPRESA_POR_DEFECTO = "SenaEmpresa"
CATEGORIA_POR_DEFECTO = "Abonos y Sustratos"


# =========================================================
# INDICADORES
# =========================================================

def obtener_estadisticas():
    """Retorna los indicadores del panel de control (diccionario vacío si falla la BD)."""
    return adminModel.obtener_estadisticas()


# =========================================================
# USUARIOS
# =========================================================

def listar_usuarios():
    """Retorna la lista de usuarios del sistema."""
    return adminModel.listar_usuarios()


def crear_usuario_admin(nombre, usuario, password, rol):
    """
    Valida y crea un nuevo usuario del sistema.

    Lanza ValueError si falta algún campo o si el login ya existe.
    """
    nombre = (nombre or "").strip()
    usuario = (usuario or "").strip()
    password = password or ""

    if not nombre:
        raise ValueError("El nombre es obligatorio.")
    if not usuario:
        raise ValueError("El usuario (login) es obligatorio.")
    if len(password) < LONGITUD_MINIMA_PASSWORD:
        raise ValueError(f"La contraseña debe tener al menos {LONGITUD_MINIMA_PASSWORD} caracteres.")
    if not es_administrador(rol) and rol != "Facturador":
        raise ValueError("Selecciona un rol válido.")

    return crear_usuario(nombre, usuario, password, rol)


def actualizar_usuario(id_usuario, nombre, usuario, rol, admin_id=None):
    """
    Valida y actualiza nombre, login y rol de un usuario.

    Protecciones de negocio:
      - El administrador que tiene la sesión abierta no puede quitarse
        su propio rol de administrador.
      - No se puede dejar al sistema sin al menos un administrador.

    Lanza ValueError si alguna validación falla.
    """
    nombre = (nombre or "").strip()
    usuario = (usuario or "").strip()

    if not nombre:
        raise ValueError("El nombre es obligatorio.")
    if not usuario:
        raise ValueError("El usuario (login) es obligatorio.")
    if not es_administrador(rol) and rol != "Facturador":
        raise ValueError("Selecciona un rol válido.")

    objetivo = adminModel.obtener_usuario(id_usuario)
    if not objetivo:
        raise ValueError("El usuario ya no existe.")

    # Si el usuario deja de ser administrador, valido que no sea el último
    if es_administrador(objetivo.get("rol")) and not es_administrador(rol):
        if admin_id is not None and id_usuario == admin_id:
            raise ValueError("No puedes quitar tu propio rol de administrador.")
        if adminModel.contar_administradores(excluyendo_id=id_usuario) == 0:
            raise ValueError(
                "No se puede quitar el rol: debe quedar al menos "
                "un administrador en el sistema."
            )

    return adminModel.actualizar_usuario(id_usuario, nombre, usuario, rol)


def cambiar_password(id_usuario, password, confirmacion):
    """
    Valida y cambia la contraseña de un usuario.

    Lanza ValueError si la contraseña es muy corta o si la confirmación
    no coincide.
    """
    password = password or ""
    if len(password) < LONGITUD_MINIMA_PASSWORD:
        raise ValueError(f"La contraseña debe tener al menos {LONGITUD_MINIMA_PASSWORD} caracteres.")
    if password != (confirmacion or ""):
        raise ValueError("La confirmación no coincide con la contraseña.")

    return adminModel.cambiar_password(id_usuario, password)


def eliminar_usuario(id_usuario, admin_id=None):
    """
    Valida y elimina un usuario del sistema.

    Protecciones de negocio:
      - No se puede eliminar el usuario con el que se abrió la sesión
        de administración.
      - No se puede eliminar al último administrador del sistema.

    Lanza ValueError si alguna validación falla o si el usuario tiene
    documentos asociados.
    """
    if admin_id is not None and id_usuario == admin_id:
        raise ValueError("No puedes eliminar el usuario con el que abriste la sesión de administración.")

    objetivo = adminModel.obtener_usuario(id_usuario)
    if not objetivo:
        raise ValueError("El usuario ya no existe.")

    if es_administrador(objetivo.get("rol")) and adminModel.contar_administradores(excluyendo_id=id_usuario) == 0:
        raise ValueError(
            "No se puede eliminar: debe quedar al menos un administrador en el sistema."
        )

    return adminModel.eliminar_usuario(id_usuario)


# =========================================================
# PRODUCTOS
# =========================================================

def listar_productos(filtro=""):
    """Retorna el catálogo de productos (con filtro opcional de búsqueda)."""
    return adminModel.listar_productos(filtro)


def guardar_producto(datos, id_producto=None):
    """
    Valida y guarda un producto (nuevo o existente).

    'datos' es un dict con: codigo, nombre, unidad, lugar, precio,
    categoria, stock, estado y descripcion.

    Lanza ValueError si falta un campo o si precio/stock no son numéricos.
    """
    codigo = (datos.get("codigo") or "").strip()
    nombre = (datos.get("nombre") or "").strip()

    if not codigo:
        raise ValueError("El código es obligatorio.")
    if not nombre:
        raise ValueError("El nombre es obligatorio.")

    try:
        precio = float(datos.get("precio", 0) or 0)
    except (TypeError, ValueError):
        raise ValueError("El precio debe ser un número.")
    if precio < 0:
        raise ValueError("El precio no puede ser negativo.")

    try:
        stock = float(datos.get("stock", 0) or 0)
    except (TypeError, ValueError):
        raise ValueError("El stock debe ser un número.")

    # Unidad, origen y categoría por defecto si el formulario no los envía.
    producto = {
        "codigo": codigo,
        "nombre": nombre,
        "unidad": (datos.get("unidad") or UNIDAD_POR_DEFECTO).strip(),
        "lugar": (datos.get("lugar") or EMPRESA_POR_DEFECTO).strip(),
        "precio": precio,
        "categoria": (datos.get("categoria") or CATEGORIA_POR_DEFECTO).strip(),
        "stock": stock,
        "estado": (datos.get("estado") or "inactivo").strip(),
        "descripcion": (datos.get("descripcion") or "").strip(),
    }

    return adminModel.guardar_producto(producto, id_producto)


def eliminar_producto(id_producto):
    """
    Elimina un producto del catálogo.

    Lanza ValueError si el producto tiene movimientos asociados.
    """
    return adminModel.eliminar_producto(id_producto)


# =========================================================
# RESPALDO DE LA BASE DE DATOS
# =========================================================

def generar_respaldo(ruta_destino):
    """
    Genera el respaldo .sql de la base de datos en la ruta indicada.

    Lanza ValueError si mysqldump no está disponible o si el respaldo falla.
    """
    return adminModel.generar_respaldo(ruta_destino)
