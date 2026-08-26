import flet as ft
from datetime import datetime
import asyncio
from utils.buscarProducto import buscar_producto_view
from utils.buscarCliente import buscar_cliente_view
from controllers import remisionController as remision_controller
from utils.crearP_C import Crear
from utils.confirmacion import confirmar_view
from utils.abrirNuevaVentana import abrir_nueva_instancia
from utils.notificaciones import mostrar_notificacion

# =========================================================
# VISTA PRINCIPAL PARA BUSCAR Y REALIZAR REMISIONES
# =========================================================
# Este módulo contiene la función `remision()` que construye la
# interfaz gráfica completa del módulo de remisiones del sistema POS.
#
# FUNCIONALIDADES:
#   - Agregar productos a la tabla de remisión desde el buscador (F3)
#   - Seleccionar cliente para la remisión (F1)
#   - Editar cantidad de cada producto inline (click en celda)
#   - Contar productos y cantidad total (sin cálculo de precios)
#   - Generar remisión con selección de tipo/motivo en diálogo modal
#   - Campo de notas opcional para tipo "Retiro Transformación"
#   - Consultar remisiones guardadas y navegar entre ellas (F6/F7)
#   - Anular remisiones existentes (solo admin/Aprendiz con permisos)
#   - Imprimir una remisión ya consultada
#   - Crear nuevos productos o clientes desde un diálogo (F8)
#   - Alternar entre crear nueva remisión en la misma ventana o en una nueva (F4)
#
# ATAJOS DE TECLADO:
#   F1  → Buscar cliente
#   F2  → Generar remisión (abre diálogo de tipo)
#   F3  → Buscar producto
#   F4  → Nueva remisión (1ra vez: limpia, 2da vez: abre nueva ventana)
#   F5  → Borrar/Anular remisión
#   F6  → Siguiente remisión guardada
#   F7  → Anterior remisión guardada
#   F8  → Crear producto o cliente
#   Escape → Volver al menú principal
#
# NAVEGACIÓN:
#   - ir_a_menu: vuelve al menú principal del sistema
#   - ir_a_main: vuelve a la pantalla principal (no se usa directamente aquí)
#
# DIFERENCIAS CON VENTAS/COMPRAS:
#   - NO maneja precios ni totales económicos, solo conteo de productos
#   - El resumen muestra: cantidad de productos, cantidad total, "Valor: No aplica"
#   - Al generar, se abre un diálogo para elegir el tipo de remisión
#   - El campo de notas aparece solo para el tipo "Retiro Transformación"
#   - El buscador de productos se abre con mostrar_precio=False
#   - El botón de generar abre un diálogo modal con opciones de tipo
#
# FLUJO TÍPICO:
#   1. El usuario selecciona un cliente (F1)
#   2. Agrega productos (F3) que se insertan en la tabla
#   3. Puede editar cantidades haciendo clic en las celdas
#   4. Presiona F2 o "Generar" → se abre diálogo de tipo de remisión
#   5. Selecciona tipo (Retiro Transformación, etc.) y opcionalmente escribe notas
#   6. Se genera el PDF y la remisión se guarda en la base de datos
#
def remision(pagina: ft.Page, ir_a_main, ir_a_menu, usuario):
#------------------- DATOS -----------------

    # Lista de productos agregados a la remisión actual.
    # Cada producto es un diccionario con: id, nombre, cantidad, unidad,
    # precio, subtotal, lugar, etc.
    productos = []

    # Cliente seleccionado actualmente para la remisión.
    # Se asigna cuando el usuario elige un cliente desde el buscador (F1).
    cliente_actual = None

    # Lista de remisiones cargadas desde la base de datos para navegación (F6/F7)
    remisiones = []

    # Índice actual dentro de la lista de remisiones (-1 = ninguna cargada)
    index_remision = -1

    # Bandera de modo consulta: True cuando se muestra una remisión ya guardada.
    # En modo consulta no se pueden agregar/modificar productos.
    modo_consulta = False

    # ID de la remisión que se está consultando actualmente
    id_remision_actual = None

    # Control para alternar entre crear una nueva remisión en la misma ventana o abrir otra ventana.
    # Primera pulsación de F4 limpia; segunda pulsación abre nueva ventana.
    f4_siguiente_abrir_ventana = True

    # Obtener las opciones de tipo de remisión disponibles desde el controlador
    # (ej: "Retiro Transformación", "Entrega", etc.)
    opciones_remision = remision_controller.obtener_opciones_remision()
#-------------------------------------------

    # Limpiar la página y configurar el tamaño de ventana
    pagina.clean()

    # Tamaño de la ventana para la pantalla de remisiones
    pagina.window.width = 1500
    pagina.window.height = 800

    # Centrar el contenido de la página
    pagina.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    pagina.vertical_alignment = ft.MainAxisAlignment.CENTER

    # ---------------- CAMPOS ----------------

    # Logo del SENA en la esquina superior derecha
    logo = ft.Image(
        src="Logo_sena.png",
        width=50,
        height=50
    )

    # Título principal del sistema
    titulo = ft.Text("Sistema POS", size=15, weight="bold")

    # Textos del resumen de remisión en el panel derecho.
    # En remisiones NO se manejan precios, solo conteo y cantidades.
    subtotal  = ft.Text("Productos: 0", weight="bold")
    descuento = ft.Text("Cantidad total: 0", weight="bold")
    total     = ft.Text("Valor: No aplica", weight="bold")

    # Reloj en tiempo real en la barra superior
    fecha_hora  = ft.Text("", size=15)

    # Campo de solo lectura que muestra el cliente seleccionado
    nombreCliente = ft.TextField(label="Cliente seleccionado ", width=260, read_only=True)

    # Información del usuario logueado en la barra superior
    texto_usuario = ft.Text(f"Usuario: {usuario['usuario']}", size=15, weight="bold")
    texto_nombre  = ft.Text(f"Nombre: {usuario['nombre']}",  size=15, weight="bold")

    # Número de remisión actual
    numeroFactura = ft.Text("Numero de remision: 0001", size=17, weight="bold")

    # Campo de notas multilinea.
    # Solo se muestra cuando el tipo de remisión es "Retiro Transformación"
    # y también se muestra al cargar una remisión guardada que tenga notas.
    campo_notas = ft.TextField(
        label="Notas",
        width=400,
        multiline=True,
        max_lines=3,
        visible=False
    )

    # Contenedor que muestra la nota de una remisión consultada.
    # Oculto por defecto, se muestra en modo consulta si hay notas.
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

    # Texto de fecha de la remisión (visible solo en modo consulta)
    fecha_remision = ft.Text(
        "",
        size=13,
        weight="bold",
        visible=False
    )

    # Texto del usuario que creó la remisión (visible solo en modo consulta)
    usuarioRemision = ft.Text(
        "",
        size=13,
        weight="bold",
        visible=False
    )

    # ---------------- FUNCIONES ----------------

    # Actualiza el resumen de la remisión en el panel derecho.
    # En remisiones solo se muestran conteos (no hay cálculo económico).
    def actualizar_totales():

        resumen = remision_controller.calcular_resumen(productos)

        # En remision no se manejan precios, solo conteo y cantidades.
        subtotal.value = f"Productos: {resumen['productos']}"
        descuento.value = f"Cantidad total: {resumen['cantidad_total']}"
        total.value = "Valor: No aplica"
        pagina.update()

    # Agrega un producto seleccionado desde el buscador a la tabla de remisión.
    # El producto se procesa a través del controlador y luego se inserta
    # una nueva fila en la tabla.
    def agregar_producto_a_tabla(producto):

        # No agregar en modo consulta
        if modo_consulta:
            return

        # Obtener el stock actual del producto
        stock_actual = producto.get("stock", 0)

        # Cantidad que el usuario quiere agregar
        cantidad = producto.get("cantidad", 1)

        # Agregar el producto a la lista a través del controlador
        producto = remision_controller.agregar_producto_a_remision(productos, producto)

        cantidad_texto = remision_controller.formatear_cantidad(
            cantidad
        )

        # Insertar nueva fila al final de la tabla
        tabla_productos.rows.append(
            ft.DataRow(
                cells=[
                    # Codigo del producto
                    ft.DataCell(ft.Text(str(producto.get('id', '-')))),
                    # Nombre del producto
                    ft.DataCell(ft.Text(producto.get('nombre', 'Sin nombre'))),
                    # Cantidad (editable al hacer clic)
                    ft.DataCell(
                    ft.TextButton(
                        content=ft.Text(cantidad_texto),
                        on_click=lambda e, idx=productos.index(producto): editar_cantidad(idx)
                    )
                ),
                    # Unidad de medida
                    ft.DataCell(ft.Text(str(producto.get('unidad', 'UND')))),
                    # Precio unitario (informativo, no se usa para totales)
                    ft.DataCell(ft.Text(f"${producto.get('precio', 0):,.2f}")),
                    # Subtotal (informativo)
                    ft.DataCell(ft.Text(f"${producto.get('subtotal', 0):,.2f}")),
                    # Empresa/lugar del producto
                    ft.DataCell(ft.Text(str(producto.get('lugar', '-')))),
                    # Botón X para eliminar producto
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
        # Actualizar el conteo de productos
        actualizar_totales()
        tabla_productos.update()

    # Tarea asíncrona que actualiza el reloj cada segundo.
    # Se ejecuta como tarea de fondo con run_task().
    # Se detiene automáticamente cuando la vista ya no está activa.
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
                # Coloco la fecha y hora actual en formato 12 horas
                fecha_hora.value = datetime.now().strftime("%d/%m/%Y %I:%M:%S %p")
                fecha_hora.update()
            except RuntimeError:
                # Si la vista ya no existe corto el ciclo
                break
            await asyncio.sleep(1)

    # Callback que se ejecuta después de seleccionar el tipo de remisión
    # y confirmar la generación. Guarda la remisión en la BD y genera el PDF.
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
            mostrar_notificacion(pagina, "No fue posible guardar la remisión.", error=True)
            return

        print(f"Remision {resultado['id_remision']} guardada")
        print(f"PDF: {resultado['ruta_pdf']}")
        # Limpiar la vista después de generar exitosamente
        limpiar_factura()
        mostrar_notificacion(
            pagina, f"Remisión #{resultado['id_remision']} guardada correctamente."
        )

    # ---------------- GENERAR REMISIÓN (F2) ----------------

    # Variable para guardar la referencia al diálogo modal de tipo de remisión.
    dialog_remision = None

    # Abre el diálogo modal de selección de tipo de remisión.
    # El usuario elige entre las opciones configuradas (ej: "Retiro Transformación")
    # y puede agregar notas opcionales. Al confirmar se genera el PDF.
    def facturar():
        nonlocal dialog_remision

        # No generar en modo consulta
        if modo_consulta:
            print("No se puede generar remision en modo consulta")
            return
        # No generar sin productos
        if not productos:
            print("No hay productos en la remision")
            return

        # Guardar el handler de teclado actual (de remision.py)
        # para restaurarlo cuando se cierre el diálogo
        teclado_anterior = pagina.on_keyboard_event

        # Función para cerrar el diálogo y restaurar el teclado
        def cerrar_dialogo(e=None):
            dialog_remision.open = False
            # Restaurar el teclado anterior solo si no fue reemplazado
            if pagina.on_keyboard_event == teclado_dialogo:
                pagina.on_keyboard_event = teclado_anterior
            pagina.update()

        # Crear grupo de radio buttons con los tipos de remisión disponibles
        tipo_remision = ft.RadioGroup(
            value="Retiro Transformacion",
            content=ft.Column(
                [ft.Radio(value=opcion, label=opcion) for opcion in opciones_remision],
                spacing=6
            )
        )

        # Callback cuando cambia la selección de tipo de remisión.
        # Muestra el campo de notas solo para "Retiro Transformación".
        def seleccionar_tipo(e):
            campo_notas.visible = (e.control.value == "Retiro Transformacion")
            campo_notas.value = ""  # Limpiar notas al cambiar tipo
            pagina.update()

        tipo_remision.on_change = seleccionar_tipo

        # Función para generar la remisión (se ejecuta al hacer clic en "Generar PDF")
        def generar(e=None):
            cerrar_dialogo()
            # Obtener notas solo si el campo está visible
            notas = campo_notas.value if campo_notas.visible else ""
            confirmar_remision(tipo_remision.value, notas)

        # Inicializar campo de notas para el diálogo
        campo_notas.value = ""
        campo_notas.visible = True

        # Construir el diálogo modal con las opciones de tipo y campo de notas
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
                # Botón cancelar
                ft.TextButton("Cancelar", on_click=cerrar_dialogo),
                # Botón generar PDF (verde, con autofocus)
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

        # Teclado temporal exclusivo del diálogo.
        # Escape cierra, Enter genera la remisión.
        async def teclado_dialogo(e: ft.KeyboardEvent):
            if e.key == "Escape":
                cerrar_dialogo()
            elif e.key == "Enter":
                generar()

        # Reemplazar temporalmente el handler de teclado principal
        pagina.on_keyboard_event = teclado_dialogo

        # Mostrar el diálogo como overlay
        pagina.overlay.append(dialog_remision)
        dialog_remision.open = True
        pagina.update()


    # Permite editar la cantidad de un producto haciendo clic en la celda.
    # Reemplaza el texto por un TextField editable. Al presionar Enter
    # se guarda el nuevo valor y se actualiza la tabla.
    def editar_cantidad(index):

        # Los Aprendices no pueden editar en modo consulta
        if modo_consulta and usuario.get("rol", "") == "Aprendiz":
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
                # Actualizar cantidad en el controlador
                remision_controller.actualizar_cantidad_producto_remision(producto, nueva_cantidad)
                # Restaurar celda de cantidad con valor formateado
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
                # Actualizar celda de subtotal
                tabla_productos.rows[index].cells[5] = ft.DataCell(
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

    # Elimina un producto de la tabla de remisión por su índice.
    # Reconstruye toda la tabla desde cero para mantener los índices correctos.
    def eliminar_producto(index):

        # No eliminar en modo consulta
        if modo_consulta:
            return

        # Quitar de la lista
        productos.pop(index)

        # Reconstruir todas las filas de la tabla
        tabla_productos.rows.clear()

        for i, p in enumerate(productos):
            cantidad_texto = remision_controller.formatear_cantidad(
                p["cantidad"]
            )
            tabla_productos.rows.append(
                ft.DataRow(
                    cells=[
                        # Codigo
                        ft.DataCell(
                            ft.Text(str(p.get("id", "-")))
                        ),
                        # Nombre
                        ft.DataCell(
                            ft.Text(p.get("nombre", "Sin nombre"))
                        ),
                        # Cantidad (editable)
                        ft.DataCell(
                            ft.TextButton(
                                content=ft.Text(cantidad_texto),
                                on_click=lambda e, idx=i: editar_cantidad(idx)
                            )
                        ),
                        # Unidad
                        ft.DataCell(
                            ft.Text(str(p.get("unidad", "UND")))
                        ),
                        # Precio
                        ft.DataCell(
                            ft.Text(f"${p.get('precio', 0):,.2f}")
                        ),
                        # Subtotal
                        ft.DataCell(
                            ft.Text(f"${p.get('subtotal', 0):,.2f}")
                        ),
                        # Empresa
                        ft.DataCell(
                            ft.Text(str(p.get('lugar', '-')))
                        ),
                        # Botón X para eliminar
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

        # Recalcular totales después de eliminar
        actualizar_totales()

        pagina.update()


    # Resetea toda la vista a su estado inicial para comenzar una nueva remisión.
    # Limpia productos, cliente, tabla, campos de texto, notas y totales.
    def limpiar_factura():

        nonlocal productos
        nonlocal modo_consulta
        nonlocal id_remision_actual
        nonlocal cliente_actual

        # Vaciar lista de productos y cliente
        productos = []
        cliente_actual = None

        # Limpiar filas de la tabla
        tabla_productos.rows.clear()

        # Ocultar campos de usuario de la remisión consultada
        usuarioRemision.value = ""
        usuarioRemision.visible = False

        # Vaciar campo de cliente
        nombreCliente.value = ""

        # Resetear número de remisión
        numeroFactura.value = "Numero de remision: Nueva"

        # Ocultar nota de remisión consultada
        nota_remision.visible = False
        nota_remision.content.controls[1].value = ""

        # Ocultar fecha de remisión consultada
        fecha_remision.value = ""
        fecha_remision.visible = False

        # Recalcular totales (quedará en 0)
        actualizar_totales()

        # Salir del modo consulta
        modo_consulta = False
        id_remision_actual = None

        # Ocultar botón de imprimir (solo visible en modo consulta)
        btn_imprimir_consulta.visible = False

        pagina.update()

    # Carga una remisión existente desde la base de datos por su ID.
    # Reconstruye la tabla, muestra datos del cliente, usuario, fecha,
    # notas y el tipo de remisión.
    # Retorna True si se cargó correctamente, False si hubo error.
    def cargar_remision_actual(id_remision):
        nonlocal productos, modo_consulta, id_remision_actual

        # Solicitar datos al controlador
        datos = remision_controller.cargar_remision(id_remision)
        if not datos:
            return False

        remision_actual = datos["remision"]

        # Mostrar las notas de la remisión en el campo de notas
        campo_notas.value = remision_actual.get("notas", "")
        campo_notas.visible = True

        # Mostrar fecha de la remisión
        fecha = remision_actual.get("fecha")

        if fecha:
            fecha_remision.value = (
                "Fecha: " +
                fecha.strftime("%d/%m/%Y %H:%M:%S")
            )
            fecha_remision.visible = True

        # Mostrar quién realizó la remisión
        usuarioRemision.value = (
            f"Hecha por: {remision_actual.get('nombre_usuario', 'Sin usuario')}"
        )
        usuarioRemision.visible = True

        cliente = datos["cliente"]
        productos = datos["productos"]

        # Limpiar y reconstruir la tabla
        tabla_productos.rows.clear()
        for i, producto in enumerate(productos):
            cantidad_texto = remision_controller.formatear_cantidad(
                producto["cantidad"]
            )
            tabla_productos.rows.append(
                ft.DataRow(
                    cells=[
                        # Codigo
                        ft.DataCell(
                            ft.Text(str(producto.get("id", "-")))
                        ),
                        # Nombre
                        ft.DataCell(
                            ft.Text(producto.get("nombre", "Sin nombre"))
                        ),
                        # Cantidad (editable)
                        ft.DataCell(
                            ft.TextButton(
                                content=ft.Text(cantidad_texto),
                                on_click=lambda e, idx=i: editar_cantidad(idx)
                            )
                        ),
                        # Unidad
                        ft.DataCell(
                            ft.Text(producto.get("unidad", "UND"))
                        ),
                        # Precio
                        ft.DataCell(
                            ft.Text(
                                f"${producto.get('precio', 0):,.2f}"
                            )
                        ),
                        # Subtotal
                        ft.DataCell(
                            ft.Text(
                                f"${producto.get('subtotal', 0):,.2f}"
                            )
                        ),
                        # Empresa
                        ft.DataCell(
                            ft.Text(str(producto.get("lugar", "-")))
                        ),
                        # Botón X (deshabilitado en modo consulta)
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
        # Mostrar nombre del cliente
        nombreCliente.value = (
            f"{cliente['nombre']} - {cliente['rol']}"
            if cliente else "Sin cliente"
        )
        # Mostrar número de remisión con el tipo incluido
        numeroFactura.value = (
            f"Numero de remision: "
            f"{id_remision:04d} - "
            f"{remision_actual['tipo_remision']}"
        )
        # Mostrar notas si existen
        notas = (remision_actual.get("notas") or "").strip()
        nota_remision.visible = bool(notas)
        nota_remision.content.controls[1].value = notas

        actualizar_totales()

        # Activar modo consulta
        modo_consulta = True
        id_remision_actual = id_remision

        # Mostrar botón de imprimir
        btn_imprimir_consulta.visible = True
        pagina.update()
        return True
    
    # Genera el PDF de la remisión consultada y lo envía a imprimir.
    # Solo funciona si hay una remisión cargada en modo consulta.
    def imprimir_remision_consultada():
        if not modo_consulta or id_remision_actual is None:
            print("Primero consulta una remision para imprimirla")
            return

        # Delegar al controlador la generación del PDF
        resultado = remision_controller.imprimir_remision_consultada(
            id_remision_actual,
            usuario
        )

        if not resultado:
            print("No se pudo imprimir la remision consultada")
            return

        print(f"Remision {id_remision_actual} enviada a imprimir")

    # Maneja la pulsación de F4 para nueva remisión.
    # Primera vez: limpia la remisión actual en la misma ventana.
    # Segunda vez: abre una nueva ventana con la vista de remisiones.
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
        # Marcar que la próxima pulsación abrirá ventana nueva
        f4_siguiente_abrir_ventana = False

    # Navega a la siguiente remisión guardada (F6).
    # Usa navegación circular.
    def siguiente_remision():
        nonlocal index_remision
        if not remisiones:
            cargar_lista_remisiones()
            return
        index_remision = (index_remision + 1) % len(remisiones)
        cargar_remision_actual(remisiones[index_remision]['id_remision'])

    # Navega a la remisión anterior guardada (F7).
    # Usa navegación circular.
    def anterior_remision():
        nonlocal index_remision
        if not remisiones:
            cargar_lista_remisiones()
            return
        index_remision = (index_remision - 1) % len(remisiones)
        cargar_remision_actual(remisiones[index_remision]['id_remision'])

    # Carga la lista completa de remisiones desde la base de datos
    # y muestra la primera de la lista.
    def cargar_lista_remisiones():
        nonlocal remisiones, index_remision
        remisiones = remision_controller.listar_remisiones()
        if remisiones:
            index_remision = 0
            cargar_remision_actual(remisiones[0]['id_remision'])
        else:
            limpiar_factura()

    # Borra o anula la remisión actual según el modo:
    # - Modo nueva remisión: simplemente limpia la tabla
    # - Modo consulta: anula la remisión (requiere permisos)
    # Muestra un diálogo de confirmación antes de ejecutar la acción.
    def borrar_remision_actual():
        nonlocal index_remision
        # -----------------------------
        # NUEVA REMISIÓN
        # -----------------------------
        if not modo_consulta:
            mensaje = "¿Deseas limpiar la remision actual?"
        # -----------------------------
        # MODO CONSULTA - ANULAR REMISIÓN
        # -----------------------------
        else:
            # Los Aprendices no tienen permisos para anular
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
        # CONFIRMACIÓN GENERAL
        # -----------------------------
        def on_confirmar(confirmado):
            if not confirmado:
                return
            # LIMPIAR - modo nueva remisión
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
            # ANULAR - modo consulta
            if id_remision_actual is None:
                return
            if remision_controller.borrar_remision(id_remision_actual):
                snack = ft.SnackBar(
                    content=ft.Text("Remision anulada"),
                    bgcolor=ft.Colors.RED
                )
                pagina.overlay.append(snack)
                snack.open = True
                # Recargar lista después de anular
                remisiones.clear()
                index_remision = -1
                cargar_lista_remisiones()

        # Mostrar diálogo de confirmación
        dialog = confirmar_view(
            pagina,
            mensaje,
            on_confirmar
        )
        pagina.overlay.append(dialog)
        dialog.open = True
        pagina.update()

    # Abre el diálogo de búsqueda de productos (F3).
    # Se pasa mostrar_precio=False porque en remisiones no se manejan precios
    # en la búsqueda (aunque el precio sí se muestra en la tabla).
    def buscar_producto():
        if modo_consulta:
            return
        dialog = buscar_producto_view(pagina, agregar_producto_a_tabla, mostrar_precio=False)
        pagina.overlay.append(dialog)
        dialog.open = True
        pagina.update()

    # Callback que se ejecuta cuando el usuario selecciona un cliente
    # desde el diálogo de búsqueda. Actualiza el campo de cliente en pantalla.
    def seleccionar_cliente(cliente):
        nonlocal cliente_actual
        cliente_actual = cliente
        nombre = cliente.get("nombre", "Sin nombre")
        rol = cliente.get("rol", "Sin rol")
        nombreCliente.value = f"{nombre} - {rol}"
        pagina.update()
    

    # Abre el diálogo de búsqueda de clientes (F1).
    # Se pasa `seleccionar_cliente` como callback.
    def buscar_cliente():
        if modo_consulta:
            return
        dialog = buscar_cliente_view(pagina, seleccionar_cliente)
        pagina.overlay.append(dialog)
        dialog.open = True
        pagina.update()

    # Abre el diálogo de creación rápida de productos o clientes (F8).
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

    # Handler principal de atajos de teclado para la vista de remisiones.
    async def teclado(e: ft.KeyboardEvent):

        # F2 → Generar remisión (abre diálogo de tipo)
        if e.key == "F2":
            facturar()

        # Escape → Volver al menú principal
        elif e.key == "Escape":
            ir_a_menu(usuario)

        # F3 → Abrir búsqueda de productos
        elif e.key == "F3":
            buscar_producto()

        # F1 → Abrir búsqueda de clientes
        elif e.key == "F1":
            buscar_cliente()

        # F4 → Nueva remisión (limpiar o abrir nueva ventana)
        elif e.key == "F4":
            nueva_remision()

        # F5 → Borrar/Anular remisión actual
        elif e.key == "F5":
            borrar_remision_actual()

        # F6 → Siguiente remisión guardada
        elif e.key == "F6":
            siguiente_remision()

        # F7 → Anterior remisión guardada
        elif e.key == "F7":
            anterior_remision()
        
        # F8 → Crear producto o cliente
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

    # Botón para generar la remisión (atajo: F2).
    # Color verde para indicar acción de confirmación.
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

    # Botón para abrir búsqueda de clientes (atajo: F1)
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
    
    # Botón para crear producto o cliente (atajo: F8)
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

    # Botón para nueva remisión (atajo: F4).
    # Primera pulsación: limpia. Segunda: abre nueva ventana.
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

    # Botón para cargar y consultar remisiones guardadas (atajos: F6/F7)
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

    # Botón para imprimir la remisión consultada.
    # Solo visible en modo consulta. Color azul para diferenciar.
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

    # Botón para borrar/anular remisión (atajo: F5).
    # Color rojo para indicar acción destructiva.
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

    # Tabla principal de productos de la remisión.
    # Columnas: Codigo, Producto, Cantidad (editable), Unidad,
    #           Precio, Subtotal, Empresa, Acciones (botón X).
    # A diferencia de ventas/compras, NO hay columna de descuento.
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

    # Panel izquierdo: encabezado, botones de acción, campo de cliente
    # y tabla de productos con scroll automático.
    panel_izquierdo = ft.Container(
        expand=True,
        bgcolor=ft.Colors.WHITE,
        border=ft.Border.all(1, ft.Colors.BLACK),
        border_radius=10,
        padding=20,
        content=ft.Column(
            [
                # Encabezado: título "Nueva remision" y número
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

                # Fila de botones principales
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
                # Fila con título y campo de cliente
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
                # Tabla con scroll automático vertical y horizontal
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

    # Panel derecho: resumen de remisión, nota, fecha, usuario,
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
                ft.Text("Resumen de remision", weight="bold", size=17),

                # Contadores (no precios)
                subtotal,
                descuento,

                ft.Divider(),

                # Nota visible solo si hay notas cargadas
                nota_remision,
                # Fecha visible solo en modo consulta
                fecha_remision,
                # Usuario que hizo la remisión
                usuarioRemision,

                ft.Divider(),

                # Botón generar remisión (verde, centrado)
                ft.Row(
                    btn_facturar,
                    spacing=10,
                    alignment=ft.MainAxisAlignment.CENTER,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                ),
                # Botón consultar remisiones guardadas
                ft.Row(
                    btn_consultar,
                    spacing=10,
                    alignment=ft.MainAxisAlignment.CENTER,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                ),
                # Botón imprimir (oculto por defecto)
                ft.Row(
                    btn_imprimir_consulta,
                    spacing=10,
                    alignment=ft.MainAxisAlignment.CENTER,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                ),
                # Botón borrar/anular (rojo)
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
                # Cuerpo principal: panel izquierdo (tabla) + panel derecho (resumen)
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

    # Registrar handler de atajos de teclado
    pagina.on_keyboard_event = teclado


    # Cargar la primera remisión guardada al iniciar la vista
    cargar_lista_remisiones()

    # Renderizar la interfaz
    pagina.update()

    # Iniciar tarea asíncrona del reloj
    pagina.run_task(actualizar_hora)