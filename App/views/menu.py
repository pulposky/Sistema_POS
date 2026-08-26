"""
Vista del menú principal del sistema POS.

Muestra una lista vertical de botones que permiten acceder a todos los módulos:
Facturación, Compras, Remisiones, Inventario, Entradas, Nuevo Usuario,
Consultar Facturas, Actualizar Facturas y Cerrar Sesión.

La visibilidad de los botones se controla según el rol del usuario:
  - Admin / Administrador: acceso total.
  - Consultas: solo puede ver facturas (botón de consulta deshabilitado en menú,
    pero se accede desde aquí si tiene permiso; todos los demás deshabilitados).
  - Cualquier otro rol: no puede crear usuarios, registrar entradas ni actualizar facturas.

Atajos de teclado:
    ArrowDown  -> Mueve la selección al siguiente botón.
    ArrowUp    -> Mueve la selección al botón anterior.
    Escape     -> Cierra sesión y vuelve a la pantalla de bienvenida.

Navegación:
    Cada botón invoca un callback que navega a la vista correspondiente,
    pasando siempre el diccionario del usuario actual.
"""

import flet as ft

# Vista del menú principal.
# Desde aquí se accede a ventas, compras, remisiones y otras opciones.
# =========================================================
# MENU DE MODULOS
# =========================================================
def menu_view(pagina: ft.Page, ir_a_main, ir_a_vender, ir_a_remision, usuario, ir_a_compras, ir_a_inventario, ir_a_consultar_facturas, ir_a_nuevo_usuario, ir_a_entradas, ir_a_actualizar_facturas):
    """
    Renderiza el menú principal con navegación por teclado.

    Parámetros:
        pagina                   -> Instancia de la página Flet.
        ir_a_main                -> Callback para cerrar sesión (volver al inicio).
        ir_a_vender              -> Callback para abrir el módulo de facturación/ventas.
        ir_a_remision            -> Callback para abrir el módulo de remisiones.
        usuario                  -> Diccionario con los datos del usuario logueado.
        ir_a_compras             -> Callback para abrir el módulo de compras.
        ir_a_inventario          -> Callback para abrir el módulo de inventario.
        ir_a_consultar_facturas  -> Callback para abrir la consulta de facturas.
        ir_a_nuevo_usuario       -> Callback para abrir la creación de usuarios.
        ir_a_entradas            -> Callback para abrir el registro de entradas.
        ir_a_actualizar_facturas -> Callback para abrir la actualización de facturas.
    """

    # Limpio la pantalla
    pagina.clean()

    # Centro todo el contenido
    pagina.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    pagina.vertical_alignment = ft.MainAxisAlignment.CENTER

    # Tamaño de la ventana para el menu
    pagina.window.width = 400
    pagina.window.height = 800

    # Variable que guarda que boton esta seleccionado con el teclado
    # Se usa como índice del array 'botones' para el navegación con flechas
    index = 0

    # ---------------- FUNCIONES ----------------

    # Por ahora solo imprimo en consola, luego conectare cada vista

    # Cada función envía el usuario logueado a la vista correspondiente
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

    def actualizar_facturas(e):
        ir_a_actualizar_facturas(usuario)
        
    def cerrar_sesion():
        """Vuelve a la pantalla de bienvenida (inicio_view) limpiando la sesión."""
        ir_a_main()

    # ---------------- BOTONES ----------------

    # Lista de botones del menu
    # Cada botón tiene un ícono emoji, un handler de clic y estilo uniforme
    botones = [
        # [0] Facturación -> abre el módulo de ventas/facturación
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
        # [1] Compras -> abre el módulo de compras
        ft.Button("🛒 Compras",
                on_click=compras,
                width=250,
                height=40,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=10),
                    text_style=ft.TextStyle(size=15, weight="bold")
                )
                ),
        # [2] Remisiones -> abre el módulo de remisiones
        ft.Button("♻️ Remision",
                on_click=abrir_remision,
                width=250,
                height=40,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=10),
                    text_style=ft.TextStyle(size=15, weight="bold")
                )),
        # [3] Inventario -> abre el informe de inventario
        ft.Button("📦 Inventario",
                on_click=abrir_inventario,
                width=250,
                height=40,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=10),
                    text_style=ft.TextStyle(size=15, weight="bold")
                )),
        # [4] Entradas -> registro de entradas de inventario (solo admin)
        ft.Button("➕ Entradas",
                on_click=abrir_entradas,
                width=250,
                height=40,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=10),
                    text_style=ft.TextStyle(size=15, weight="bold")
                )),
        # [5] Nuevo Usuario -> crear usuarios (solo admin)
        ft.Button("👤 Nuevo Usuario",
                on_click=abrir_nuevo_usuario,
                width=250,
                height=40,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=10),
                    text_style=ft.TextStyle(size=15, weight="bold")
            )),
        # [6] Consultar Facturas -> vista de consulta con filtros
        ft.Button("🔍 Consultar Facturas", 
                on_click=consultar_facturas,
                width=250,
                height=40,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=10),
                    text_style=ft.TextStyle(size=15, weight="bold")
                )),
        # [7] Actualizar Facturas -> modificar documentos existentes (solo admin)
        ft.Button("✏️ Actualizar Facturas",
                on_click=actualizar_facturas,
                width=250,
                height=40,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=10),
                    text_style=ft.TextStyle(size=15, weight="bold")
                )),
        # [8] Cerrar sesión -> vuelve a la pantalla de bienvenida
        ft.Button("🚪 Cerrar sesión",
                on_click=cerrar_sesion, width=250, height=40,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=10),
                    text_style=ft.TextStyle(size=15, weight="bold")
                ))
    ]


    # validacion de rol para los botones de menu
    # Si el usuario NO es admin ni administrador, deshabilito funciones restringidas:
    #   - Nuevo Usuario [5]
    #   - Entradas [4]
    #   - Actualizar Facturas [7]
    if usuario.get("rol", "") not in {"Admin", "Administrador"}:
        botones[5].disabled = True  # Nuevo Usuario
        botones[4].disabled = True  # Entradas
        botones[7].disabled = True  # Actualizar Facturas

    # Si el rol es "Consultas", solo puede ver facturas; todo lo demás se deshabilita
    if usuario.get("rol", "") == "Consultas":
        botones[0].disabled = True  # Facturacion
        botones[1].disabled = True  # Compras
        botones[2].disabled = True  # Remision
        botones[3].disabled = True  # Inventario
        botones[4].disabled = True  # Entradas
        botones[5].disabled = True  # Nuevo Usuario
        botones[7].disabled = True  # Actualizar Facturas

    # ---------------- TECLADO ----------------

    # Coloco el foco en el boton seleccionado
    # Se usa try/except porque puede fallar si el botón fue deshabilitado
    async def actualizar_focus():
            try:
                await botones[index].focus()
            except:
                pass

    # Detecto cuando el usuario presiona una tecla
    async def posicion(e: ft.KeyboardEvent):
        """
        Navegación con teclado entre los botones del menú.
        ArrowDown/ArrowUp mueven la selección cíclicamente.
        Escape cierra sesión.
        """
        nonlocal index

        # Flecha abajo mueve al siguiente boton (con wrap-around al final)
        if e.key == "ArrowDown":
            index = (index + 1) % len(botones)
            await actualizar_focus()

        # Flecha arriba mueve al boton anterior (con wrap-around al inicio)
        elif e.key == "ArrowUp":
            index = (index - 1) % len(botones)
            await actualizar_focus()
        elif e.key == "Escape":
            # Escape cierra sesión y vuelve a la pantalla de bienvenida
            cerrar_sesion()

    # Activo la deteccion de teclado en la pagina
    pagina.on_keyboard_event = posicion

    # ---------------- INTERFAZ ----------------

    # Construyo la interfaz: un Container con tarjeta blanca que contiene
    # el título, subtítulo y todos los botones del menú desplegados verticalmente
    # El *botones desempaqueta la lista para agregar cada botón como hijo de la Column
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
    # Se usa run_task porque actualizar_focus es async y necesita ejecutarse
    # después de que la interfaz se haya renderizado completamente
    pagina.run_task(actualizar_focus)
