import flet as ft
from pathlib import Path

# Vista inicial del sistema antes de entrar al menú principal.
# Vista inicial del sistema
def inicio_view(pagina: ft.Page, ir_a_login):

    carpeta_docs = Path(__file__).resolve().parents[1] / "docs"
    selector_archivos = ft.FilePicker()
    pagina.services.append(selector_archivos)

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

    def mostrar_mensaje(mensaje, color=None):
        snack = ft.SnackBar(content=ft.Text(mensaje), bgcolor=color)
        pagina.overlay.append(snack)
        snack.open = True
        pagina.update()

    async def descargar_manual(nombre_archivo, titulo, e=None):
        ruta_manual = carpeta_docs / nombre_archivo
        if not ruta_manual.is_file():
            mostrar_mensaje(f"El archivo {nombre_archivo} aún no está disponible.", ft.Colors.RED)
            return

        contenido = ruta_manual.read_bytes()
        destino = await selector_archivos.save_file(
            dialog_title=f"Guardar {titulo}",
            file_name=nombre_archivo,
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["txt"],
            src_bytes=contenido,
        )

        # En escritorio Flet devuelve la ruta seleccionada, por lo que se guarda
        # el contenido allí. En web, src_bytes realiza la descarga directamente.
        if destino:
            Path(destino).write_bytes(contenido)
            mostrar_mensaje(f"{titulo} descargado correctamente.", ft.Colors.GREEN)

    # Muestra las opciones de ayuda disponibles.
    def mostrar_ayuda(e=None):
        def cerrar_ayuda(e=None):
            dialogo_ayuda.open = False
            pagina.update()

        async def descargar_usuario(e=None):
            dialogo_ayuda.open = False
            pagina.update()
            await descargar_manual("Manual.txt", "Manual de usuario")

        async def descargar_tecnico(e=None):
            dialogo_ayuda.open = False
            pagina.update()
            await descargar_manual("ManualTecnico.txt", "Manual técnico")

        dialogo_ayuda = ft.AlertDialog(
            modal=True,
            title=ft.Text("Ayuda", weight="bold"),
            content=ft.Column(
                [
                    ft.Text("Selecciona el manual que deseas consultar."),
                    ft.Button(
                        "Manual de usuario",
                        on_click=descargar_usuario,
                    ),
                    ft.Button(
                        "Manual técnico",
                        on_click=descargar_tecnico,
                    ),
                ],
                tight=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            actions=[ft.TextButton("Cerrar", on_click=cerrar_ayuda)],
        )
        pagina.overlay.append(dialogo_ayuda)
        dialogo_ayuda.open = True
        pagina.update()

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
            "Ayuda",
            on_click=mostrar_ayuda,
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
