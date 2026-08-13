import json
import os
import flet as ft

# Punto de entrada principal del sistema.
# Aquí se inicia la aplicación y se define el comportamiento inicial de la ventana.
from routers.navegacion import configurar_rutas

# ---------------- BASE DE DATOS ----------------
from database.bd import conectar


def probar_conexion():
    try:                                                        
        conexion = conectar()
        print("Base de datos conectada")
        conexion.close()
    except Exception as error:
        print("Error de conexión:", error)

#---------------- VISTAS ----------------
def main(pagina: ft.Page):

    # Verifica la base de datos una sola vez al iniciar la app
    probar_conexion()

    # Configuración general
    pagina.title = "SENA"

    pagina.theme_mode = ft.ThemeMode.LIGHT

    # Inicio las rutas disponibles de la app
    rutas, iniciar = configurar_rutas(pagina)

    # Leo la vista que se debe abrir desde la nueva instancia
    vista = os.getenv("POS_VIEW", "").strip().lower()
    usuario_json = os.getenv("POS_USUARIO", "")

    # Si viene una vista específica, la abro directamente en la nueva ventana
    if vista in {"factura", "venta", "vender"}:
        usuario = json.loads(usuario_json) if usuario_json else None
        if usuario:
            rutas["vender"](usuario)
        else:
            iniciar()
    elif vista in {"compra", "compras"}:
        usuario = json.loads(usuario_json) if usuario_json else None
        if usuario:
            rutas["compras"](usuario)
        else:
            iniciar()
    elif vista == "remision":
        usuario = json.loads(usuario_json) if usuario_json else None
        if usuario:
            rutas["remision"](usuario)
        else:
            iniciar()
    elif vista in {"entrada", "entradas"}:
        usuario = json.loads(usuario_json) if usuario_json else None
        if usuario:
            rutas["entradas"](usuario)
        else:
            iniciar()
    else:
        # Si no viene una vista especial, sigo con la vista inicial normal
        iniciar()

# Inicio Flet
if __name__ == "__main__":
    ft.run(main)
