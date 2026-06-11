import flet as ft
from datetime import datetime
import asyncio
from utils.buscarProducto import buscar_producto_view
from utils.buscarCliente import buscar_cliente_view
from controllers import ventasController as ventas_controller
from utils.metodoPago import metodo_pago_view
from utils.crearP_C import Crear
from utils.confirmacion import confirmar_view


# =========================================================
# VISTA PRINCIPAL PARA BUSCAR Y REALIZAR VENTAS
# =========================================================

def vender(pagina: ft.Page, ir_a_main, ir_a_menu, usuario):
#------------------- DATOS -----------------

    # Lista donde se guardan los productos agregados a la venta
    productos = []
    print (f"Usuario en vender: {usuario}")
    # Cliente seleccionado actualmente
    cliente_actual = None

    # Variables para navegación de facturas guardadas
    facturas = []
    index_factura = -1
    modo_consulta = False
    id_factura_actual = None
#-------------------------------------------

    # Limpio la consola y la pantalla
    pagina.clean()

    # Tamaño de la ventana para el login
    pagina.window.width = 1400
    pagina.window.height = 800

    # Centro todo el contenido
    pagina.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    pagina.vertical_alignment = ft.MainAxisAlignment.CENTER

    # ---------------- CAMPOS ----------------

    logo = ft.Image(
        src="assets/Logo_sena.png",
        width=50,
        height=50
    )

    titulo = ft.Text("Sistema POS", size=15, weight="bold")

    subtotal  = ft.Text("Subtotal: $0",  weight="bold")
    descuento = ft.Text("Descuento: $0", weight="bold")
    total     = ft.Text("Total: $0",     weight="bold")

    fecha_hora  = ft.Text("", size=15)
    nombreCliente = ft.TextField(label="Cliente seleccionado ", width=260, read_only=True)
    texto_usuario = ft.Text(f"Usuario: {usuario['usuario']}", size=15, weight="bold")
    texto_nombre  = ft.Text(f"Nombre: {usuario['nombre']}",  size=15, weight="bold")

    numeroFactura = ft.Text("Número de factura: 0001", size=17, weight="bold")
    texto_fecha = ft.Text("", size=13, weight="bold", visible=False)
    usuarioFactura = ft.Text("", size=13, weight="bold", visible=False)

    # ---------------- FUNCIONES ----------------

    # Actualizo subtotal, descuento y total segun los productos agregados
    def actualizar_totales():

        subtotal_total = ventas_controller.calcular_total(productos)
        descuento_valor = 0
        total_valor = subtotal_total - descuento_valor

        subtotal.value = f"Subtotal: ${subtotal_total:,.2f}"
        descuento.value = f"Descuento: ${descuento_valor:,.2f}"
        total.value = f"Total: ${total_valor:,.2f}"
        pagina.update()

    def editar_cantidad(index):

        if modo_consulta and usuario.get("rol", "") == "Aprendiz":
            return

        producto = productos[index]
        campo = ft.TextField(
            value=str(producto["cantidad"]),
            autofocus=True,
            width=120
        )
        def guardar(e):
            try:
                nueva_cantidad = float(campo.value)
                producto["cantidad"] = nueva_cantidad
                producto["subtotal"] = (
                    nueva_cantidad * float(producto["precio"])
                )
                tabla_productos.rows[index].cells[2] = ft.DataCell(
                    ft.TextButton(
                        content=ft.Text(
                            ventas_controller.formatear_cantidad(
                                nueva_cantidad
                            )
                        ),
                        on_click=lambda e: editar_cantidad(index)
                    )
                )
                tabla_productos.rows[index].cells[5] = ft.DataCell(
                    ft.Text(
                        f"${producto['subtotal']:,.2f}"
                    )
                )
                tabla_productos.rows[index].cells[7] = crear_celda_acciones(
                    producto,
                    index
                )
                actualizar_totales()
                pagina.update()

            except:
                pass
        tabla_productos.rows[index].cells[2] = ft.DataCell(campo)
        campo.on_submit = guardar
        pagina.update()

    def obtener_stock_restante(producto):
        try:
            return float(producto.get("stock", 0)) - float(producto.get("cantidad", 0))
        except (TypeError, ValueError):
            return 0

    def formatear_stock(stock):
        if isinstance(stock, float) and stock.is_integer():
            return str(int(stock))
        return str(stock)

    def crear_celda_acciones(producto, index, deshabilitado=False):
        stock_restante = obtener_stock_restante(producto)
        controles = []

        if stock_restante < 0:
            controles.append(
                ft.Text(
                    formatear_stock(stock_restante),
                    color=ft.Colors.RED,
                    weight="bold",
                    size=12
                )
            )

        controles.append(
            ft.IconButton(
                icon=ft.Icons.CLOSE,
                icon_color=ft.Colors.RED,
                on_click=lambda e, idx=index: eliminar_producto(idx),
                disabled=deshabilitado
            )
        )

        return ft.DataCell(
            ft.Row(
                controles,
                spacing=4,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            )
        )


    def eliminar_producto(index):

        if modo_consulta:
            return

        productos.pop(index)

        tabla_productos.rows.clear()

        for i, p in enumerate(productos):

            cantidad_texto = ventas_controller.formatear_cantidad(
                p["cantidad"]
            )

            tabla_productos.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(
                            ft.Text(str(p.get("id", "-")))
                        ),

                        ft.DataCell(
                            ft.Text(p.get("nombre", "Sin nombre"))
                        ),

                        ft.DataCell(
                            ft.TextButton(
                                content=ft.Text(cantidad_texto),
                                on_click=lambda e, idx=i: editar_cantidad(idx)
                            )
                        ),

                        ft.DataCell(
                            ft.Text(str(p.get("unidad", "UND")))
                        ),

                        ft.DataCell(
                            ft.Text(f"${p.get('precio', 0):,.2f}")
                        ),

                        ft.DataCell(
                            ft.Text(f"${p.get('subtotal', 0):,.2f}")
                        ),

                        ft.DataCell(
                            ft.Text(str(p.get('lugar', '-')))
                        ),

                        # BOTON X
                        crear_celda_acciones(p, i)
                    ]
                )
            )

        actualizar_totales()

        pagina.update()

    # Agrego el producto seleccionado en el buscador a la tabla de la venta
    # Agrego el producto seleccionado en la tabla
    def agregar_producto_a_tabla(producto):

        if modo_consulta:
            return

        # Obtengo el stock actual del producto
        stock_actual = producto.get("stock", 0)

        # Cantidad que el usuario quiere agregar
        cantidad = producto.get("cantidad", 1)

        # ---------------------------------------------
        # LO AGREGO NORMAL
        # ---------------------------------------------

        producto["subtotal"] = (
            float(producto["cantidad"]) * float(producto["precio"])
        )
        productos.append(producto)
        cantidad_texto = ventas_controller.formatear_cantidad(
            cantidad
        )
        tabla_productos.rows.append(
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(str(producto.get('id', '-')))),
                    ft.DataCell(ft.Text(producto.get('nombre', 'Sin nombre'))),
                    ft.DataCell(
                    ft.TextButton(
                        content=ft.Text(cantidad_texto),
                        on_click=lambda e, idx=len(productos): editar_cantidad(idx - 1)
                    )
                ),
                    ft.DataCell(ft.Text(str(producto.get('unidad', 'UND')))),
                    ft.DataCell(ft.Text(f"${producto.get('precio', 0):,.2f}")),
                    ft.DataCell(ft.Text(f"${producto.get('subtotal', 0):,.2f}")),
                    ft.DataCell(ft.Text(str(producto.get('lugar', '-')))),
                    crear_celda_acciones(producto, len(productos)-1)
                ]
            )
        )

        actualizar_totales()
        tabla_productos.update()

    # Mantengo la fecha y hora actualizadas en pantalla
    async def actualizar_hora():

        # Ciclo infinito mientras la vista siga activa
        while True:
            try:
                # Si el texto todavia no esta en la pagina espero un momento
                if fecha_hora.page is None:
                    await asyncio.sleep(0.1)
                    continue
            except RuntimeError:
                await asyncio.sleep(0.1)
                continue
            try:
                # Coloco la fecha y hora actual
                fecha_hora.value = datetime.now().strftime("%d/%m/%Y %I:%M:%S %p")
                fecha_hora.update()
            except RuntimeError:
                # Si la vista ya no existe corto el ciclo
                break
            await asyncio.sleep(1)

    def confirmar_factura(pago):
        resultado = ventas_controller.confirmar_factura(
            pago=pago,
            productos=productos,
            cliente=cliente_actual,
            usuario=usuario
        )

        if not resultado:
            print("Error al guardar la factura")
            return

        print(f"Factura {resultado['id_factura']} guardada")
        print(f"PDF: {resultado['ruta_pdf']}")
        limpiar_factura()

    # ---------------- FACTURAR ----------------

    def facturar():

        if modo_consulta and usuario.get("rol", "").lower() != "admin":
            print("No se puede facturar en modo consulta")
            return
        if not productos:
            print("No hay productos en la factura")
            return

        total_valor = ventas_controller.calcular_total(productos)

        # Crear dialogo
        dialog = metodo_pago_view(
            pagina,
            total_valor,
            confirmar_factura
        )

        # Abrir dialogo
        pagina.overlay.append(dialog)
        dialog.open = True
        pagina.update()

    def limpiar_factura():

        nonlocal productos
        nonlocal modo_consulta
        nonlocal id_factura_actual
        nonlocal cliente_actual

        productos = []
        cliente_actual = None

        tabla_productos.rows.clear()

        nombreCliente.value = ""

        usuarioFactura.value = ""
        usuarioFactura.visible = False
        texto_fecha.value = ""
        texto_fecha.visible = False

        numeroFactura.value = "Número de factura: Nueva"
        numeroFactura.color = ft.Colors.BLACK
        btn_imprimir_consulta.visible = False

        actualizar_totales()

        modo_consulta = False
        id_factura_actual = None

        pagina.update()

    def cargar_factura(id_venta):
        nonlocal productos, modo_consulta, id_factura_actual

        datos = ventas_controller.cargar_factura(id_venta)
        if not datos:
            return False

        cliente = datos["cliente"]
        productos = datos["productos"]
        factura = datos["factura"]
        tabla_productos.rows.clear()
        texto_fecha.value = (
            f"Fecha: {factura['fecha'].strftime('%d/%m/%Y %H:%M:%S')}"
        )
        texto_fecha.visible = True

        for i, producto in enumerate(productos):
            cantidad_texto = ventas_controller.formatear_cantidad(producto["cantidad"])
            tabla_productos.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(str(producto["id"]))),
                    ft.DataCell(ft.Text(producto["nombre"])),
                    ft.DataCell(
                        ft.TextButton(
                            content=ft.Text(cantidad_texto),
                            on_click=lambda e, idx=len(productos): editar_cantidad(idx - 1)
                        )
                    ),
                    ft.DataCell(ft.Text(producto["unidad"])),
                    ft.DataCell(ft.Text(f"${producto['precio']:,.2f}")),
                    ft.DataCell(ft.Text(f"${producto['subtotal']:,.2f}")),
                    ft.DataCell(ft.Text(producto["lugar"])),
                    crear_celda_acciones(producto, i, deshabilitado=True)
                ])
            )

        nombreCliente.value = f"{cliente['nombre']} - {cliente['rol']}" if cliente else "Sin cliente"

        usuarioFactura.value = (
            f"Vendido por: {factura.get('nombre_usuario', 'Sin usuario')}"
        )
        usuarioFactura.visible = True
        if datos["factura"]["estado"] == "ANULADA":

            numeroFactura.value = (
                f"FACTURA ANULADA #{id_venta:04d}"
            )
            numeroFactura.color = ft.Colors.RED
        else:
            numeroFactura.value = (
                f"Número de factura: {id_venta:04d}"
            )
            numeroFactura.color = ft.Colors.BLACK
        actualizar_totales()
        modo_consulta = True
        id_factura_actual = id_venta
        btn_imprimir_consulta.visible = True
        pagina.update()
        return True

    def imprimir_factura_consultada():
        if not modo_consulta or id_factura_actual is None:
            print("Primero consulta una factura para imprimirla")
            return

        ruta_pdf = ventas_controller.imprimir_factura_consultada(
            id_factura_actual,
            usuario
        )
        if not ruta_pdf:
            print("No se pudo imprimir la factura consultada")
            return

        print(f"Factura {id_factura_actual} enviada a imprimir")

    def nueva_factura():
        nonlocal index_factura, modo_consulta
        facturas.clear()
        index_factura = -1
        modo_consulta = False
        limpiar_factura()

    def siguiente_factura():
        nonlocal index_factura
        if not facturas:
            cargar_lista_facturas()
            return
        index_factura = (index_factura + 1) % len(facturas)
        cargar_factura(facturas[index_factura]['id_venta'])

    def anterior_factura():
        nonlocal index_factura
        if not facturas:
            cargar_lista_facturas()
            return
        index_factura = (index_factura - 1) % len(facturas)
        cargar_factura(facturas[index_factura]['id_venta'])

    def cargar_lista_facturas():
        nonlocal facturas, index_factura
        facturas = ventas_controller.listar_facturas()
        if facturas:
            index_factura = 0
            cargar_factura(facturas[0]['id_venta'])
        else:
            limpiar_factura()

    def borrar_factura_actual():
        nonlocal index_factura

        # -----------------------------------
        # MODO NUEVA FACTURA
        # -----------------------------------
        if not modo_consulta:
            mensaje = "¿Deseas limpiar la factura actual?"

            def on_confirmar(confirmado):
                if not confirmado:
                    return
                limpiar_factura()

                snack = ft.SnackBar(
                    content=ft.Text("Factura limpiada"),
                    bgcolor=ft.Colors.BLUE
                )
                pagina.overlay.append(snack)
                snack.open = True
                pagina.update()

        # -----------------------------------
        # MODO CONSULTA
        # -----------------------------------
        else:
            # VALIDAR PERMISOS
            if usuario.get("rol", "") == "Aprendiz":
                snack = ft.SnackBar(
                    content=ft.Text(
                        "No tienes permisos para anular facturas"
                    ),
                    bgcolor=ft.Colors.RED
                )
                pagina.overlay.append(snack)
                snack.open = True
                pagina.update()
                return

            if id_factura_actual is None:
                return

            mensaje = (
                f"¿Deseas anular la factura "
                f"#{id_factura_actual:04d}?"
            )

            def on_confirmar(confirmado):
                nonlocal index_factura

                if not confirmado:
                    return

                if ventas_controller.borrar_factura(
                    id_factura_actual
                ):
                    snack = ft.SnackBar(
                        content=ft.Text("Factura anulada"),
                        bgcolor=ft.Colors.RED
                    )
                    pagina.overlay.append(snack)
                    snack.open = True
                    facturas.clear()
                    index_factura = -1
                    cargar_lista_facturas()

        # -----------------------------------
        # DIALOGO GENERAL
        # -----------------------------------
        dialog = confirmar_view(
            pagina,
            mensaje,
            on_confirmar
        )
        pagina.overlay.append(dialog)
        dialog.open = True
        pagina.update()

    # Abro el dialogo para buscar productos con F3
    def buscar_producto():
        if modo_consulta:
            return
        dialog = buscar_producto_view(pagina, agregar_producto_a_tabla)
        pagina.overlay.append(dialog)
        dialog.open = True
        pagina.update()

    # Muestro el cliente seleccionado en el campo de cliente
    def seleccionar_cliente(cliente):
        nonlocal cliente_actual
        cliente_actual = cliente
        nombre = cliente.get("nombre", "Sin nombre")
        rol = cliente.get("rol", "Sin rol")
        nombreCliente.value = f"{nombre} - {rol}"
        pagina.update()
    

    # Funcion pendiente para buscar cliente
    def buscar_cliente():
        if modo_consulta:
            return
        dialog = buscar_cliente_view(pagina, seleccionar_cliente)
        pagina.overlay.append(dialog)
        dialog.open = True
        pagina.update()

    def crearP_C():
        def on_crear(opcion):
            if opcion == "CrearP":
                print("Abrir crear producto")
            elif opcion == "CrearU":
                print("Abrir crear usuario") 

        dialog = Crear(pagina, on_crear)
        pagina.overlay.append(dialog)
        dialog.open = True
        pagina.update()


    # ---------------- TECLADO ----------------

    # Detecto las teclas rapidas de la pantalla de ventas
    async def teclado(e: ft.KeyboardEvent):

        # F2 factura la venta
        if e.key == "F2":
            facturar()

        # Escape vuelve al menu
        elif e.key == "Escape":
            ir_a_menu(usuario)

        # F3 abre el buscador de productos
        elif e.key == "F3":
            buscar_producto()

        # F1 busca o enfoca el cliente
        elif e.key == "F1":
            buscar_cliente()

        # F4 crea una nueva factura
        elif e.key == "F4":
            nueva_factura()

        # F5 borra la factura actual
        elif e.key == "F5":
            borrar_factura_actual()

        # F6 siguiente factura guardada
        elif e.key == "F6":
            siguiente_factura()

        # F7 anterior factura guardada
        elif e.key == "F7":
            anterior_factura()
        
        # F8 Crear producto o cliente
        elif e.key == "F8":
            crearP_C()


    # ---------------- BOTONES ----------------

    # Boton para volver al menu principal
    Volver_menu = ft.Button("Volver [Esc]", on_click=lambda _: ir_a_menu(usuario))

    # Boton para abrir el buscador de productos con click
    btn_buscar_producto = ft.Button(
        "Buscar producto [F3]",
        on_click=lambda _: buscar_producto(),
        width=203,
        height=40,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            text_style=ft.TextStyle(size=15, weight="bold")
        )
    )

    # Boton para facturar la venta
    btn_facturar = ft.Button(
        "Facturar [F2]",
        on_click=lambda _: facturar(),
        bgcolor=ft.Colors.GREEN,
        color=ft.Colors.WHITE,
        width=200,
        height=40,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            text_style=ft.TextStyle(size=15, weight="bold")
        )
    )

    btn_buscar_cliente = ft.Button(
        "Buscar Cliente [F1]",
        on_click=lambda _: buscar_cliente(),
        width=187,
        height=40,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            text_style=ft.TextStyle(size=15, weight="bold")
        )
    )
    
    btn_registar_cliente = ft.Button(
        "Crear P/C [F8]",
        on_click=lambda _: crearP_C(),
        width=190,
        height=40,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            text_style=ft.TextStyle(size=15, weight="bold")
        )
    )

    # Boton para crear nueva factura
    btn_nueva_factura = ft.Button(
        "Nueva Factura [F4]",
        on_click=lambda _: nueva_factura(),
        width=190,
        height=40,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            text_style=ft.TextStyle(size=15, weight="bold")
        )
    )

    # Boton para consultar facturas guardadas
    btn_consultar = ft.Button(
        "Consultar [F6/F7]",
        on_click=lambda _: cargar_lista_facturas(),
        width=200,
        height=40,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            text_style=ft.TextStyle(size=15, weight="bold")
        )
    )

    btn_imprimir_consulta = ft.Button(
        "Imprimir consulta",
        on_click=lambda _: imprimir_factura_consultada(),
        width=200,
        height=40,
        visible=False,
        bgcolor=ft.Colors.BLUE,
        color=ft.Colors.WHITE,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            text_style=ft.TextStyle(size=15, weight="bold")
        )
    )

    # Boton para borrar factura
    btn_borrarFactura = ft.Button(
        "Borrar [F5]",
        on_click=lambda _: borrar_factura_actual(),
        width=200,
        height=40,
        bgcolor=ft.Colors.RED,
        color=ft.Colors.WHITE,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            text_style=ft.TextStyle(size=15, weight="bold")
        )
    )

    # ---------------- TABLA PRODUCTOS ----------------

    # Tabla donde se muestran los productos agregados a la venta
    tabla_productos = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Codigo")),
            ft.DataColumn(ft.Text("Producto")),
            ft.DataColumn(ft.Text("Cantidad")),
            ft.DataColumn(ft.Text("Unidad")),
            ft.DataColumn(ft.Text("Precio unitario")),
            ft.DataColumn(ft.Text("Subtotal")),
            ft.DataColumn(ft.Text("Empresa")),
            ft.DataColumn(ft.Text("")), # Columna para el botón eliminar
        ],
        rows=[],
        border=ft.Border.all(1, ft.Colors.BLACK),
        border_radius=10,
        vertical_lines=ft.BorderSide(1, ft.Colors.BLACK_26),
        horizontal_lines=ft.BorderSide(1, ft.Colors.BLACK),
    )

    # ---------------- PANELES ----------------

    # Panel izquierdo con los datos de la venta y la tabla de productos
    panel_izquierdo = ft.Container(
        expand=True,
        bgcolor=ft.Colors.WHITE,
        border=ft.Border.all(1, ft.Colors.BLACK),
        border_radius=10,
        padding=20,
        content=ft.Column(
            [
                # Encabezado
                ft.Row(
                    [
                        ft.Text(
                            "Nueva venta",
                            weight="bold",
                            size=17
                        ),
                        numeroFactura,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),

                # Botones
                ft.Row(
                    [
                        btn_nueva_factura,
                        btn_buscar_producto,
                        btn_buscar_cliente,
                        btn_registar_cliente
                    ],
                    spacing=5
                ),
                ft.Divider(),
                # Cliente
                ft.Row(
                    [
                        ft.Text(
                            "Productos agregados",
                            size=15,
                            weight="bold"
                        ),
                        nombreCliente
                    ],
                    spacing=20,
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                # TABLA CON SCROLL
                ft.Container(
                    expand=True,
                    border_radius=10,
                    content=ft.Column(
                        expand=True,
                        scroll=ft.ScrollMode.AUTO,
                        controls=[
                            ft.Row(
                                scroll=ft.ScrollMode.AUTO,
                                controls=[
                                    tabla_productos
                                ]
                            )
                        ]
                    )
                )
            ],
            expand=True,
            spacing=20
        )
    )

    # Panel derecho con el resumen de la venta
    panel_derecho = ft.Container(
        width=230,
        bgcolor=ft.Colors.WHITE,
        border=ft.Border.all(1, ft.Colors.BLACK),
        border_radius=10,
        padding=20,
        content=ft.Column(
            [
                ft.Text("Resumen de venta", weight="bold", size=17),

                subtotal,
                descuento,

                ft.Divider(),

                total,

                ft.Divider(),

                texto_fecha,
                usuarioFactura,


                ft.Row(
                    btn_facturar,
                    spacing=10,
                    alignment=ft.MainAxisAlignment.CENTER,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                ),
                ft.Row(
                    btn_consultar,
                    spacing=10,
                    alignment=ft.MainAxisAlignment.CENTER,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                ),
                ft.Row(
                    btn_imprimir_consulta,
                    spacing=10,
                    alignment=ft.MainAxisAlignment.CENTER,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                ),
                ft.Row(
                    btn_borrarFactura,
                    spacing=10,
                    alignment=ft.MainAxisAlignment.CENTER,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                )
            ],
            spacing=20
        )
    )

    # ---------------- LAYOUT ----------------

    # Agrego toda la interfaz a la pagina
    pagina.add(
        ft.Column(
            [
                # Barra superior con logo, titulo, hora y boton volver
                ft.Container(
                    bgcolor=ft.Colors.WHITE,
                    border=ft.Border.all(1, ft.Colors.BLACK),
                    padding=ft.Padding.symmetric(horizontal=20, vertical=10),
                    content=ft.Row(
                        [
                            ft.Row(
                                [
                                    titulo,
                                    texto_usuario,
                                    texto_nombre,
                                    fecha_hora,
                                    Volver_menu,
                                ],
                                spacing=15,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                expand=True,
                                alignment=ft.MainAxisAlignment.CENTER
                            ),
                            logo
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        expand=True
                    )
                ),
                # Cuerpo principal dividido en panel izquierdo y derecho
                ft.Row(
                    [
                        panel_izquierdo,
                        panel_derecho
                    ],
                    expand=True,
                    spacing=10,
                    alignment=ft.MainAxisAlignment.START,
                    vertical_alignment=ft.CrossAxisAlignment.START
                )
            ],
            expand=True,
            spacing=0
        )
    )

    # Activo los atajos de teclado de esta vista
    pagina.on_keyboard_event = teclado

    # Refresco la pantalla
    pagina.update()

    # Cargo la lista de facturas para poder navegar con F6/F7
    cargar_lista_facturas()

    # Inicio la tarea que actualiza la hora
    pagina.run_task(actualizar_hora)
