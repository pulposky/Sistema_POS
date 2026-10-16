"""Helpers de autorización para los roles que pueden usar el POS."""


def normalizar_rol(rol):
    """Devuelve el rol normalizado para comparar sin distinguir mayúsculas."""
    return str(rol or "").strip().casefold()


def es_administrador(rol):
    return normalizar_rol(rol) in {"admin", "administrador"}


def es_facturador(rol):
    return normalizar_rol(rol) == "facturador"


def puede_ingresar(rol):
    return es_administrador(rol) or es_facturador(rol)
