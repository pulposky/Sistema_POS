import json
import os
import subprocess
# Utilidad para abrir una nueva instancia de la factura o compra en otra ventana.
import sys
from pathlib import Path


# Función para abrir una nueva ventana de la app desde la vista actual
# Esto permite crear otro documento sin interrumpir el proceso que ya está en marcha
def abrir_nueva_instancia(tipo_vista, usuario):
    # Ruta principal de la aplicación
    app_dir = Path(__file__).resolve().parents[1]

    # Creo un entorno con la vista y el usuario para que la nueva ventana se abra correctamente
    entorno = os.environ.copy()
    entorno["POS_VIEW"] = tipo_vista
    entorno["POS_USUARIO"] = json.dumps(usuario)

    # Comando para iniciar la app en una nueva instancia
    argumentos = [sys.executable, str(app_dir / "main.py")]
    opciones = {
        "cwd": str(app_dir),
        "env": entorno,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "stdin": subprocess.DEVNULL,
    }

    # En Windows se evita mostrar la consola de fondo para que solo aparezca la interfaz de la app
    if os.name == "nt":
        opciones["creationflags"] = subprocess.CREATE_NO_WINDOW

    # Inicio la nueva instancia de la aplicación
    subprocess.Popen(argumentos, **opciones)
