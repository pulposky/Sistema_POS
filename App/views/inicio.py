import flet as ft

# Vista inicial del sistema antes de entrar al menú principal.
# Vista inicial del sistema
def inicio_view(pagina: ft.Page, ir_a_login):

    # Limpio la pantalla
    pagina.clean()

    # Configuración ventana
    pagina.window.width = 400
    pagina.window.height = 600  

    # Centro contenido
    pagina.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    pagina.vertical_alignment = ft.MainAxisAlignment.CENTER

    # Guarda qué botón está seleccionado
    index = 0
    # ---------------- FUNCIONES ----------------
    # Navega al login
    def SenaEmpresa(e):
        ir_a_login()

    # ---------------- BOTONES ----------------
    botones = [
        ft.Button(
            "SenaEmpresa",
            on_click=SenaEmpresa,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                text_style=ft.TextStyle(size=15, weight="bold")
            )
        ),
        ft.Button(
            "Eventos",
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                text_style=ft.TextStyle(size=15, weight="bold")
            )
        )
    ]
    # ---------------- TECLADO ----------------

    # Coloca foco en el botón seleccionado
    async def actualizar_focus():
            try:
                await botones[index].focus()
            except:
                pass
    # Detecta teclas
    async def posicion(e: ft.KeyboardEvent):
        nonlocal index
        # Flecha abajo
        if e.key == "ArrowDown":
            index = (index + 1) % len(botones)
            await actualizar_focus()
        # Flecha arriba
        elif e.key == "ArrowUp":
            index = (index - 1) % len(botones)
            await actualizar_focus()
        # Enter
        elif e.key == "Enter":
            if botones[index].on_click:
                botones[index].on_click(e)

    # Activo teclado
    pagina.on_keyboard_event = posicion

    # ---------------- INTERFAZ ----------------
    pagina.add(
        ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Sistema de Punto de Venta",
                        size=22,
                        weight="bold"
                    ),
                    *botones
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
    pagina.run_task(actualizar_focus)