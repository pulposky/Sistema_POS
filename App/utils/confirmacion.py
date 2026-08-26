import flet as ft

# ============================================================================
# MÓDULO DE DIÁLOGO DE CONFIRMACIÓN GENÉRICO
# ============================================================================
# Muestra un diálogo modal de confirmación antes de ejecutar acciones
# destructivas como borrar, anular o eliminar registros.
#
# El usuario puede confirmar (Enter) o cancelar (Escape). El resultado
# se comunica al callback como True (confirmó) o False (canceló).
#
# Uso típico:
#   dialog = confirmar_view(pagina, "¿Estás seguro de borrar?", mi_callback)
#   pagina.overlay.append(dialog)
#   dialog.open = True
#   pagina.update()
# ============================================================================


def confirmar_view(pagina: ft.Page, mensaje, callback):
    """
    Crea un diálogo modal de confirmación.

    Parámetros:
        pagina (ft.Page): Página de Flet donde se mostrará el diálogo.
        mensaje (str): Mensaje de texto que se mostrará como pregunta
            de confirmación (ej. "¿Desea anular la factura #0042?").
        callback (callable): Función que se ejecutará al confirmar o cancelar.
            Recibe un bool: True si confirmó, False si canceló.

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

    def confirmar(e=None):
        """Cierra el diálogo y notifica que el usuario confirmó."""
        cerrar_dialogo()
        callback(True)   # ← confirmó

    def cancelar(e=None):
        """Cierra el diálogo y notifica que el usuario canceló."""
        cerrar_dialogo()
        callback(False)  # ← canceló

    async def teclado(e: ft.KeyboardEvent):
        """Maneja las teclas Escape y Enter del diálogo."""
        if e.key == "Escape":
            cancelar()
        elif e.key == "Enter":
            confirmar()

    async def teclado_pagina(e: ft.KeyboardEvent):
        """Wrapper del handler de teclado para la página."""
        await teclado(e)

    # Construyo el diálogo modal con botones de confirmar y cancelar
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

    # Reemplazo el teclado temporalmente para que Escape y Enter funcionen
    pagina.on_keyboard_event = teclado_pagina
    return dialog
