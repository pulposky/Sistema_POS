import flet as ft


def mostrar_notificacion(pagina, mensaje, error=False):
    """Muestra un aviso breve y uniforme en cualquier vista de Flet."""
    snack = ft.SnackBar(
        content=ft.Text(mensaje),
        bgcolor=ft.Colors.RED if error else ft.Colors.GREEN,
        duration=3500,
    )
    pagina.overlay.append(snack)
    snack.open = True
    pagina.update()
