import flet as ft

# Vista del menú principal.
# Desde aquí se accede a ventas, compras, remisiones y otras opciones.
# =========================================================
# MENU DE MODULOS
# =========================================================
def menu_view(pagina: ft.Page, ir_a_main, ir_a_vender, ir_a_remision, usuario, ir_a_compras, ir_a_inventario, ir_a_consultar_facturas, ir_a_nuevo_usuario, ir_a_entradas):

    # Limpio la pantalla
    pagina.clean()

    # Centro todo el contenido
    pagina.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    pagina.vertical_alignment = ft.MainAxisAlignment.CENTER

    # Tamaño de la ventana para el menu
    pagina.window.width = 400
    pagina.window.height = 800

    # Variable que guarda que boton esta seleccionado con el teclado
    index = 0

    # ---------------- FUNCIONES ----------------

    # Por ahora solo imprimo en consola, luego conectare cada vista
    def ventas(e):
        ir_a_vender(usuario)

    def compras(e):
        ir_a_compras(usuario)

    def abrir_remision(e):
        ir_a_remision(usuario)

    def abrir_inventario(e):
        ir_a_inventario(usuario)

    def abrir_entradas(e):
        ir_a_entradas(usuario)

    def abrir_nuevo_usuario(e):
        ir_a_nuevo_usuario(usuario)

    def consultar_facturas(e):
        ir_a_consultar_facturas(usuario)
        
    def cerrar_sesion():
        ir_a_main()

    # ---------------- BOTONES ----------------

    # Lista de botones del menu
    botones = [
        ft.Button(
            "📄 Facturacion", 
            on_click=ventas,
            width=250,
            height=40,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                text_style=ft.TextStyle(size=15, weight="bold")
            )
        ),
        ft.Button("🛒 Compras",
                on_click=compras,
                width=250,
                height=40,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=10),
                    text_style=ft.TextStyle(size=15, weight="bold")
                )
                ),
        ft.Button("♻️ Remision",
                on_click=abrir_remision,
                width=250,
                height=40,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=10),
                    text_style=ft.TextStyle(size=15, weight="bold")
                )),
        ft.Button("📦 Inventario",
                on_click=abrir_inventario,
                width=250,
                height=40,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=10),
                    text_style=ft.TextStyle(size=15, weight="bold")
                )),
        ft.Button("➕ Entradas",
                on_click=abrir_entradas,
                width=250,
                height=40,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=10),
                    text_style=ft.TextStyle(size=15, weight="bold")
                )),
        ft.Button("👤 Nuevo Usuario",
                on_click=abrir_nuevo_usuario,
                width=250,
                height=40,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=10),
                    text_style=ft.TextStyle(size=15, weight="bold")
            )),
        ft.Button("🔍 Consultar Facturas", 
                on_click=consultar_facturas,
                width=250,
                height=40,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=10),
                    text_style=ft.TextStyle(size=15, weight="bold")
                )),
        ft.Button("🚪 Cerrar sesión",
                on_click=cerrar_sesion, width=250, height=40,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=10),
                    text_style=ft.TextStyle(size=15, weight="bold")
                ))
    ]


    # validacion de rol para los botones de menu
    if usuario.get("rol", "") != "Admin":
        botones[5].disabled = True  # Nuevo Usuario
        botones[4].disabled = True  # Entradas

    if usuario.get("rol", "") == "Consultas":
        botones[0].disabled = True  # Facturacion
        botones[1].disabled = True  # Compras
        botones[2].disabled = True  # Remision
        botones[3].disabled = True  # Inventario
        botones[4].disabled = True  # Entradas
        botones[5].disabled = True  # Nuevo Usuario

    # ---------------- TECLADO ----------------

    # Coloco el foco en el boton seleccionado
    async def actualizar_focus():
            try:
                await botones[index].focus()
            except:
                pass

    # Detecto cuando el usuario presiona una tecla
    async def posicion(e: ft.KeyboardEvent):
        nonlocal index

        # Flecha abajo mueve al siguiente boton
        if e.key == "ArrowDown":
            index = (index + 1) % len(botones)
            await actualizar_focus()

        # Flecha arriba mueve al boton anterior
        elif e.key == "ArrowUp":
            index = (index - 1) % len(botones)
            await actualizar_focus()
        elif e.key == "Escape":
            cerrar_sesion()

    # Activo la deteccion de teclado en la pagina
    pagina.on_keyboard_event = posicion

    # ---------------- INTERFAZ ----------------

    pagina.add(
        ft.Container(
            content=ft.Column(
                [
                    ft.Text("Menú Principal", size=28, weight="bold"),
                    ft.Text("Seleccione una opción"),
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

    # Coloco el foco inicial en el primer boton
    pagina.run_task(actualizar_focus)
