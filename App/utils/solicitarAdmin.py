import flet as ft

from models.loginModel import verificar_password_admin

# ============================================================================
# MÓDULO DE SOLICITUD DE CONTRASEÑA DE ADMINISTRADOR
# ============================================================================
# Muestra un diálogo modal que pide la contraseña de un administrador antes de
# permitir el acceso a una función restringida (por ejemplo, cuando un Aprendiz
# quiere entrar a Entradas, Nuevo Usuario o Actualizar Facturas).
#
# Si la contraseña coincide con la de algún administrador, el diálogo se cierra
# y se notifica al callback con True. Si el usuario cancela (Escape o botón),
# se notifica con False. Si la contraseña es incorrecta, se muestra el error y
# el diálogo permanece abierto para reintentar.
#
# Uso típico (desde el menú principal):
#   dialogo = solicitar_password_admin(pagina, mi_callback)
#   pagina.overlay.append(dialogo)
#   dialogo.open = True
#   pagina.update()
# ============================================================================


def solicitar_password_admin(pagina: ft.Page, callback):
    """
    Crea un diálogo modal que solicita la contraseña de un administrador.

    Parámetros:
        pagina (ft.Page): Página de Flet donde se mostrará el diálogo.
        callback (callable): Función que se ejecuta al terminar. Recibe un bool:
            True si la contraseña fue correcta, False si el usuario canceló.

    Retorna:
        ft.AlertDialog: Componente de diálogo listo para mostrarse.
    """
    # Guardo el handler de teclado actual para restaurarlo al cerrar
    teclado_anterior = pagina.on_keyboard_event
    dialogo_cerrado = False

    def cerrar_dialogo():
        """Cierra el diálogo y restaura el teclado anterior."""
        nonlocal dialogo_cerrado
        if dialogo_cerrado:
            return
        dialogo_cerrado = True
        dialog.open = False
        # Solo restauro si el teclado sigue siendo el de este diálogo
        if pagina.on_keyboard_event == teclado_pagina:
            pagina.on_keyboard_event = teclado_anterior
        pagina.update()

    def validar(e=None):
        """Valida la contraseña y, si es de un admin, autoriza el acceso."""
        # Evito que Enter dispare la validación dos veces (campo + teclado)
        if dialogo_cerrado:
            return

        # Comparo la contraseña contra la de cualquier administrador
        if verificar_password_admin(campo_password.value):
            cerrar_dialogo()
            callback(True)   # ← autorizado
        else:
            # Contraseña incorrecta: muestro error y dejo reintentar
            mensaje.value = "Contraseña de administrador incorrecta."
            mensaje.color = ft.Colors.RED
            campo_password.value = ""
            pagina.update()

    def cancelar(e=None):
        """Cierra el diálogo y notifica que el usuario canceló."""
        if dialogo_cerrado:
            return
        cerrar_dialogo()
        callback(False)  # ← canceló

    async def teclado(e: ft.KeyboardEvent):
        """Maneja las teclas Escape y Enter del diálogo."""
        if e.key == "Escape":
            cancelar()
        elif e.key == "Enter":
            validar()

    async def teclado_pagina(e: ft.KeyboardEvent):
        """Wrapper del handler de teclado para la página."""
        await teclado(e)

    # Campo donde se escribe la contraseña del administrador
    campo_password = ft.TextField(
        label="Contraseña de administrador",
        password=True,
        can_reveal_password=True,
        width=300,
        autofocus=True,
        on_submit=validar
    )

    # Texto para mostrar el mensaje de error si la contraseña es incorrecta
    mensaje = ft.Text("", size=12)

    # Construyo el diálogo modal con el aviso, el campo y los botones
    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Acceso restringido", weight="bold"),
        content=ft.Column(
            [
                ft.Text("Esta opción está reservada a administradores.", size=13),
                ft.Text("Ingrese la contraseña de un administrador para continuar.", size=13),
                campo_password,
                mensaje
            ],
            width=320,
            height=160,
            spacing=10
        ),
        actions=[
            ft.TextButton("Cancelar [Esc]", on_click=cancelar),
            ft.Button(
                "Aceptar [Enter]",
                bgcolor=ft.Colors.GREEN,
                color=ft.Colors.WHITE,
                on_click=validar
            )
        ],
        actions_alignment=ft.MainAxisAlignment.END
    )

    # Reemplazo el teclado temporalmente para que Escape y Enter funcionen
    pagina.on_keyboard_event = teclado_pagina
    return dialog
