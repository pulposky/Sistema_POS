import json
import os
import subprocess
# Utilidad para abrir una nueva instancia de la factura o compra en otra ventana.
import sys
from pathlib import Path


# ============================================================================
# MÓDULO DE APERTURA DE NUEVAS VENTANAS
# ============================================================================
# Permite abrir una nueva instancia de la aplicación POS en una ventana
# separada, sin interrumpir el proceso actual. Esto es útil cuando el
# usuario necesita crear un nuevo documento (factura o compra) mientras
# está trabajando en otro.
#
# La nueva instancia recibe la vista a mostrar y los datos del usuario
# a través de variables de entorno, las cuales son leídas por main.py
# al iniciar.
# ============================================================================


def abrir_nueva_instancia(tipo_vista, usuario):
    """
    Abre una nueva ventana de la aplicación con la vista y usuario indicados.

    Lanza un nuevo proceso de Python ejecutando main.py con variables de
    entorno que indican qué vista abrir y qué usuario está autenticado.

    Parámetros:
        tipo_vista (str): Tipo de vista a abrir en la nueva ventana
            (ej. "ventas", "compras"). Se pasa a main.py como POS_VIEW.
        usuario (dict): Datos del usuario autenticado, serializado como
            JSON y pasado como POS_USUARIO en el entorno.
    """
    # Ruta principal de la aplicación (carpeta App/)
    app_dir = Path(__file__).resolve().parents[1]

    # Creo un entorno con la vista y el usuario para que la nueva ventana se abra correctamente
    entorno = os.environ.copy()
    entorno["POS_VIEW"] = tipo_vista
    entorno["POS_USUARIO"] = json.dumps(usuario)

    # Comando para iniciar la app en una nueva instancia
    argumentos = [sys.executable, str(app_dir / "main.py")]
    opciones = {
        "cwd": str(app_dir),       # Directorio de trabajo: App/
        "env": entorno,             # Variables de entorno personalizadas
        "stdout": subprocess.DEVNULL,  # Redirijo salida para no saturar la consola
        "stderr": subprocess.DEVNULL,
        "stdin": subprocess.DEVNULL,
    }

    # En Windows se evita mostrar la consola de fondo para que solo aparezca la interfaz de la app
    if os.name == "nt":
        opciones["creationflags"] = subprocess.CREATE_NO_WINDOW

    # Inicio la nueva instancia de la aplicación
    subprocess.Popen(argumentos, **opciones)
