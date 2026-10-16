import flet as ft
from datetime import datetime
import asyncio
from utils.buscarProducto import buscar_producto_view
from controllers import comprasController as compras_controller
from utils.roles import es_facturador
from utils.metodoPago import metodo_pago_view
from utils.crearP_C import Crear
from utils.confirmacion import confirmar_view
from utils.buscarProveedor import buscar_proveedor_view
from utils.abrirNuevaVentana import abrir_nueva_instancia
from utils.notificaciones import mostrar_notificacion


# =========================================================
# VISTA PRINCIPAL PARA COMPRAS
# =========================================================
# Este módulo contiene la función `compras_view()` que construye la
# interfaz gráfica completa del módulo de compras del sistema POS.
#
# FUNCIONALIDADES:
#   - Agregar productos a la tabla de compra desde el buscador (F3)
#   - Seleccionar proveedor para la compra (F1)
#   - Editar cantidad y descuento de cada producto inline (click en celda)
#   - Calcular subtotal, descuento y total en tiempo real
#   - Confirmar la compra y generar el PDF de comprobante
#   - Consultar compras guardadas y navegar entre ellas (F6/F7)
#   - Anular compras existentes (solo admin/Aprendiz con permisos)
#   - Imprimir una compra ya consultada
#   - Crear nuevos productos o proveedores desde un diálogo (F8)
#   - Alternar entre crear nueva compra en la misma ventana o en una nueva (F4)
#
# ATAJOS DE TECLADO:
#   F1  → Buscar proveedor
#   F2  → Confirmar compra
#   F3  → Buscar producto
#   F4  → Nueva compra (1ra vez: limpia, 2da vez: abre nueva ventana)
#   F5  → Borrar/Anular compra
#   F6  → Siguiente compra guardada
#   F7  → Anterior compra guardada
#   F8  → Crear producto o proveedor
#   Escape → Volver al menú principal
#
# NAVEGACIÓN:
#   - ir_a_menu: vuelve al menú principal del sistema
#   - ir_a_main: vuelve a la pantalla principal (no se usa directamente aquí)
#
# DIFERENCIAS CON LA VISTA DE VENTAS (vender.py):
#   - Usa proveedor en lugar de cliente
#   - No maneja campo de notas
#   - El botón de confirmación se llama "compra" en vez de "Facturar"
#   - El controlador es comprasController en vez de ventasController
#
def compras_view(pagina: ft.Page, ir_a_main, ir_a_menu, usuario):
    # ------------------- DATOS -----------------
    # Lista de productos agregados a la compra actual.
    # Cada producto es un diccionario con: id, nombre, cantidad, unidad,
    # precio, descuento, subtotal, lugar, etc.
    productos = []

    # Proveedor seleccionado actualmente para la compra.
    # Se asigna cuando el usuario elige un proveedor desde el buscador (F1).
    proveedor_actual = None

    # Lista de compras cargadas desde la base de datos para navegación (F6/F7)
    compras = []

    # Índice actual dentro de la lista de compras (-1 = ninguna cargada)
    index_compra = -1

    # Bandera de modo consulta: True cuando se muestra una compra ya guardada.
    # En modo consulta no se pueden agregar/modificar productos.
    modo_consulta = False

    # ID de la compra que se está consultando actualmente
    id_compra_actual = None

    # Control para alternar entre crear una nueva compra en la misma ventana o abrir otra ventana.
    # Primera pulsación de F4 limpia la compra; segunda pulsación abre nueva ventana.
    f4_siguiente_abrir_ventana = True

    # Limpiar la página y configurar el tamaño de ventana
    pagina.clean()
    pagina.window.width = 1500
    pagina.window.height = 800

    # Centrar el contenido de la página
    pagina.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    pagina.vertical_alignment = ft.MainAxisAlignment.CENTER

    # ---------------- CAMPOS ----------------

    # Logo del SENA
    logo = ft.Image(src="Logo_sena.png", width=50, height=50)

    # Título de la vista
    titulo = ft.Text("Sistema POS - Compras", size=15, weight="bold")

    # Textos del resumen de compra (panel derecho).
    # Se actualizan dinámicamente cuando cambian los productos.
    subtotal = ft.Text("Subtotal: $0", weight="bold")
    descuento = ft.Text("Descuento: $0", weight="bold")
    total = ft.Text("Total: $0", weight="bold")

    # Reloj en tiempo real en la barra superior
    fecha_hora = ft.Text("", size=15)

    # Campo de solo lecturo que muestra el proveedor seleccionado
    nombreProveedor = ft.TextField(label="Proveedor seleccionado", width=260, read_only=True)

    # Información del usuario logueado
    texto_usuario = ft.Text(f"Usuario: {usuario['usuario']}", size=15, weight="bold")
    texto_nombre = ft.Text(f"Nombre: {usuario['nombre']}", size=15, weight="bold")

    # Número de compra actual (se actualiza al cargar o crear compras)
    numeroCompra = ft.Text("Número de compra: Nueva", size=17, weight="bold")

    # Campos de información de la compra consultada (ocultos por defecto,
    # se muestran solo cuando se carga una compra existente)
    fechaCompra = ft.Text("", size=13, weight="bold", visible=False)

    usuarioCompra = ft.Text(
        "",
        size=13,
        weight="bold",
        visible=False
    )

    # ---------------- FUNCIONES ----------------

    # Recalcula subtotal, descuento y total de la compra
    # usando el controlador con la lista actual de productos.
    def actualizar_totales():
        resumen = compras_controller.calcular_resumen_compra(productos)
        subtotal.value = f"Subtotal: ${resumen['subtotal']:,.2f}"
        descuento.value = f"Descuento: ${resumen['descuento']:,.2f}"
        total.value = f"Total: ${resumen['total']:,.2f}"
        pagina.update()

    # Permite editar la cantidad de un producto haciendo clic en la celda.
    # Reemplaza el texto por un TextField editable. Al presionar Enter
    # se guarda el nuevo valor, se actualiza la fila y los totales.
    # Los Aprendices no pueden editar en modo consulta.
    def editar_cantidad(index):

        # Bloquear si es Aprendiz en modo consulta
        if modo_consulta and es_facturador(usuario.get("rol")):
            return

        producto = productos[index]
        # Campo temporal con la cantidad actual
        campo = ft.TextField(
            value=str(producto["cantidad"]),
            autofocus=True,
            width=120
        )
        def guardar(e):
            try:
                nueva_cantidad = float(campo.value)
                # Actualizar en el controlador (recalcula subtotal del producto)
                compras_controller.actualizar_cantidad_producto_compra(producto, nueva_cantidad)
                # Restaurar celda de cantidad con valor formateado
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
                # Actualizar celda de subtotal
                tabla_productos.rows[index].cells[6] = ft.DataCell(
                    ft.Text(
                        f"${producto['subtotal']:,.2f}"
                    )
                )
                actualizar_totales()
                pagina.update()

            except:
                pass
        # Reemplazar celda con campo editable
        tabla_productos.rows[index].cells[2] = ft.DataCell(campo)
        campo.on_submit = guardar
        pagina.update()

    # Permite editar el descuento de un producto haciendo clic en la celda.
    # Funciona igual que editar_cantidad pero para el campo de descuento.
    def editar_descuento(index):

        # Bloquear si es Aprendiz en modo consulta
        if modo_consulta and es_facturador(usuario.get("rol")):
            return

        producto = productos[index]
        # Campo temporal con el descuento actual
        campo = ft.TextField(
            value=str(producto.get("descuento", 0)),
            autofocus=True,
            width=120
        )
        def guardar(e):
            try:
                nuevo_descuento = float(campo.value)
                # Actualizar descuento en el controlador
                compras_controller.actualizar_descuento_producto_compra(producto, nuevo_descuento)
                # Restaurar celda de descuento como botón clickeable
                tabla_productos.rows[index].cells[5] = ft.DataCell(
                    ft.TextButton(
                        content=ft.Text(
                            f"{producto['descuento']:,.2f}%"
                        ),
                        on_click=lambda e: editar_descuento(index)
                    )
                )
                # Actualizar celda de subtotal
                tabla_productos.rows[index].cells[6] = ft.DataCell(
                    ft.Text(
                        f"${producto['subtotal']:,.2f}"
                    )
                )
                actualizar_totales()
                pagina.update()
            except:
                pass
        # Reemplazar celda de descuento con campo editable
        tabla_productos.rows[index].cells[5] = ft.DataCell(campo)
        campo.on_submit = guardar
        pagina.update()

    # Quita un producto individual de la compra actual y actualiza la tabla y los totales.
    def eliminar_producto(index):
        if modo_consulta:
            return

        productos.pop(index)
        refrescar_tabla()
        actualizar_totales()

    # Reconstruye todas las filas de la tabla de productos desde la lista.
    # Se usa después de agregar productos o para refrescar la vista completa.
    def refrescar_tabla():
        
        tabla_productos.rows.clear()
        for i, p in enumerate(productos):
            cantidad_texto = compras_controller.formatear_cantidad(p["cantidad"])
            tabla_productos.rows.append(
                ft.DataRow(
                    cells=[
                        # Codigo del producto
                        ft.DataCell(ft.Text(str(p.get('id', '-')))),
                        # Nombre del producto
                        ft.DataCell(ft.Text(p.get('nombre', 'Sin nombre'))),
                        # Cantidad (editable al hacer clic)
                        ft.DataCell(
                            ft.TextButton(
                                content=ft.Text(cantidad_texto),
                                on_click=lambda e, idx=i: editar_cantidad(idx)
                            )
                        ),
                        # Unidad de medida
                        ft.DataCell(ft.Text(str(p.get('unidad', 'UND')))),
                        # Precio unitario
                        ft.DataCell(ft.Text(f"${p.get('precio', 0):,.2f}")),
                        # Descuento (editable al hacer clic)
                        ft.DataCell(
                            ft.TextButton(
                                content=ft.Text(f"${p.get('descuento', 0):,.2f}"),
                                on_click=lambda e, idx=i: editar_descuento(idx)
                            )
                        ),
                        # Subtotal del producto
                        ft.DataCell(ft.Text(f"${p.get('subtotal', 0):,.2f}")),
                        # Empresa/lugar del producto
                        ft.DataCell(ft.Text(str(p.get('lugar', '-')))),
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
        tabla_productos.update()

    # Agrega un producto seleccionado desde el buscador a la tabla de compra.
    # Delega al controlador la lógica de agregar/duplicar y luego refresca la tabla.
    def agregar_producto_a_tabla(producto):
        if modo_consulta:
            return

        # Agregar el producto a la lista (el controlador maneja duplicados)
        producto = compras_controller.agregar_producto_a_compra(productos, producto)
        # Reconstruir toda la tabla
        refrescar_tabla()
        # Recalcular totales
        actualizar_totales()

    # Tarea asíncrona que actualiza el reloj cada segundo.
    # Se detiene automáticamente cuando la vista ya no existe.
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
                # Actualizar con formato 12 horas (AM/PM)
                fecha_hora.value = datetime.now().strftime("%d/%m/%Y %I:%M:%S %p")
                fecha_hora.update()
            except RuntimeError:
                # La vista fue destruida, salir del ciclo
                break
            await asyncio.sleep(1)

    # Callback que se ejecuta después de confirmar el método de pago.
    # Guarda la compra en la base de datos y genera el PDF de comprobante.
    def confirmar_compra(pago):

        resultado = compras_controller.confirmar_compra(

            proveedor=proveedor_actual,
            productos=productos,
            usuario=usuario
        )

        if not resultado:
            print("Error al guardar la compra")
            mostrar_notificacion(pagina, "No fue posible guardar la compra.", error=True)
            return

        print(f"Compra {resultado['id_compra']} guardada")
        print(f"PDF: {resultado['ruta_pdf']}")

        # Limpiar la vista para una nueva compra
        limpiar_compra()
        mostrar_notificacion(
            pagina, f"Compra #{resultado['id_compra']} guardada correctamente."
        )

    # Abre el diálogo de método de pago para confirmar la compra.
    # Valida que haya productos y que no estemos en modo consulta.
    def facturar():
        if modo_consulta:
            return
        # No permitir confirmar sin productos
        if not productos:
            snack = ft.SnackBar(
                content=ft.Text("Agrega productos antes de confirmar la compra."),
                bgcolor=ft.Colors.RED
            )
            pagina.overlay.append(snack)
            snack.open = True
            pagina.update()
            return

        # Calcular el total para mostrarlo en el diálogo de pago
        total_valor = compras_controller.calcular_total(productos)
        # Abrir diálogo de método de pago con callback de confirmación
        dialog = metodo_pago_view(
            pagina,
            total_valor,
            confirmar_compra
        )
        pagina.overlay.append(dialog)
        dialog.open = True
        pagina.update()

    # Resetea toda la vista a su estado inicial para comenzar una nueva compra.
    # Limpia productos, proveedor, tabla, campos de texto y totales.
    def limpiar_compra():
        nonlocal productos, proveedor_actual, modo_consulta
        # Vaciar lista de productos y proveedor
        productos = []
        proveedor_actual = None
        modo_consulta = False

        # Limpiar filas de la tabla
        tabla_productos.rows.clear()

        # Vaciar campo de proveedor
        nombreProveedor.value = ""

        # Resetear número de compra
        numeroCompra.value = "Número de compra: Nueva"
        numeroCompra.color = ft.Colors.BLACK

        # Ocultar botón de imprimir (solo visible en modo consulta)
        btn_imprimir_consulta.visible = False

        # Ocultar campos de información de compra consultada
        usuarioCompra.value = ""
        usuarioCompra.visible = False
        fechaCompra.value = ""
        fechaCompra.visible = False

        # Recalcular totales (quedará en $0)
        actualizar_totales()
        pagina.update()

    # Callback que se ejecuta cuando el usuario selecciona un proveedor
    # desde el diálogo de búsqueda. Actualiza el campo en pantalla.
    def seleccionar_proveedor(proveedor):
        nonlocal proveedor_actual
        proveedor_actual = proveedor
        nombre = proveedor.get("nombre", "Sin nombre")
        nombreProveedor.value = nombre
        pagina.update()

    # Carga una compra existente desde la base de datos por su ID.
    # Reconstruye la tabla de productos, muestra datos del proveedor,
    # usuario que compró, fecha y el estado (anulada o activa).
    # Retorna True si se cargó correctamente, False si hubo error.
    def cargar_compra(id_compra):
        nonlocal productos, modo_consulta, id_compra_actual, proveedor_actual

        # Solicitar datos al controlador
        datos = compras_controller.cargar_compra(id_compra)
        if not datos:
            return False

        compra = datos["compra"]
        productos = datos["productos"]

        # Mostrar fecha de la compra
        fechaCompra.value = (
            f"Fecha: {compra['fecha'].strftime('%d/%m/%Y %H:%M:%S')}"
        )
        fechaCompra.visible = True

        # Guardar referencia del proveedor
        proveedor_actual = datos.get("proveedor")

        # Limpiar y reconstruir la tabla
        tabla_productos.rows.clear()
        for i, producto in enumerate(productos):
            cantidad_texto = compras_controller.formatear_cantidad(producto["cantidad"])
            tabla_productos.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(str(producto["id"]))),
                    ft.DataCell(ft.Text(producto["nombre"])),
                ft.DataCell(
                    ft.TextButton(
                        content=ft.Text(cantidad_texto),
                        on_click=lambda e, idx=i: editar_cantidad(idx)
                    )
                ),
                    ft.DataCell(ft.Text(producto["unidad"])),
                    ft.DataCell(ft.Text(f"${producto['precio']:,.2f}")),
                    ft.DataCell(
                        ft.TextButton(
                            content=ft.Text(f"{producto.get('descuento', 0):,.2f}%"),
                            on_click=lambda e, idx=i: editar_descuento(idx)
                        )
                    ),
                    ft.DataCell(ft.Text(f"${producto['subtotal']:,.2f}")),
                    ft.DataCell(ft.Text(producto["lugar"])),
                    ft.DataCell(
                        ft.IconButton(
                            icon=ft.Icons.CLOSE,
                            icon_color=ft.Colors.RED,
                            on_click=lambda e, idx=i: eliminar_producto(idx)
                        )
                    )
                ])
            )

            # Mostrar nombre del proveedor seleccionado
            nombreProveedor.value = (
                proveedor_actual.get("nombre", "")
                if proveedor_actual else ""
            )

            # Mostrar quién realizó la compra
            usuarioCompra.value = (
                f"Comprado por: {compra.get('nombre_usuario', 'Sin usuario')}"
            )
            usuarioCompra.visible = True

        # Mostrar número de compra con color según estado
        if compra["estado"] == "ANULADA":
            numeroCompra.value = f"COMPRA ANULADA #{id_compra:04d}"
            numeroCompra.color = ft.Colors.RED
        else:
            numeroCompra.value = f"Número de compra: {id_compra:04d}"
            numeroCompra.color = ft.Colors.BLACK

        actualizar_totales()

        # Activar modo consulta: bloquea edición
        modo_consulta = True
        id_compra_actual = id_compra

        # Mostrar botón de imprimir
        btn_imprimir_consulta.visible = True
        pagina.update()
        return True

    # Genera el PDF de la compra consultada y lo envía a imprimir.
    # Solo funciona si hay una compra cargada en modo consulta.
    def imprimir_compra_consultada():
        if not modo_consulta or id_compra_actual is None:
            print("Primero consulta una compra para imprimirla")
            return

        # Delegar al controlador la generación del PDF
        resultado = compras_controller.imprimir_compra_consultada(
            id_compra_actual,
            usuario
        )

        if not resultado:
            print("No se pudo imprimir la compra consultada")
            return

        print(f"Compra {id_compra_actual} enviada a imprimir")

    # Maneja la pulsación de F4 para nueva compra.
    # Primera vez: limpia la compra actual en la misma ventana.
    # Segunda vez: abre una nueva ventana con la vista de compras.
    def nueva_compra():
        nonlocal compras, index_compra, modo_consulta, f4_siguiente_abrir_ventana

        # Si ya se usó el cambio anterior, abro una segunda ventana
        if not f4_siguiente_abrir_ventana:
            abrir_nueva_instancia("compra", usuario)
            f4_siguiente_abrir_ventana = True
            return

        # Si es la primera vez, limpio la compra actual y preparo una nueva en la misma ventana
        compras.clear()
        index_compra = -1
        modo_consulta = False
        limpiar_compra()
        # Marcar que la próxima pulsación abrirá ventana nueva
        f4_siguiente_abrir_ventana = False

    # Navega a la siguiente compra guardada (F6).
    # Usa navegación circular: al llegar al final vuelve al principio.
    def siguiente_compra():
        nonlocal index_compra
        if not compras:
            cargar_lista_compras()
            return
        index_compra = (index_compra + 1) % len(compras)
        cargar_compra(compras[index_compra]["id_compra"])

    # Navega a la compra anterior guardada (F7).
    # Usa navegación circular: al llegar al inicio va al final.
    def anterior_compra():
        nonlocal index_compra
        if not compras:
            cargar_lista_compras()
            return
        index_compra = (index_compra - 1) % len(compras)
        cargar_compra(compras[index_compra]["id_compra"])

    # Carga la lista completa de compras desde la base de datos
    # y muestra la primera de la lista.
    def cargar_lista_compras():
        nonlocal compras, index_compra
        compras = compras_controller.listar_compras()
        if compras:
            index_compra = 0
            cargar_compra(compras[0]["id_compra"])
        else:
            limpiar_compra()

    # Borra o anula la compra actual según el modo:
    # - Modo nueva compra: simplemente limpia la tabla
    # - Modo consulta: anula la compra (requiere permisos)
    # Muestra un diálogo de confirmación antes de ejecutar la acción.
    def borrar_compra_actual():
        nonlocal index_compra
        # -----------------------------
        # MODO NUEVA COMPRA
        # -----------------------------
        if not modo_consulta:
            mensaje = "¿Deseas limpiar la compra actual?"
        # -----------------------------
        # MODO CONSULTA - ANULAR COMPRA
        # -----------------------------
        else:
            # Los Aprendices no tienen permisos para anular
            if es_facturador(usuario.get("rol")):
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
        # CONFIRMACIÓN GENERAL
        # -----------------------------
        def on_confirmar(confirmado):
            if not confirmado:
                return
            # LIMPIAR - modo nueva compra
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
            
            # ANULAR - modo consulta
            if id_compra_actual is None:
                return
            
            if compras_controller.anular_compra(id_compra_actual):
                snack = ft.SnackBar(
                    content=ft.Text("Compra anulada"),
                    bgcolor=ft.Colors.RED
                )

                pagina.overlay.append(snack)
                snack.open = True
                # Recargar lista después de anular
                compras.clear()
                index_compra = -1
                cargar_lista_compras()

        # Mostrar diálogo de confirmación
        dialog = confirmar_view(
            pagina,
            mensaje,
            on_confirmar
        )
        pagina.overlay.append(dialog)
        dialog.open = True
        pagina.update()

    # Abre el diálogo de búsqueda de proveedores (F1).
    # Se pasa `seleccionar_proveedor` como callback para que al
    # elegir un proveedor se muestre en la interfaz.
    def buscar_proveedor():
        dialog = buscar_proveedor_view(
            pagina,
            seleccionar_proveedor
        )
        pagina.overlay.append(dialog)
        dialog.open = True
        pagina.update()

    # Abre el diálogo de búsqueda de productos (F3).
    # Se pasa `agregar_producto_a_tabla` como callback.
    def buscar_producto():
        dialog = buscar_producto_view(pagina, agregar_producto_a_tabla)
        pagina.overlay.append(dialog)
        dialog.open = True
        pagina.update()

    # Abre el diálogo de creación rápida de productos o proveedores (F8).
    # Si se crea un proveedor, automáticamente lo selecciona para la compra.
    def crearP_C():
        def callback_creacion(datos):
            # Si se creó un proveedor, seleccionarlo automáticamente
            if datos.get("id_proveedor"):
                seleccionar_proveedor(datos)

        dialog = Crear(pagina, callback_creacion, tipo_tercero="proveedor")
        pagina.overlay.append(dialog)
        dialog.open = True
        pagina.update()

    # ---------------- TECLADO ----------------

    # Handler principal de atajos de teclado para la vista de compras.
    async def teclado(e: ft.KeyboardEvent):
        # F2 → Confirmar compra
        if e.key == "F2":
            facturar()
        # Escape → Volver al menú principal
        elif e.key == "Escape":
            ir_a_menu(usuario)
        # F3 → Abrir búsqueda de productos
        elif e.key == "F3":
            buscar_producto()
        # F1 → Abrir búsqueda de proveedores
        elif e.key == "F1":
            buscar_proveedor()
        # F4 → Nueva compra
        elif e.key == "F4":
            nueva_compra()
        # F5 → Borrar/Anular compra
        elif e.key == "F5":
            borrar_compra_actual()
        # F6 → Siguiente compra guardada
        elif e.key == "F6":
            siguiente_compra()
        # F7 → Anterior compra guardada
        elif e.key == "F7":
            anterior_compra()
        # F8 → Crear producto o proveedor
        elif e.key == "F8":
            crearP_C()

    # ---------------- BOTONES ----------------

    # Botón para volver al menú principal (atajo: Escape)
    Volver_menu = ft.Button("Volver [Esc]", on_click=lambda _: ir_a_menu(usuario))

    # Botón para abrir búsqueda de productos (atajo: F3)
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
    
    # Botón para confirmar la compra (atajo: F2).
    # Color verde para indicar acción de confirmación.
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
    
    # Botón para abrir búsqueda de proveedores (atajo: F1)
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
    
    # Botón para crear producto o proveedor (atajo: F8)
    btn_crear_pc = ft.Button(
        "Crear P/Prov [F8]",
        on_click=lambda _: crearP_C(),
        width=190,
        height=40,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            text_style=ft.TextStyle(size=15, weight="bold")
        )
    )
    
    # Botón para nueva compra (atajo: F4).
    # Primera pulsación: limpia. Segunda: abre nueva ventana.
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

    # Botón para cargar y consultar compras guardadas (atajos: F6/F7)
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

    # Botón para imprimir la compra consultada.
    # Solo visible cuando hay una compra cargada en modo consulta.
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

    # Botón para borrar/anular compra (atajo: F5).
    # Color rojo para indicar acción destructiva.
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

    # ---------------- TABLA PRODUCTOS ----------------

    # Tabla principal de productos de la compra.
    # Columnas: Codigo, Producto, Cantidad (editable), Unidad,
    #           Precio unitario, Descuento (editable), Subtotal, Empresa, quitar.
    tabla_productos = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Codigo")),
            ft.DataColumn(ft.Text("Producto")),
            ft.DataColumn(ft.Text("Cantidad")),
            ft.DataColumn(ft.Text("Unidad")),
            ft.DataColumn(ft.Text("Precio unitario")),
            ft.DataColumn(ft.Text("Descuento")),
            ft.DataColumn(ft.Text("Subtotal")),
            ft.DataColumn(ft.Text("Empresa")),
            ft.DataColumn(ft.Text("")),
        ],
        rows=[],
        border=ft.Border.all(1, ft.Colors.BLACK),
        border_radius=10,
        vertical_lines=ft.BorderSide(1, ft.Colors.BLACK_26),
        horizontal_lines=ft.BorderSide(1, ft.Colors.BLACK),
    )

    # ---------------- PANELES ----------------

    # Panel izquierdo: encabezado, botones de acción, campo de proveedor
    # y tabla de productos con scroll automático.
    panel_izquierdo = ft.Container(
        expand=True,
        bgcolor=ft.Colors.WHITE,
        border=ft.Border.all(1, ft.Colors.BLACK),
        border_radius=10,
        padding=20,
        content=ft.Column(
            [
                # Encabezado: título y número de compra
                ft.Row([ft.Text("Nueva compra", weight="bold", size=17), numeroCompra], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                # Fila de botones principales
                ft.Row([btn_nueva_compra, btn_buscar_producto, btn_buscar_proveedor, btn_crear_pc], spacing=5),
                ft.Divider(),
                # Fila con título "Productos agregados" y campo de proveedor
                ft.Row([ft.Text("Productos agregados", size=15, weight="bold"), nombreProveedor], spacing=20, alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                # Tabla con scroll automático
                ft.Container(expand=True, border_radius=10, content=ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, controls=[ft.Row(scroll=ft.ScrollMode.AUTO, controls=[tabla_productos])]))
            ],
            expand=True,
            spacing=20
        )
    )

    # Panel derecho: resumen de compra, información de compra consultada
    # y botones de acción secundarios. Ancho fijo de 230px.
    panel_derecho = ft.Container(
        width=230,
        bgcolor=ft.Colors.WHITE,
        border=ft.Border.all(1, ft.Colors.BLACK),
        border_radius=10,
        padding=20,
        content=ft.Column(
            [
                # Título del resumen
                ft.Text("Resumen de compra", weight="bold", size=17),
                # Totales calculados dinámicamente
                subtotal,
                descuento,
                ft.Divider(),
                total,
                ft.Divider(),

                # Campos visibles solo en modo consulta
                fechaCompra,
                usuarioCompra,

                ft.Divider(),
                # Botones de acción (cada uno centrado en su fila)
                ft.Row([btn_confirmar], spacing=10, alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Row([btn_consultar], spacing=10, alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Row([btn_imprimir_consulta], spacing=10, alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Row([btn_borrar_compra], spacing=10, alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER)
            ],
            spacing=20
        )
    )

    # ---------------- LAYOUT ----------------

    # Layout principal: barra superior + cuerpo dividido en dos paneles
    pagina.add(
        ft.Column(
            [
                # Barra superior: logo, título, usuario, reloj y botón volver
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
                # Cuerpo principal: panel izquierdo (tabla) + panel derecho (resumen)
                ft.Row([panel_izquierdo, panel_derecho], expand=True, spacing=10, alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START)
            ],
            expand=True,
            spacing=0
        )
    )

    # Cargar la primera compra guardada al iniciar la vista
    cargar_lista_compras()

    # Registrar handler de atajos de teclado
    pagina.on_keyboard_event = teclado

    # Renderizar la interfaz
    pagina.update()

    # Iniciar tarea asíncrona del reloj
    pagina.run_task(actualizar_hora)
