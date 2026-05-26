import flet as ft
import os
from models.loginModel import iniciar_sesion
# =========================================================
# LOGIN
# =========================================================
def login_view(pagina: ft.Page, ir_a_main, ir_a_menu):

    # Limpio la consola y la pantalla
    os.system('cls')
    pagina.clean()

    # Tamaño de la ventana para el login
    pagina.window.width = 400
    pagina.window.height = 600

    # Centro todo el contenido
    pagina.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    pagina.vertical_alignment = ft.MainAxisAlignment.CENTER

    # ---------------- FUNCIONES ----------------

    # Valido el usuario y la contraseña cuando el usuario intenta ingresar
    def actualizar_mensaje():
        if usuario.value == "" and password.value == "":
            mensaje.value = "Por favor, ingrese su usuario y contraseña."
            mensaje.color = "orange"
        else:
            # Si las credenciales son correctas navego al menu
            resultado = iniciar_sesion(usuario.value, password.value)
            if resultado:
                mensaje.value = "¡Inicio de sesión exitoso!"
                mensaje.color = "green"
                ir_a_menu(resultado)
            else:
                mensaje.value = "Usuario o contraseña incorrectos."
                mensaje.color = "red"

        pagina.update()

    # ---------------- CONTROLES ----------------

    # Campo de texto para el usuario
    usuario = ft.TextField(
        label="Usuario",
        width=250,
        autofocus=True,
        on_submit=lambda e: actualizar_mensaje()
    )

    # Campo de texto para la contraseña, oculta lo que escribe el usuario
    password = ft.TextField(
        label="Contraseña",
        password=True,
        width=250,
        on_submit=lambda e: actualizar_mensaje()
    )

    # Logo del SENA
    logo = ft.Image(
        src="assets/Logo_sena.png", 
        width=200,
        height=100
    )

    # Texto que muestra mensajes de error o exito
    mensaje = ft.Text("")

    # Boton para iniciar sesion
    btn_login = ft.Button(
        "Ingresar [Enter]",
        bgcolor="green",
        color="white",
        width=200,
        on_click=lambda e: actualizar_mensaje()
    )

    async def teclado(e: ft.KeyboardEvent):
        # Si el usuario presiona Escape vuelvo al main
        if e.key == "Escape":
            ir_a_main()


    # Activo la deteccion de teclado en la pagina
    pagina.on_keyboard_event = teclado

    # Boton para volver al main
    btn_return = ft.Button(
        "Volver",
        bgcolor="gray",
        color="black",
        width=200,
        on_click=lambda e: ir_a_main()
    )

    # ---------------- INTERFAZ ----------------
    pagina.add(
        ft.Container(
            content=ft.Column(
                [
                    logo,
                    ft.Text("Sistema de Punto de Venta", size=22, weight="bold"),
                    ft.Text("Inicio de sesión"),
                    usuario,
                    password,
                    btn_login,
                    btn_return,
                    mensaje
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=15
            ),
            padding=30,
            border_radius=15,
            bgcolor=ft.Colors.WHITE,
            shadow=ft.BoxShadow(
                blur_radius=12,
                spread_radius=2,
                color=ft.Colors.BLACK_12
            )
        )
    )