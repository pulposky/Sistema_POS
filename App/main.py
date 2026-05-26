import flet as ft

# Importo la navegación
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

    # Inicio las rutas
    iniciar = configurar_rutas(pagina)

    # Muestro la vista inicial
    iniciar()

# Inicio Flet
if __name__ == "__main__":
    ft.run(main)