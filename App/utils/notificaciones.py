import flet as ft

# ============================================================================
# MÓDULO DE NOTIFICACIONES SNACKBAR
# ============================================================================
# Proporciona una función auxiliar para mostrar notificaciones breves
# (SnackBars) en cualquier vista de la aplicación Flet.
# Se usa para confirmar acciones como creación, edición o eliminación
# de registros en el sistema POS.
# ============================================================================


def mostrar_notificacion(pagina, mensaje, error=False):
    """
    Muestra una notificación breve tipo SnackBar en la parte inferior
    de la pantalla.

    Parámetros:
        pagina (ft.Page): Página de Flet donde se mostrará la notificación.
        mensaje (str): Texto que se mostrará en la notificación.
        error (bool): Si es True, el fondo es rojo (para errores).
                      Si es False, el fondo es verde (para confirmaciones).

    La notificación se cierra automáticamente después de 3.5 segundos.
    """
    snack = ft.SnackBar(
        content=ft.Text(mensaje),
        bgcolor=ft.Colors.RED if error else ft.Colors.GREEN,
        duration=3500,
    )
    # Se agrega al overlay de la página para que aparezca encima de todo
    pagina.overlay.append(snack)
    snack.open = True
    pagina.update()
