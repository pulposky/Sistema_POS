"""
Vista de inicio de sesión del sistema POS.

Muestra un formulario con campos de usuario y contraseña dentro de una tarjeta
centrada. Al autenticarse correctamente, navega al menú principal pasando los
datos del usuario logueado. Permite volver a la pantalla de bienvenida con
Escape o el botón "Volver".

Atajos de teclado:
    Enter  -> Intenta iniciar sesión (desde cualquier campo).
    Escape -> Regresa a la pantalla de bienvenida (inicio_view).

Navegación:
    ir_a_main()   -> Pantalla de bienvenida (inicio_view).
    ir_a_menu(d)  -> Menú principal con los datos del usuario autenticado.
"""

import flet as ft
import os
from models.loginModel import iniciar_sesion
# =========================================================
# LOGIN
# =========================================================
def login_view(pagina: ft.Page, ir_a_main, ir_a_menu):
    """
    Renderiza la pantalla de login y maneja la autenticación.

    Parámetros:
        pagina     -> Instancia de la página Flet actual.
        ir_a_main  -> Callback para navegar a la pantalla de bienvenida.
        ir_a_menu  -> Callback para navegar al menú principal. Se le pasa
                      el diccionario del usuario autenticado.
    """

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
        """Valida credenciales y navega al menú si son correctas."""
        if usuario.value == "" and password.value == "":
            # Ambos campos vacíos: muestro advertencia en naranja
            mensaje.value = "Por favor, ingrese su usuario y contraseña."
            mensaje.color = "orange"
        else:
            # Si las credenciales son correctas navego al menu
            resultado = iniciar_sesion(usuario.value, password.value)
            if resultado:
                # Login exitoso: muestro mensaje verde y navego al menú
                # pasando el diccionario del usuario (contiene id, nombre, rol, etc.)
                mensaje.value = "¡Inicio de sesión exitoso!"
                mensaje.color = "green"
                ir_a_menu(resultado)
            else:
                # Credenciales incorrectas: muestro mensaje en rojo
                mensaje.value = "Usuario o contraseña incorrectos."
                mensaje.color = "red"

        # Refresco la pantalla para mostrar el mensaje actualizado
        pagina.update()

    # ---------------- CONTROLES ----------------

    # Campo de texto para el usuario
    # autofocus=True coloca el cursor aquí al cargar la vista
    # on_submit se dispara al presionar Enter
    usuario = ft.TextField(
        label="Usuario",
        width=250,
        autofocus=True,
        on_submit=lambda e: actualizar_mensaje()
    )

    # Campo de texto para la contraseña, oculta lo que escribe el usuario
    # password=True oculta el texto con asteriscos
    # can_reveal_password=True muestra un ícono de ojo para revelar la contraseña
    password = ft.TextField(
        label="Contraseña",
        password=True,
        width=250,
        on_submit=lambda e: actualizar_mensaje(),
        can_reveal_password=True
    )

    # Logo del SENA
    logo = ft.Image(
        src="Logo_sena.png", 
        width=200,
        height=100
    )

    # Texto que muestra mensajes de error o exito
    mensaje = ft.Text("")

    # Boton para iniciar sesion
    # El texto indica que también puede usar Enter como atajo
    btn_login = ft.Button(
        "Ingresar [Enter]",
        bgcolor="green",
        color="white",
        width=200,
        on_click=lambda e: actualizar_mensaje()
    )

    async def teclado(e: ft.KeyboardEvent):
        """
        Manejador de eventos de teclado global para esta vista.
        Escape: vuelve a la pantalla de bienvenida.
        """
        # Si el usuario presiona Escape vuelvo al main
        if e.key == "Escape":
            ir_a_main()


    # Activo la deteccion de teclado en la pagina
    pagina.on_keyboard_event = teclado

    # Boton para volver al main
    # Navega a la pantalla de bienvenida sin autenticar
    btn_return = ft.Button(
        "Volver",
        bgcolor="gray",
        color="black",
        width=200,
        on_click=lambda e: ir_a_main()
    )

    # ---------------- INTERFAZ ----------------
    # Construyo la interfaz como un Container con estilo de tarjeta (sombra y bordes redondeados)
    # que contiene una Columna centrada con todos los controles apilados verticalmente
    pagina.add(
        ft.Container(
            content=ft.Column(
                [
                    logo,                                      # Logo del SENA arriba
                    ft.Text("Sistema de Punto de Venta", size=22, weight="bold"),  # Título
                    ft.Text("Inicio de sesión"),               # Subtítulo
                    usuario,                                    # Campo de usuario
                    password,                                   # Campo de contraseña
                    btn_login,                                  # Botón de ingreso
                    btn_return,                                 # Botón de retorno
                    mensaje                                     # Mensaje de éxito/error
                ],
                alignment=ft.MainAxisAlignment.CENTER,         # Centrado vertical
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,  # Centrado horizontal
                spacing=15                                     # Espacio entre elementos
            ),
            padding=30,                                        # Relleno interior
            border_radius=15,                                  # Bordes redondeados
            bgcolor=ft.Colors.WHITE,                           # Fondo blanco
            shadow=ft.BoxShadow(                               # Sombra para efecto tarjeta
                blur_radius=12,
                spread_radius=2,
                color=ft.Colors.BLACK_12
            )
        )
    )
