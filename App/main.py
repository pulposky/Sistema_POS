"""
Módulo principal del sistema POS (Punto de Venta) del SENA.

Este archivo es el punto de entrada de la aplicación Flet.
Se encarga de:
  - Crear y configurar la ventana principal del sistema.
  - Probar la conexión a la base de datos antes de iniciar.
  - Resolver qué vista abrir según las variables de entorno
    (POS_VIEW y POS_USUARIO), lo que permite abrir ventanas
    secundarias desde el módulo de seguridad/permisos.
  - De lo contrario, lanzar la pantalla de inicio estándar.

La app se ejecuta con `ft.run(main, assets_dir="assets")` al final
del archivo, lo que arranca el loop de eventos de Flet.
"""

import json
import os
import flet as ft

# Punto de entrada principal del sistema.
# Aquí se inicia la aplicación y se define el comportamiento inicial de la ventana.
from routers.navegacion import configurar_rutas

# ---------------- BASE DE DATOS ----------------
from database.bd import conectar


def probar_conexion():
    """
    Verifica que la conexión a la base de datos MySQL funcione correctamente.

    Se llama una sola vez al iniciar la aplicación. Si la conexión
    es exitosa se imprime un mensaje de confirmación y se cierra
    el recurso. Si falla, se captura la excepción y se muestra
    el error en consola para facilitar la depuración.

    No retorna valores; su propósito es únicamente de validación.
    """
    try:
        conexion = conectar()
        print("Base de datos conectada")
        conexion.close()
    except Exception as error:
        print("Error de conexión:", error)


#---------------- VISTAS ----------------
def main(pagina: ft.Page):
    """
    Función principal que Flet ejecuta como entry point de la aplicación.

    Configura la ventana (título, tema, ícono) y determina qué vista
    mostrar dependiendo de las variables de entorno:

    - Si POS_VIEW indica una vista específica (factura, compra, remisión,
      entrada) y POS_USUARIO contiene los datos del usuario en JSON,
      abre esa vista directamente como ventana secundaria.
    - Si no hay variables de entorno o la vista no es reconocida,
      se muestra la pantalla de inicio estándar.

    Parámetros:
        pagina (ft.Page): Objeto que representa la ventana principal
                          de la aplicación Flet. Flet lo crea
                          automáticamente y lo pasa a esta función.
    """

    # Verifica la base de datos una sola vez al iniciar la app
    probar_conexion()

    # Configuración general
    pagina.title = "SENA"

    pagina.theme_mode = ft.ThemeMode.LIGHT

    pagina.window.icon = "Logo_sena.ico"

    # Inicio las rutas disponibles de la app
    # configurar_rutas retorna un diccionario de funciones de navegación
    # y la función de inicio por defecto
    rutas, iniciar = configurar_rutas(pagina)

    # Leo la vista que se debe abrir desde la nueva instancia
    # POS_VIEW se establece cuando el módulo de seguridad lanza una
    # nueva ventana para una función específica (ej. facturación)
    vista = os.getenv("POS_VIEW", "").strip().lower()
    # POS_USUARIO contiene el objeto del usuario logueado serializado
    # en JSON, para que la nueva ventana sepa quién está operando
    usuario_json = os.getenv("POS_USUARIO", "")

    # Si viene una vista específica, la abro directamente en la nueva ventana
    # Cada bloque verifica que exista un usuario válido antes de navegar;
    # si no hay usuario, cae a la pantalla de inicio por seguridad
    if vista in {"factura", "venta", "vender"}:
        # Deserializo el JSON del usuario; si viene vacío, queda en None
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
# ft.run arranca el loop de eventos y llama a `main` pasándole
# el objeto Page. assets_dir indica dónde están los recursos
# estáticos (imágenes, íconos, etc.) que usa la aplicación.
if __name__ == "__main__":
    ft.run(main, assets_dir="assets")
