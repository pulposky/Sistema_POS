import flet as ft

def confirmar_view(pagina: ft.Page, mensaje, callback):

    teclado_anterior = pagina.on_keyboard_event
    dialogo_cerrado = False

    def cerrar_dialogo():
        nonlocal dialogo_cerrado
        if dialogo_cerrado:
            return
        dialogo_cerrado = True
        dialog.open = False
        if pagina.on_keyboard_event == teclado_pagina:
            pagina.on_keyboard_event = teclado_anterior
        pagina.update()

    def confirmar(e=None):
        cerrar_dialogo()
        callback(True)   # ← confirmó

    def cancelar(e=None):
        cerrar_dialogo()
        callback(False)  # ← canceló

    async def teclado(e: ft.KeyboardEvent):
        if e.key == "Escape":
            cancelar()
        elif e.key == "Enter":
            confirmar()

    async def teclado_pagina(e: ft.KeyboardEvent):
        await teclado(e)

    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Confirmar", weight="bold"),
        content=ft.Text(mensaje, size=16),
        actions=[
            ft.TextButton("Cancelar [Esc]", on_click=cancelar),
            ft.Button(
                "Confirmar [Enter]",
                bgcolor=ft.Colors.RED,
                color=ft.Colors.WHITE,
                on_click=confirmar
            )
        ],
        actions_alignment=ft.MainAxisAlignment.END
    )

    pagina.on_keyboard_event = teclado_pagina
    return dialog