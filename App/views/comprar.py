import flet as ft
from datetime import datetime
import asyncio
from utils.buscarProducto import buscar_producto_view
from controllers import comprasController as compras_controller
from utils.metodoPago import metodo_pago_view
from utils.crearP_C import Crear
from utils.confirmacion import confirmar_view
from utils.buscarProveedor import buscar_proveedor_view


# =========================================================
# VISTA PRINCIPAL PARA COMPRAS
# =========================================================

def compras_view(pagina: ft.Page, ir_a_main, ir_a_menu, usuario):
    # Datos de la compra
    productos = []
    proveedor_actual = None
    compras = []
    index_compra = -1
    modo_consulta = False
    id_compra_actual = None

    pagina.clean()
    pagina.window.width = 1400
    pagina.window.height = 800
    pagina.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    pagina.vertical_alignment = ft.MainAxisAlignment.CENTER

    logo = ft.Image(src="assets/Logo_sena.png", width=50, height=50)
    titulo = ft.Text("Sistema POS - Compras", size=15, weight="bold")

    subtotal = ft.Text("Subtotal: $0", weight="bold")
    descuento = ft.Text("Descuento: $0", weight="bold")
    total = ft.Text("Total: $0", weight="bold")

    fecha_hora = ft.Text("", size=15)
    nombreProveedor = ft.TextField(label="Proveedor seleccionado", width=260, read_only=True)
    texto_usuario = ft.Text(f"Usuario: {usuario['usuario']}", size=15, weight="bold")
    texto_nombre = ft.Text(f"Nombre: {usuario['nombre']}", size=15, weight="bold")
    numeroCompra = ft.Text("Número de compra: Nueva", size=17, weight="bold")
    fechaCompra = ft.Text("", size=13, weight="bold")

    usuarioCompra = ft.Text(
        "",
        size=13,
        weight="bold",
        visible=False
    )

    def actualizar_totales():
        subtotal_total = compras_controller.calcular_total(productos)
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
                            compras_controller.formatear_cantidad(
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

    def refrescar_tabla():
        tabla_productos.rows.clear()
        for p in productos:
            cantidad_texto = compras_controller.formatear_cantidad(p["cantidad"])
            tabla_productos.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(p.get('id', '-')))),
                        ft.DataCell(ft.Text(p.get('nombre', 'Sin nombre'))),
                        ft.DataCell(
                            ft.TextButton(
                                content=ft.Text(cantidad_texto),
                                on_click=lambda e, idx=productos.index(p): editar_cantidad(idx)
                            )
                        ),
                        ft.DataCell(ft.Text(str(p.get('unidad', 'UND')))),
                        ft.DataCell(ft.Text(f"${p.get('precio', 0):,.2f}")),
                        ft.DataCell(ft.Text(f"${p.get('subtotal', 0):,.2f}")),
                        ft.DataCell(ft.Text(str(p.get('lugar', '-'))))
                    ]
                )
            )
        tabla_productos.update()

    def agregar_producto_a_tabla(producto):
        if modo_consulta:
            return

        cantidad = producto.get("cantidad", 1)

        for producto_existente in productos:
            if producto_existente["id"] == producto["id"]:
                producto_existente["cantidad"] += cantidad
                producto_existente["subtotal"] = (
                    float(producto_existente["cantidad"]) * float(producto_existente["precio"])
                )
                refrescar_tabla()
                actualizar_totales()
                return

        producto["subtotal"] = float(producto.get("cantidad", 1)) * float(producto.get("precio", 0))
        productos.append(producto)
        refrescar_tabla()
        actualizar_totales()

    async def actualizar_hora():
        while True:
            try:
                if fecha_hora.page is None:
                    await asyncio.sleep(0.1)
                    continue
            except RuntimeError:
                await asyncio.sleep(0.1)
                continue
            try:
                fecha_hora.value = datetime.now().strftime("%d/%m/%Y %I:%M:%S %p")
                fecha_hora.update()
            except RuntimeError:
                break
            await asyncio.sleep(1)

    def confirmar_compra(pago):

        resultado = compras_controller.confirmar_compra(

            proveedor=proveedor_actual,
            productos=productos,
            usuario=usuario
        )

        if not resultado:
            print("Error al guardar la compra")
            return

        print(f"Compra {resultado['id_compra']} guardada")
        print(f"PDF: {resultado['ruta_pdf']}")

        limpiar_compra()

    def facturar():
        if modo_consulta:
            return
        if not productos:
            snack = ft.SnackBar(
                content=ft.Text("Agrega productos antes de confirmar la compra."),
                bgcolor=ft.Colors.RED
            )
            pagina.overlay.append(snack)
            snack.open = True
            pagina.update()
            return

        total_valor = compras_controller.calcular_total(productos)
        dialog = metodo_pago_view(
            pagina,
            total_valor,
            confirmar_compra
        )
        pagina.overlay.append(dialog)
        dialog.open = True
        pagina.update()

    def limpiar_compra():
        nonlocal productos, proveedor_actual, modo_consulta
        productos = []
        proveedor_actual = None
        modo_consulta = False
        tabla_productos.rows.clear()
        nombreProveedor.value = ""
        numeroCompra.value = "Número de compra: Nueva"
        numeroCompra.color = ft.Colors.BLACK
        btn_imprimir_consulta.visible = False


        usuarioCompra.value = ""
        usuarioCompra.visible = False

        actualizar_totales()
        pagina.update()

    def seleccionar_proveedor(proveedor):
        nonlocal proveedor_actual
        proveedor_actual = proveedor
        nombre = proveedor.get("nombre", "Sin nombre")
        nombreProveedor.value = nombre
        pagina.update()

    def cargar_compra(id_compra):
        nonlocal productos, modo_consulta, id_compra_actual, proveedor_actual

        datos = compras_controller.cargar_compra(id_compra)
        if not datos:
            return False

        compra = datos["compra"]
        productos = datos["productos"]
        fechaCompra.value = (
            f"Fecha: {compra['fecha'].strftime('%d/%m/%Y %H:%M:%S')}"
        )
        proveedor_actual = datos.get("proveedor")

        tabla_productos.rows.clear()
        for producto in productos:
            cantidad_texto = compras_controller.formatear_cantidad(producto["cantidad"])
            tabla_productos.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(str(producto["id"]))),
                    ft.DataCell(ft.Text(producto["nombre"])),
                ft.DataCell(
                    ft.TextButton(
                        content=ft.Text(cantidad_texto),
                        on_click=lambda e, idx=productos.index(producto): editar_cantidad(idx)
                    )
                ),
                    ft.DataCell(ft.Text(producto["unidad"])),
                    ft.DataCell(ft.Text(f"${producto['precio']:,.2f}")),
                    ft.DataCell(ft.Text(f"${producto['subtotal']:,.2f}")),
                    ft.DataCell(ft.Text(producto["lugar"]))
                ])
            )

            nombreProveedor.value = (
                proveedor_actual.get("nombre", "")
                if proveedor_actual else ""
            )

            usuarioCompra.value = (
                f"Comprado por: {compra.get('nombre_usuario', 'Sin usuario')}"
            )
            usuarioCompra.visible = True

        if compra["estado"] == "ANULADA":
            numeroCompra.value = f"COMPRA ANULADA #{id_compra:04d}"
            numeroCompra.color = ft.Colors.RED
        else:
            numeroCompra.value = f"Número de compra: {id_compra:04d}"
            numeroCompra.color = ft.Colors.BLACK

        actualizar_totales()
        modo_consulta = True
        id_compra_actual = id_compra
        btn_imprimir_consulta.visible = True
        pagina.update()
        return True

    def imprimir_compra_consultada():
        if not modo_consulta or id_compra_actual is None:
            print("Primero consulta una compra para imprimirla")
            return

        resultado = compras_controller.imprimir_compra_consultada(
            id_compra_actual,
            usuario
        )

        if not resultado:
            print("No se pudo imprimir la compra consultada")
            return

        print(f"Compra {id_compra_actual} enviada a imprimir")

    def nueva_compra():
        nonlocal compras, index_compra, modo_consulta
        compras.clear()
        index_compra = -1
        modo_consulta = False
        limpiar_compra()

    def siguiente_compra():
        nonlocal index_compra
        if not compras:
            cargar_lista_compras()
            return
        index_compra = (index_compra + 1) % len(compras)
        cargar_compra(compras[index_compra]["id_compra"])

    def anterior_compra():
        nonlocal index_compra
        if not compras:
            cargar_lista_compras()
            return
        index_compra = (index_compra - 1) % len(compras)
        cargar_compra(compras[index_compra]["id_compra"])

    def cargar_lista_compras():
        nonlocal compras, index_compra
        compras = compras_controller.listar_compras()
        if compras:
            index_compra = 0
            cargar_compra(compras[0]["id_compra"])
        else:
            limpiar_compra()

    def borrar_compra_actual():
        nonlocal index_compra
        # -----------------------------
        # MODO NUEVA COMPRA
        # -----------------------------
        if not modo_consulta:
            mensaje = "¿Deseas limpiar la compra actual?"
        # -----------------------------
        # MODO CONSULTA
        # -----------------------------
        else:
            # VALIDAR PERMISOS
            if usuario.get("rol", "") == "Aprendiz":
                snack = ft.SnackBar(
                    content=ft.Text(
                        "No tienes permisos para anular compras"
                    ),
                    bgcolor=ft.Colors.RED
                )
                pagina.overlay.append(snack)
                snack.open = True
                pagina.update()
                return

            mensaje = f"¿Deseas anular la compra #{id_compra_actual:04d}?"
        # -----------------------------
        # CONFIRMAR
        # -----------------------------
        def on_confirmar(confirmado):
            if not confirmado:
                return
            # LIMPIAR
            if not modo_consulta:
                limpiar_compra()
                snack = ft.SnackBar(
                    content=ft.Text("Compra limpiada"),
                    bgcolor=ft.Colors.BLUE
                )
                pagina.overlay.append(snack)
                snack.open = True
                pagina.update()
                return
            
            # ANULAR
            if id_compra_actual is None:
                return
            
            if compras_controller.anular_compra(id_compra_actual):
                snack = ft.SnackBar(
                    content=ft.Text("Compra anulada"),
                    bgcolor=ft.Colors.RED
                )

                pagina.overlay.append(snack)
                snack.open = True
                compras.clear()
                index_compra = -1
                cargar_lista_compras()

        dialog = confirmar_view(
            pagina,
            mensaje,
            on_confirmar
        )
        pagina.overlay.append(dialog)
        dialog.open = True
        pagina.update()

    def buscar_proveedor():
        dialog = buscar_proveedor_view(
            pagina,
            seleccionar_proveedor
        )
        pagina.overlay.append(dialog)
        dialog.open = True
        pagina.update()

    def buscar_producto():
        dialog = buscar_producto_view(pagina, agregar_producto_a_tabla)
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

    async def teclado(e: ft.KeyboardEvent):
        if e.key == "F2":
            facturar()
        elif e.key == "Escape":
            ir_a_menu(usuario)
        elif e.key == "F3":
            buscar_producto()
        elif e.key == "F1":
            buscar_proveedor()
        elif e.key == "F4":
            nueva_compra()
        elif e.key == "F5":
            borrar_compra_actual()
        elif e.key == "F6":
            siguiente_compra()
        elif e.key == "F7":
            anterior_compra()
        elif e.key == "F8":
            crearP_C()

    Volver_menu = ft.Button("Volver [Esc]", on_click=lambda _: ir_a_menu(usuario))

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
    
    btn_confirmar = ft.Button(
        "compra [F2]",
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
    
    btn_buscar_proveedor = ft.Button(
        "Buscar proveedor [F1]",
        on_click=lambda _: buscar_proveedor(),
        width=230,
        height=40,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            text_style=ft.TextStyle(size=15, weight="bold")
        )
    )
    
    btn_crear_pc = ft.Button(
        "Crear P/C [F8]",
        on_click=lambda _: crearP_C(),
        width=190,
        height=40,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            text_style=ft.TextStyle(size=15, weight="bold")
        )
    )
    
    btn_nueva_compra = ft.Button(
        "Nueva compra [F4]",
        on_click=lambda _: nueva_compra(),
        width=190,
        height=40,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            text_style=ft.TextStyle(size=15, weight="bold")
        )
    )

    btn_consultar = ft.Button(
        "Consultar [F6/F7]",
        on_click=lambda _: cargar_lista_compras(),
        width=200,
        height=40,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            text_style=ft.TextStyle(size=15, weight="bold")
        )
    )

    btn_imprimir_consulta = ft.Button(
        "Imprimir consulta",
        on_click=lambda _: imprimir_compra_consultada(),
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

    btn_borrar_compra = ft.Button(
        "Anular [F5]",
        on_click=lambda _: borrar_compra_actual(),
        width=200,
        height=40,
        bgcolor=ft.Colors.RED,
        color=ft.Colors.WHITE,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            text_style=ft.TextStyle(size=15, weight="bold")
        )
    )

    tabla_productos = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Codigo")),
            ft.DataColumn(ft.Text("Producto")),
            ft.DataColumn(ft.Text("Cantidad")),
            ft.DataColumn(ft.Text("Unidad")),
            ft.DataColumn(ft.Text("Precio unitario")),
            ft.DataColumn(ft.Text("Subtotal")),
            ft.DataColumn(ft.Text("Empresa")),
        ],
        rows=[],
        border=ft.Border.all(1, ft.Colors.BLACK),
        border_radius=10,
        vertical_lines=ft.BorderSide(1, ft.Colors.BLACK_26),
        horizontal_lines=ft.BorderSide(1, ft.Colors.BLACK),
    )

    panel_izquierdo = ft.Container(
        expand=True,
        bgcolor=ft.Colors.WHITE,
        border=ft.Border.all(1, ft.Colors.BLACK),
        border_radius=10,
        padding=20,
        content=ft.Column(
            [
                ft.Row([ft.Text("Nueva compra", weight="bold", size=17), numeroCompra], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([btn_nueva_compra, btn_buscar_producto, btn_buscar_proveedor, btn_crear_pc], spacing=5),
                ft.Divider(),
                ft.Row([ft.Text("Productos agregados", size=15, weight="bold"), nombreProveedor], spacing=20, alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(expand=True, border_radius=10, content=ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, controls=[ft.Row(scroll=ft.ScrollMode.AUTO, controls=[tabla_productos])]))
            ],
            expand=True,
            spacing=20
        )
    )

    panel_derecho = ft.Container(
        width=230,
        bgcolor=ft.Colors.WHITE,
        border=ft.Border.all(1, ft.Colors.BLACK),
        border_radius=10,
        padding=20,
        content=ft.Column(
            [
                ft.Text("Resumen de compra", weight="bold", size=17),
                subtotal,
                descuento,
                ft.Divider(),
                total,
                ft.Divider(),

                fechaCompra,
                usuarioCompra,

                ft.Divider(),
                ft.Row([btn_confirmar], spacing=10, alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Row([btn_consultar], spacing=10, alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Row([btn_imprimir_consulta], spacing=10, alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Row([btn_borrar_compra], spacing=10, alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER)
            ],
            spacing=20
        )
    )

    pagina.add(
        ft.Column(
            [
                ft.Container(
                    bgcolor=ft.Colors.WHITE,
                    border=ft.Border.all(1, ft.Colors.BLACK),
                    padding=ft.Padding.symmetric(horizontal=20, vertical=10),
                    content=ft.Row(
                        [
                            ft.Row([titulo, texto_usuario, texto_nombre, fecha_hora, Volver_menu], spacing=15, vertical_alignment=ft.CrossAxisAlignment.CENTER, expand=True, alignment=ft.MainAxisAlignment.CENTER),
                            logo
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        expand=True
                    )
                ),
                ft.Row([panel_izquierdo, panel_derecho], expand=True, spacing=10, alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START)
            ],
            expand=True,
            spacing=0
        )
    )

    cargar_lista_compras() # Cargo las compras para mostrar la primera al cargar la vista

    pagina.on_keyboard_event = teclado
    pagina.update()
    pagina.run_task(actualizar_hora)
