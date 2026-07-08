import flet as ft
from datetime import datetime
import asyncio
from utils.buscarProducto import buscar_producto_view
from utils.buscarCliente import buscar_cliente_view
from controllers import remisionController as remision_controller
from utils.crearP_C import Crear
from utils.confirmacion import confirmar_view
from utils.abrirNuevaVentana import abrir_nueva_instancia

# =========================================================
# VISTA PRINCIPAL PARA BUSCAR Y REALIZAR REMISIONES
# =========================================================

def remision(pagina: ft.Page, ir_a_main, ir_a_menu, usuario):
#------------------- DATOS -----------------

    # Guardo los productos que voy agregando a la remision
    productos = []

    # Guardo el cliente que selecciono para la remision
    cliente_actual = None

    # Variables para navegar las remisiones guardadas
    remisiones = []
    index_remision = -1
    modo_consulta = False
    id_remision_actual = None

    # Control para alternar entre crear una nueva remisión en la misma ventana o abrir otra ventana
    f4_siguiente_abrir_ventana = True
    opciones_remision = remision_controller.obtener_opciones_remision()
#-------------------------------------------

    # Limpio la consola y la pantalla
    pagina.clean()

    # TamaÃ±o de la ventana para el login
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

    subtotal  = ft.Text("Productos: 0", weight="bold")
    descuento = ft.Text("Cantidad total: 0", weight="bold")
    total     = ft.Text("Valor: No aplica", weight="bold")

    fecha_hora  = ft.Text("", size=15)
    nombreCliente = ft.TextField(label="Cliente seleccionado ", width=260, read_only=True)
    texto_usuario = ft.Text(f"Usuario: {usuario['usuario']}", size=15, weight="bold")
    texto_nombre  = ft.Text(f"Nombre: {usuario['nombre']}",  size=15, weight="bold")

    numeroFactura = ft.Text("Numero de remision: 0001", size=17, weight="bold")

    # Campo de notas (aparecerá solo para Retiro Transformación)
    campo_notas = ft.TextField(
        label="Notas",
        width=400,
        multiline=True,
        max_lines=3,
        visible=False
    )

    nota_remision = ft.Container(
        visible=False,
        content=ft.Column(
            [
                ft.Text("Nota", weight="bold"),
                ft.Text("", size=13)
            ],
            spacing=5
        )
    )

    fecha_remision = ft.Text(
        "",
        size=13,
        weight="bold",
        visible=False
    )

    usuarioRemision = ft.Text(
        "",
        size=13,
        weight="bold",
        visible=False
    )

    # ---------------- FUNCIONES ----------------

    # Actualizo el resumen de la remision en pantalla
    def actualizar_totales():

        resumen = remision_controller.calcular_resumen(productos)

        # En remision no se manejan precios, solo conteo y cantidades.
        subtotal.value = f"Productos: {resumen['productos']}"
        descuento.value = f"Cantidad total: {resumen['cantidad_total']}"
        total.value = "Valor: No aplica"
        pagina.update()

    # Agrego el producto seleccionado en el buscador a la tabla
    # Agrego el producto seleccionado en la tabla
    def agregar_producto_a_tabla(producto):

        if modo_consulta:
            return

        # Obtengo el stock actual del producto
        stock_actual = producto.get("stock", 0)

        # Cantidad que el usuario quiere agregar
        cantidad = producto.get("cantidad", 1)

        producto["subtotal"] = (
            producto["cantidad"] * producto["precio"]
        )

        productos.append(producto)

        cantidad_texto = remision_controller.formatear_cantidad(
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
                        on_click=lambda e, idx=productos.index(producto): editar_cantidad(idx)
                    )
                ),
                    ft.DataCell(ft.Text(str(producto.get('unidad', 'UND')))),
                    ft.DataCell(ft.Text(f"${producto.get('precio', 0):,.2f}")),
                    ft.DataCell(ft.Text(f"${producto.get('subtotal', 0):,.2f}")),
                    ft.DataCell(ft.Text(str(producto.get('lugar', '-')))),
                    ft.DataCell(
                    ft.IconButton(
                        icon=ft.Icons.CLOSE,
                        icon_color=ft.Colors.RED,
                        on_click=lambda e, idx=-1: eliminar_producto(idx)
                    )
                )
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

    def confirmar_remision(tipo_remision, notas=""):
        resultado = remision_controller.confirmar_remision(
            tipo_remision=tipo_remision,
            productos=productos,
            cliente=cliente_actual,
            usuario=usuario,
            notas=notas
        )

        if not resultado:
            print("Error al guardar la remision")
            return

        print(f"Remision {resultado['id_remision']} guardada")
        print(f"PDF: {resultado['ruta_pdf']}")
        limpiar_factura()

    # ---------------- FACTURAR ----------------
    dialog_remision = None

    def facturar():
        nonlocal dialog_remision

        if modo_consulta:
            print("No se puede generar remision en modo consulta")
            return
        if not productos:
            print("No hay productos en la remision")
            return

        # Guardar el teclado anterior (de remision.py)
        teclado_anterior = pagina.on_keyboard_event

        def cerrar_dialogo(e=None):
            dialog_remision.open = False
            # Restaurar el teclado anterior
            if pagina.on_keyboard_event == teclado_dialogo:
                pagina.on_keyboard_event = teclado_anterior
            pagina.update()

        tipo_remision = ft.RadioGroup(
            value="Retiro Transformacion",
            content=ft.Column(
                [ft.Radio(value=opcion, label=opcion) for opcion in opciones_remision],
                spacing=6
            )
        )

        def seleccionar_tipo(e):
            # Mostrar campo de notas solo para Retiro Transformación
            campo_notas.visible = (e.control.value == "Retiro Transformacion")
            campo_notas.value = ""  # Limpiar notas al cambiar tipo
            pagina.update()

        tipo_remision.on_change = seleccionar_tipo

        def generar(e=None):
            cerrar_dialogo()
            notas = campo_notas.value if campo_notas.visible else ""
            confirmar_remision(tipo_remision.value, notas)

        # Inicializar notas para el diálogo
        campo_notas.value = ""
        campo_notas.visible = True

        dialog_remision = ft.AlertDialog(
            modal=True,
            title=ft.Text("Generar remision", weight="bold"),
            content=ft.Container(
                width=430,
                content=ft.Column(
                    [
                        ft.Text("Selecciona el motivo de la remision:"),
                        tipo_remision,
                        campo_notas,
                    ],
                    spacing=10
                )
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=cerrar_dialogo),
                ft.Button(
                    "Generar PDF",
                    bgcolor=ft.Colors.GREEN,
                    color=ft.Colors.WHITE,
                    on_click=generar,
                    autofocus=True
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )

        # Teclado temporal del diálogo
        async def teclado_dialogo(e: ft.KeyboardEvent):
            if e.key == "Escape":
                cerrar_dialogo()
            elif e.key == "Enter":
                generar()

        # Reemplazar temporalmente el teclado
        pagina.on_keyboard_event = teclado_dialogo

        pagina.overlay.append(dialog_remision)
        dialog_remision.open = True
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
                            remision_controller.formatear_cantidad(
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
                actualizar_totales()
                pagina.update()

            except:
                pass
        tabla_productos.rows[index].cells[2] = ft.DataCell(campo)
        campo.on_submit = guardar
        pagina.update()

    def eliminar_producto(index):

        if modo_consulta:
            return

        productos.pop(index)
        tabla_productos.rows.clear()

        for i, p in enumerate(productos):
            cantidad_texto = remision_controller.formatear_cantidad(
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
                        ft.DataCell(
                            ft.IconButton(
                                icon=ft.Icons.CLOSE,
                                icon_color=ft.Colors.RED,
                                on_click=lambda e, idx=i: eliminar_producto(idx)
                            )
                        )
                    ]
                )
            )

        actualizar_totales()

        pagina.update()


    def limpiar_factura():

        nonlocal productos
        nonlocal modo_consulta
        nonlocal id_remision_actual
        nonlocal cliente_actual

        productos = []
        cliente_actual = None

        tabla_productos.rows.clear()

        usuarioRemision.value = ""
        usuarioRemision.visible = False

        nombreCliente.value = ""

        numeroFactura.value = "Numero de remision: Nueva"
        nota_remision.visible = False
        nota_remision.content.controls[1].value = ""
        fecha_remision.value = ""
        fecha_remision.visible = False

        actualizar_totales()

        modo_consulta = False
        id_remision_actual = None
        btn_imprimir_consulta.visible = False

        pagina.update()

    def cargar_remision_actual(id_remision):
        nonlocal productos, modo_consulta, id_remision_actual

        datos = remision_controller.cargar_remision(id_remision)
        if not datos:
            return False

        remision_actual = datos["remision"]
        campo_notas.value = remision_actual.get("notas", "")
        campo_notas.visible = True

        fecha = remision_actual.get("fecha")

        if fecha:
            fecha_remision.value = (
                "Fecha: " +
                fecha.strftime("%d/%m/%Y %H:%M:%S")
            )
            fecha_remision.visible = True


        usuarioRemision.value = (
            f"Hecha por: {remision_actual.get('nombre_usuario', 'Sin usuario')}"
        )
        usuarioRemision.visible = True

        cliente = datos["cliente"]
        productos = datos["productos"]

        tabla_productos.rows.clear()
        for i, producto in enumerate(productos):
            cantidad_texto = remision_controller.formatear_cantidad(
                producto["cantidad"]
            )
            tabla_productos.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(
                            ft.Text(str(producto.get("id", "-")))
                        ),
                        ft.DataCell(
                            ft.Text(producto.get("nombre", "Sin nombre"))
                        ),
                        ft.DataCell(
                            ft.TextButton(
                                content=ft.Text(cantidad_texto),
                                on_click=lambda e, idx=i: editar_cantidad(idx)
                            )
                        ),
                        ft.DataCell(
                            ft.Text(producto.get("unidad", "UND"))
                        ),
                        ft.DataCell(
                            ft.Text(
                                f"${producto.get('precio', 0):,.2f}"
                            )
                        ),
                        ft.DataCell(
                            ft.Text(
                                f"${producto.get('subtotal', 0):,.2f}"
                            )
                        ),
                        ft.DataCell(
                            ft.Text(str(producto.get("lugar", "-")))
                        ),
                        ft.DataCell(
                            ft.IconButton(
                                icon=ft.Icons.CLOSE,
                                icon_color=ft.Colors.RED,
                                on_click=lambda e, idx=i: eliminar_producto(idx),
                                disabled=modo_consulta
                            )
                        )
                    ]
                )
            )
        nombreCliente.value = (
            f"{cliente['nombre']} - {cliente['rol']}"
            if cliente else "Sin cliente"
        )
        numeroFactura.value = (
            f"Numero de remision: "
            f"{id_remision:04d} - "
            f"{remision_actual['tipo_remision']}"
        )
        notas = (remision_actual.get("notas") or "").strip()
        nota_remision.visible = bool(notas)
        nota_remision.content.controls[1].value = notas
        actualizar_totales()

        modo_consulta = True
        id_remision_actual = id_remision
        btn_imprimir_consulta.visible = True
        pagina.update()
        return True
    
    def imprimir_remision_consultada():
        if not modo_consulta or id_remision_actual is None:
            print("Primero consulta una remision para imprimirla")
            return

        resultado = remision_controller.imprimir_remision_consultada(
            id_remision_actual,
            usuario
        )

        if not resultado:
            print("No se pudo imprimir la remision consultada")
            return

        print(f"Remision {id_remision_actual} enviada a imprimir")

    def nueva_remision():
        nonlocal index_remision, modo_consulta, f4_siguiente_abrir_ventana

        # Si ya se usó el cambio anterior, abro una segunda ventana
        if not f4_siguiente_abrir_ventana:
            abrir_nueva_instancia("remision", usuario)
            f4_siguiente_abrir_ventana = True
            return

        # Si es la primera vez, limpio la remisión actual y preparo una nueva en la misma ventana
        remisiones.clear()
        index_remision = -1
        modo_consulta = False
        limpiar_factura()
        f4_siguiente_abrir_ventana = False

    def siguiente_remision():
        nonlocal index_remision
        if not remisiones:
            cargar_lista_remisiones()
            return
        index_remision = (index_remision + 1) % len(remisiones)
        cargar_remision_actual(remisiones[index_remision]['id_remision'])

    def anterior_remision():
        nonlocal index_remision
        if not remisiones:
            cargar_lista_remisiones()
            return
        index_remision = (index_remision - 1) % len(remisiones)
        cargar_remision_actual(remisiones[index_remision]['id_remision'])

    def cargar_lista_remisiones():
        nonlocal remisiones, index_remision
        remisiones = remision_controller.listar_remisiones()
        if remisiones:
            index_remision = 0
            cargar_remision_actual(remisiones[0]['id_remision'])
        else:
            limpiar_factura()

    def borrar_remision_actual():
        nonlocal index_remision
        # -----------------------------
        # NUEVA REMISION
        # -----------------------------
        if not modo_consulta:
            mensaje = "¿Deseas limpiar la remision actual?"
        # -----------------------------
        # MODO CONSULTA
        # -----------------------------
        else:
            # VALIDAR PERMISOS
            if usuario.get("rol", "") == "Aprendiz":
                snack = ft.SnackBar(
                    content=ft.Text(
                        "No tienes permisos para anular remisiones"
                    ),
                    bgcolor=ft.Colors.RED
                )
                pagina.overlay.append(snack)
                snack.open = True
                pagina.update()
                return

            mensaje = f"¿Deseas anular la remision #{id_remision_actual:04d}?"
        # -----------------------------
        # CONFIRMACION
        # -----------------------------
        def on_confirmar(confirmado):
            if not confirmado:
                return
            # LIMPIAR
            if not modo_consulta:
                limpiar_factura()
                snack = ft.SnackBar(
                    content=ft.Text("Remision limpiada"),
                    bgcolor=ft.Colors.BLUE
                )
                pagina.overlay.append(snack)
                snack.open = True
                pagina.update()
                return
            # ANULAR
            if id_remision_actual is None:
                return
            if remision_controller.borrar_remision(id_remision_actual):
                snack = ft.SnackBar(
                    content=ft.Text("Remision anulada"),
                    bgcolor=ft.Colors.RED
                )
                pagina.overlay.append(snack)
                snack.open = True
                remisiones.clear()
                index_remision = -1
                cargar_lista_remisiones()
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
        dialog = buscar_producto_view(pagina, agregar_producto_a_tabla, mostrar_precio=False)
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

    # Detecto las teclas rapidas de la pantalla de remision
    async def teclado(e: ft.KeyboardEvent):

        # F2 genera la remision
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

        # F4 crea una nueva remision
        elif e.key == "F4":
            nueva_remision()

        # F5 borra la remision actual
        elif e.key == "F5":
            borrar_remision_actual()

        # F6 muestra la siguiente remision guardada
        elif e.key == "F6":
            siguiente_remision()

        # F7 muestra la remision anterior guardada
        elif e.key == "F7":
            anterior_remision()
        
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

    # Boton para generar la remision
    btn_facturar = ft.Button(
        "Generar [F2]",
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

    # Boton para crear nueva remision
    btn_nueva_factura = ft.Button(
        "Nueva Remision [F4]",
        on_click=lambda _: nueva_remision(),
        width=210,
        height=40,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            text_style=ft.TextStyle(size=15, weight="bold")
        )
    )

    # Boton para consultar remisiones guardadas
    btn_consultar = ft.Button(
        "Consultar [F6/F7]",
        on_click=lambda _: cargar_lista_remisiones(),
        width=200,
        height=40,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            text_style=ft.TextStyle(size=15, weight="bold")
        )
    )

    btn_imprimir_consulta = ft.Button(
        "Imprimir consulta",
        on_click=lambda _: imprimir_remision_consultada(),
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

    # Boton para borrar remision
    btn_borrarFactura = ft.Button(
        "Borrar [F5]",
        on_click=lambda _: borrar_remision_actual(),
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

    # Tabla donde se muestran los productos agregados a la remision
    tabla_productos = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Codigo")),
            ft.DataColumn(ft.Text("Producto")),
            ft.DataColumn(ft.Text("Cantidad")),
            ft.DataColumn(ft.Text("Unidad")),
            ft.DataColumn(ft.Text("Precio")),
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

    # Panel izquierdo con los datos de la remision y la tabla de productos
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
                            "Nueva remision",
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

    # Panel derecho con el resumen de la remision
    panel_derecho = ft.Container(
        width=230,
        bgcolor=ft.Colors.WHITE,
        border=ft.Border.all(1, ft.Colors.BLACK),
        border_radius=10,
        padding=20,
        content=ft.Column(
            [
                ft.Text("Resumen de remision", weight="bold", size=17),

                subtotal,
                descuento,

                ft.Divider(),

                nota_remision,
                fecha_remision,
                usuarioRemision,

                ft.Divider(),

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


    cargar_lista_remisiones() # Cargo las remisiones para mostrar la primera al cargar la vista

    # Refresco la pantalla
    pagina.update()

    # Inicio la tarea que actualiza la hora
    pagina.run_task(actualizar_hora)
