"""
Vista de bienvenida / pantalla de inicio del sistema POS.

Es la primera pantalla que ve el usuario al abrir la aplicación.
Muestra dos botones principales:
  - "SenaEmpresa": navega al formulario de login.
  - "Soporte": abre un diálogo modal con opciones para descargar manuales
    (manual de usuario y manual técnico) desde la carpeta /docs del proyecto.

El selector de archivos (FilePicker) se usa internamente para guardar los
manuales descargados en una ubicación elegida por el usuario.

Atajos de teclado:
    ArrowDown -> Mueve la selección al siguiente botón.
    ArrowUp   -> Mueve la selección al botón anterior.

Navegación:
    ir_a_login() -> Navega al formulario de login (login_view).
"""

import flet as ft
from pathlib import Path

# Vista inicial del sistema antes de entrar al menú principal.
# Vista inicial del sistema
def inicio_view(pagina: ft.Page, ir_a_login):
    """
    Renderiza la pantalla de bienvenida con opciones de ingreso y soporte.

    Parámetros:
        pagina     -> Instancia de la página Flet.
        ir_a_login -> Callback para navegar al formulario de login.
    """

    # Ruta a la carpeta 'docs' del proyecto (un nivel arriba de views/)
    carpeta_docs = Path(__file__).resolve().parents[1] / "docs"

    # FilePicker: servicio de Flet para abrir diálogos de guardado/carga de archivos
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

    # Guarda qué botón está seleccionado (índice en el array 'botones')
    # Se usa para la navegación con teclado (flechas arriba/abajo)
    index = 0

    # ---------------- FUNCIONES ----------------

    # Navega al login cuando el usuario hace clic en "SenaEmpresa"
    def SenaEmpresa(e):
        ir_a_login()

    def mostrar_mensaje(mensaje, color=None):
        """
        Muestra un SnackBar (notificación temporal) en la parte inferior de la pantalla.
        Se usa para informar sobre el resultado de descargas de archivos.
        """
        snack = ft.SnackBar(content=ft.Text(mensaje), bgcolor=color)
        pagina.overlay.append(snack)
        snack.open = True
        pagina.update()

    async def descargar_manual(nombre_archivo, titulo, e=None):
        """
        Descarga un archivo desde la carpeta /docs del proyecto.
        Abre un diálogo de guardado para que el usuario elija dónde guardar.
        Si el archivo no existe en /docs, muestra un mensaje de error.

        Parámetros:
            nombre_archivo -> Nombre del archivo en /docs (ej: "Manual_de_Usuario_Sistema_POS.pdf")
            titulo         -> Título descriptivo para el diálogo de guardado.
        """
        ruta_manual = carpeta_docs / nombre_archivo
        if not ruta_manual.is_file():
            # El archivo no existe en la carpeta docs
            mostrar_mensaje(f"El archivo {nombre_archivo} aún no está disponible.", ft.Colors.RED)
            return

        # Leo el contenido del archivo como bytes
        contenido = ruta_manual.read_bytes()

        # Abro el diálogo de guardado del sistema operativo
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
        """
        Abre un diálogo modal con opciones para descargar los manuales del sistema.
        Cada opción cierra el diálogo y lanza la descarga del archivo correspondiente.
        """
        def cerrar_ayuda(e=None):
            """Cierra el diálogo de ayuda sin hacer nada más."""
            dialogo_ayuda.open = False
            pagina.update()

        async def descargar_usuario(e=None):
            """Descarga el manual de usuario y cierra el diálogo."""
            dialogo_ayuda.open = False
            pagina.update()
            await descargar_manual("Manual_de_Usuario_Sistema_POS.pdf", "Manual de usuario")

        async def descargar_tecnico(e=None):
            """Descarga el manual técnico y cierra el diálogo."""
            dialogo_ayuda.open = False
            pagina.update()
            await descargar_manual("Manual_Tecnico.pdf", "Manual técnico")

        # Construyo el diálogo modal con título, contenido y botón de cerrar
        dialogo_ayuda = ft.AlertDialog(
            modal=True,                          # Bloquea interacción con el fondo
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
                tight=True,                      # Sin espacios extra
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            actions=[ft.TextButton("Cerrar", on_click=cerrar_ayuda)],
        )
        # El diálogo se agrega al overlay de la página y se abre
        pagina.overlay.append(dialogo_ayuda)
        dialogo_ayuda.open = True
        pagina.update()

    # ---------------- BOTONES ----------------
    # Dos botones principales: ingreso al sistema y soporte/ayuda
    botones = [
        # Botón de ingreso: navega al login
        ft.Button(
            "SenaEmpresa",
            on_click=SenaEmpresa,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                text_style=ft.TextStyle(size=15, weight="bold")
            )
        ),
        # Botón de soporte: abre el diálogo de ayuda con manuales
        ft.Button(
            "Soporte",
            on_click=mostrar_ayuda,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                text_style=ft.TextStyle(size=15, weight="bold")
            )
        )
    ]

    # ---------------- TECLADO ----------------

    # Coloca foco en el botón seleccionado por el índice 'index'
    async def actualizar_focus():
            try:
                await botones[index].focus()
            except:
                pass

    # Detecta teclas para navegar entre botones con flechas
    async def posicion(e: ft.KeyboardEvent):
        nonlocal index
        # Flecha abajo: avanza al siguiente botón (con wrap-around)
        if e.key == "ArrowDown":
            index = (index + 1) % len(botones)
            await actualizar_focus()
        # Flecha arriba: retrocede al botón anterior (con wrap-around)
        elif e.key == "ArrowUp":
            index = (index - 1) % len(botones)
            await actualizar_focus()

    # Activo teclado
    pagina.on_keyboard_event = posicion

    # ---------------- INTERFAZ ----------------
    # Tarjeta centrada con el título del sistema y los dos botones principales
    pagina.add(
        ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Sistema de Punto de Venta",
                        size=22,
                        weight="bold"
                    ),
                    *botones                    # Desempaqueta la lista de botones
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
    # Foco inicial en el primer botón después de renderizar
    pagina.run_task(actualizar_focus)
