import flet as ft
from datetime import datetime
import asyncio
from utils.buscarProducto import buscar_producto_view
from utils.buscarCliente import buscar_cliente_view
from utils.entregarApartado import entregar_apartado_view
from controllers import ventasController as ventas_controller
from utils.metodoPago import metodo_pago_view
from utils.crearP_C import Crear
from utils.confirmacion import confirmar_view
from utils.abrirNuevaVentana import abrir_nueva_instancia
from utils.notificaciones import mostrar_notificacion


# =========================================================
# VISTA PRINCIPAL PARA BUSCAR Y REALIZAR VENTAS
# =========================================================
# Este módulo contiene la función principal `vender()` que construye
# la interfaz gráfica completa del módulo de ventas del sistema POS.
#
# FUNCIONALIDADES:
#   - Agregar productos a la tabla de venta desde el buscador (F3)
#   - Seleccionar cliente para la factura (F1)
#   - Editar cantidad y descuento de cada producto inline (click en celda)
#   - Calcular subtotal, descuento y total en tiempo real
#   - Confirmar la venta y generar el PDF de la factura
#   - Consultar facturas guardadas y navegar entre ellas (F6/F7)
#   - Anular facturas existentes (solo admin/Aprendiz con permisos)
#   - Imprimir una factura ya consultada
#   - Crear nuevos productos o clientes desde un diálogo (F8)
#   - Alternar entre crear nueva factura en la misma ventana o en una nueva (F4)
#
# ATAJOS DE TECLADO:
#   F1  → Buscar cliente
#   F2  → Facturar (confirmar venta)
#   F3  → Buscar producto
#   F4  → Nueva factura (1ra vez: limpia, 2da vez: abre nueva ventana)
#   F5  → Borrar/Anular factura
#   F6  → Siguiente factura guardada
#   F7  → Anterior factura guardada
#   F8  → Crear producto o cliente
#   Escape → Volver al menú principal
#
# NAVEGACIÓN:
#   - ir_a_menu: vuelve al menú principal del sistema
#   - ir_a_main: vuelve a la pantalla principal (no se usa directamente aquí)
#
# FLUJO TÍPICO:
#   1. El usuario selecciona un cliente (F1)
#   2. Agrega productos (F3) que se insertan en la tabla
#   3. Puede editar cantidades y descuentos haciendo clic en las celdas
#   4. Presiona F2 o el botón "Facturar" para elegir método de pago
#   5. Se genera el PDF y la factura se guarda en la base de datos
#
def vender(pagina: ft.Page, ir_a_main, ir_a_menu, usuario):
#------------------- DATOS -----------------

    # Lista donde se guardan los productos agregados a la venta.
    # Cada elemento es un diccionario con: id, nombre, cantidad, unidad,
    # precio, descuento, subtotal, lugar, etc.
    productos = []
    print (f"Usuario en vender: {usuario}")

    # Cliente seleccionado actualmente para la factura.
    # Se asigna cuando el usuario elige un cliente desde el buscador (F1).
    # Es un diccionario con nombre, rol, id, etc.
    cliente_actual = None

    # Apartado web que se está entregando en esta factura.
    # None = venta directa de pasillo; int = id del apartado en entrega (F9).
    # Al entregarse, se precarga el producto reservado y al facturar NO se
    # descuenta limite_venta (ya se restó en la web) y el apartado pasa a 'entregado'.
    apartado_actual = None

    # Lista de facturas cargadas desde la base de datos para navegación (F6/F7)
    facturas = []

    # Índice actual dentro de la lista de facturas cargadas.
    # Se usa para saber qué factura se está mostrando (-1 = ninguna).
    index_factura = -1

    # Bandera que indica si estamos en modo consulta (factura ya guardada)
    # o en modo edición (factura nueva en proceso).
    # En modo consulta: no se pueden agregar/eliminar/editar productos,
    # solo se puede imprimir o anular.
    modo_consulta = False

    # ID de la factura que se está consultando actualmente.
    # None si no hay factura cargada.
    id_factura_actual = None

    # Control para alternar entre crear una nueva factura en la misma ventana o abrir otra ventana.
    # Empieza en True para que la primera pulsación de F4 limpie la factura actual.
    # La segunda pulsación abre una nueva ventana con la misma vista.
    f4_siguiente_abrir_ventana = True
#-------------------------------------------

    # Limpio la consola y la pantalla para empezar la vista desde cero
    pagina.clean()

    # Tamaño de la ventana para la pantalla de ventas
    pagina.window.width = 1500
    pagina.window.height = 800

    # Centro todo el contenido en la página
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

    # Textos del resumen de venta en el panel derecho.
    # Se actualizan dinámicamente cada vez que se agrega/modifica/elimina un producto.
    subtotal  = ft.Text("Subtotal: $0",  weight="bold")
    descuento = ft.Text("Descuento: $0", weight="bold")
    total     = ft.Text("Total: $0",     weight="bold")

    # Reloj en tiempo real que se muestra en la barra superior
    fecha_hora  = ft.Text("", size=15)

    # Campo de solo lectura que muestra el cliente seleccionado actualmente
    nombreCliente = ft.TextField(label="Cliente seleccionado ", width=260, read_only=True)

    # Información del usuario logueado que se muestra en la barra superior
    texto_usuario = ft.Text(f"Usuario: {usuario['usuario']}", size=15, weight="bold")
    texto_nombre  = ft.Text(f"Nombre: {usuario['nombre']}",  size=15, weight="bold")

    # Número de factura actual (se actualiza al cargar o crear facturas)
    numeroFactura = ft.Text("Número de factura: 0001", size=17, weight="bold")

    # Campos de información de la factura consultada (ocultos por defecto,
    # se muestran solo cuando se carga una factura existente)
    texto_fecha = ft.Text("", size=13, weight="bold", visible=False)
    usuarioFactura = ft.Text("", size=13, weight="bold", visible=False)
    # Columna para las notas (una línea por empresa si aplica)
    notaFactura = ft.Column([], spacing=4, visible=False)

    # ---------------- FUNCIONES ----------------

    # Recalcula el subtotal, descuento y total de la venta
    # consultando el controlador con la lista actual de productos.
    def actualizar_totales():

        resumen = ventas_controller.calcular_resumen_venta(productos)

        subtotal.value = f"Subtotal: ${resumen['subtotal']:,.2f}"
        descuento.value = f"Descuento: ${resumen['descuento']:,.2f}"
        total.value = f"Total: ${resumen['total']:,.2f}"
        pagina.update()

    # Permite editar el descuento de un producto haciendo clic en la celda.
    # Se reemplaza el texto por un TextField editable; al presionar Enter
    # se guarda el nuevo descuento y se actualiza la fila y los totales.
    # Los Aprendices no pueden editar descuentos en modo consulta.
    def editar_descuento(index):

        # Bloquear edición si es Aprendiz en modo consulta
        if modo_consulta and usuario.get("rol", "") == "Aprendiz":
            return

        producto = productos[index]
        # Crear campo de texto temporal con el descuento actual
        campo = ft.TextField(
            value=str(producto.get("descuento", 0)),
            autofocus=True,
            width=120
        )
        def guardar_descuento(e):
            try:
                nuevo_descuento = float(campo.value)
                # Actualizar el descuento en el controlador (recalcula subtotal interno)
                ventas_controller.actualizar_descuento_producto(producto, nuevo_descuento)
                # Restaurar la celda de descuento con el nuevo valor como botón clickeable
                tabla_productos.rows[index].cells[5] = ft.DataCell(
                    ft.TextButton(
                        content=ft.Text(
                            f"{producto['descuento']:,.2f}%"
                        ),
                        on_click=lambda e: editar_descuento(index)
                    )
                )
                # Actualizar la celda de subtotal con el nuevo valor
                tabla_productos.rows[index].cells[6] = ft.DataCell(
                    ft.Text(
                        f"${producto['subtotal']:,.2f}"
                    )
                )
                # Recrear la columna de acciones por si cambió el estado del stock
                tabla_productos.rows[index].cells[8] = crear_celda_acciones(
                    producto,
                    index
                )
                actualizar_totales()
                pagina.update()
            except:
                pass
        # Reemplazar la celda de descuento con el campo editable
        tabla_productos.rows[index].cells[5] = ft.DataCell(campo)
        campo.on_submit = guardar_descuento
        pagina.update()


    # Permite editar la cantidad de un producto haciendo clic en la celda.
    # Funciona igual que editar_descuento: reemplaza el texto por un TextField
    # y al presionar Enter guarda el nuevo valor.
    def editar_cantidad(index):

        # Bloquear edición si es Aprendiz en modo consulta
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
                # Actualizar cantidad en el controlador (recalcula subtotal)
                ventas_controller.actualizar_cantidad_producto(producto, nueva_cantidad)
                # Restaurar la celda de cantidad con el valor formateado
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
                # Actualizar la celda de subtotal
                tabla_productos.rows[index].cells[6] = ft.DataCell(
                    ft.Text(
                        f"${producto['subtotal']:,.2f}"
                    )
                )
                # Recrear acciones por si cambió el stock
                tabla_productos.rows[index].cells[8] = crear_celda_acciones(
                    producto,
                    index
                )
                actualizar_totales()
                pagina.update()

            except:
                pass
        # Reemplazar celda de cantidad con campo editable
        tabla_productos.rows[index].cells[2] = ft.DataCell(campo)
        campo.on_submit = guardar
        pagina.update()

    # Delega al controlador el cálculo del stock restante
    # (stock disponible menos lo que ya se agregó a la venta)
    def obtener_stock_restante(producto):
        return ventas_controller.obtener_stock_restante(producto)

    # Formatea el stock para mostrarlo con decimales y signo
    def formatear_stock(stock):
        return ventas_controller.formatear_stock(stock)

    # Renderiza la celda de precio unitario de una fila. Si el producto tiene
    # una oferta vigente, muestra el precio original tachado, el precio final
    # (con oferta) y una etiqueta (badge) con el porcentaje de descuento.
    def crear_celda_precio(producto):
        precio_final = float(producto.get('precio', 0))
        original = float(producto.get('precio_original', precio_final))
        es_oferta = bool(producto.get('es_oferta'))

        if es_oferta and original > precio_final:
            badge = ft.Container(
                content=ft.Text(
                    f"-{producto.get('descuento_oferta', 0):.0f}%",
                    size=10,
                    weight="bold",
                    color=ft.Colors.WHITE
                ),
                bgcolor=ft.Colors.RED,
                padding=ft.Padding.symmetric(horizontal=4, vertical=1),
                border_radius=8,
            )
            return ft.DataCell(
                ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text(
                                    f"${original:,.2f}",
                                    size=11,
                                    color=ft.Colors.GREY,
                                    style=ft.TextStyle(
                                        decoration=ft.TextDecoration.LINE_THROUGH
                                    )
                                ),
                                ft.Text(
                                    f"${precio_final:,.2f}",
                                    weight="bold",
                                    color=ft.Colors.RED
                                ),
                            ],
                            spacing=0,
                            alignment=ft.MainAxisAlignment.CENTER,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER
                        ),
                        badge,
                    ],
                    spacing=6,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                )
            )
        return ft.DataCell(
            ft.Text(f"${precio_final:,.2f}")
        )

    # Crea la celda de acciones de cada fila: muestra un indicador de stock
    # negativo (en rojo) si se excedió el stock, y un botón X para eliminar
    # el producto de la venta.
    # parámetro deshabilitado: cuando True (modo consulta), el botón X no funciona.
    def crear_celda_acciones(producto, index, deshabilitado=False):
        stock_restante = obtener_stock_restante(producto)
        controles = []

        # Si el stock restante es negativo, mostrar advertencia en rojo
        if stock_restante < 0:
            controles.append(
                ft.Text(
                    formatear_stock(stock_restante),
                    color=ft.Colors.RED,
                    weight="bold",
                    size=12
                )
            )

        # Botón X para eliminar el producto de la tabla
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


    # Elimina un producto de la tabla de venta por su índice.
    # Reconstruye toda la tabla desde cero para mantener los índices correctos.
    # No funciona en modo consulta (factura ya guardada).
    def eliminar_producto(index):

        # En modo consulta no se permite eliminar
        if modo_consulta:
            return

        # Quitar el producto de la lista a través del controlador
        ventas_controller.quitar_producto_de_venta(productos, index)

        # Limpiar y reconstruir todas las filas de la tabla
        tabla_productos.rows.clear()

        for i, p in enumerate(productos):

            cantidad_texto = ventas_controller.formatear_cantidad(
                p["cantidad"]
            )

            # Agregar cada producto como una fila completa de la tabla
            tabla_productos.rows.append(
                ft.DataRow(
                    cells=[
                        # Columna 0: Código del producto
                        ft.DataCell(
                            ft.Text(str(p.get("id", "-")))
                        ),

                        # Columna 1: Nombre del producto
                        ft.DataCell(
                            ft.Text(p.get("nombre", "Sin nombre"))
                        ),

                        # Columna 2: Cantidad (clickeable para editar)
                        ft.DataCell(
                            ft.TextButton(
                                content=ft.Text(cantidad_texto),
                                on_click=lambda e, idx=i: editar_cantidad(idx)
                            )
                        ),

                        # Columna 3: Unidad de medida
                        ft.DataCell(
                            ft.Text(str(p.get("unidad", "UND")))
                        ),

                        # Columna 4: Precio unitario (con oferta si aplica)
                        crear_celda_precio(p),

                        # Columna 5: Descuento (clickeable para editar)
                        ft.DataCell(
                            ft.TextButton(
                                content=ft.Text(f"{p.get('descuento', 0):,.2f}%"),
                                on_click=lambda e, idx=i: editar_descuento(idx)
                            )
                        ),

                        # Columna 6: Subtotal del producto
                        ft.DataCell(
                            ft.Text(f"${p.get('subtotal', 0):,.2f}")
                        ),

                        # Columna 7: Empresa/lugar del producto
                        ft.DataCell(
                            ft.Text(str(p.get('lugar', '-')))
                        ),

                        # Columna 8: Botón eliminar (X roja)
                        crear_celda_acciones(p, i)
                    ]
                )
            )

        # Recalcular totales después de eliminar
        actualizar_totales()

        pagina.update()

    # Agrega un producto a la tabla de venta cuando el usuario lo selecciona
    # desde el diálogo de búsqueda (F3).
    # El producto viene del controlador con los datos ya procesados.
    def agregar_producto_a_tabla(producto):

        # No agregar si estamos en modo consulta
        if modo_consulta:
            return

        # Cantidad que el usuario quiere agregar
        cantidad = producto.get("cantidad", 1)

        # ---------------------------------------------
        # LO AGREGO NORMAL
        # ---------------------------------------------

        # Agregar el producto a la lista y obtener la referencia actualizada
        producto = ventas_controller.agregar_producto_a_venta(productos, producto)
        cantidad_texto = ventas_controller.formatear_cantidad(
            cantidad
        )
        # Insertar una nueva fila al final de la tabla
        tabla_productos.rows.append(
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(str(producto.get('codigo', '-')))),
                    ft.DataCell(ft.Text(producto.get('nombre', 'Sin nombre'))),
                    ft.DataCell(
                    ft.TextButton(
                        content=ft.Text(cantidad_texto),
                        on_click=lambda e, idx=len(productos): editar_cantidad(idx - 1)
                    )
                ),
                    ft.DataCell(ft.Text(str(producto.get('unidad', 'UND')))),
                    crear_celda_precio(producto),
                    ft.DataCell(
                        ft.TextButton(
                            content=ft.Text(f"{producto.get('descuento', 0):,.2f}%"),
                            on_click=lambda e, idx=len(productos): editar_descuento(idx - 1)
                        )
                    ),
                    ft.DataCell(ft.Text(f"${producto.get('subtotal', 0):,.2f}")),
                    ft.DataCell(ft.Text(str(producto.get('lugar', '-')))),
                    crear_celda_acciones(producto, len(productos)-1)
                ]
            )
        )

        # Actualizar subtotal, descuento y total después de agregar
        actualizar_totales()
        tabla_productos.update()

    # Tarea asíncrona que actualiza el reloj en la barra superior cada segundo.
    # Se ejecuta como una tarea de fondo con run_task().
    # Se detiene automáticamente cuando la vista ya no está activa (RuntimeError).
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
            # Esperar 1 segundo antes de actualizar
            await asyncio.sleep(1)

    # Callback que se ejecuta después de confirmar el método de pago.
    # Llama al controlador para guardar la factura en la BD y generar el PDF.
    def confirmar_factura(pago):
        resultado = ventas_controller.confirmar_factura(
            pago=pago,
            productos=productos,
            cliente=cliente_actual,
            usuario=usuario,
            id_apartado=apartado_actual
        )

        if not resultado:
            print("Error al guardar la factura")
            mostrar_notificacion(pagina, "No fue posible guardar la venta.", error=True)
            return

        print(f"Factura {resultado['id_factura']} guardada")
        print(f"PDF: {resultado['ruta_pdf']}")
        # Limpiar la tabla para una nueva venta
        limpiar_factura()
        mostrar_notificacion(
            pagina, f"Venta #{resultado['id_factura']} guardada correctamente."
        )

    # ---------------- FACTURAR ----------------

    # Abre el diálogo de método de pago para confirmar la venta.
    # Valida que haya productos y que no esté en modo consulta.
    def facturar():

        # Los usuarios normales no pueden facturar desde modo consulta
        if modo_consulta and usuario.get("rol", "").lower() != "admin":
            print("No se puede facturar en modo consulta")
            return
        # No permitir facturar sin productos
        if not productos:
            print("No hay productos en la factura")
            return

        # Calcular el total para mostrar en el diálogo de pago
        total_valor = ventas_controller.calcular_total(productos)

        # Crear dialogo de método de pago (efectivo, tarjeta, etc.)
        dialog = metodo_pago_view(
            pagina,
            total_valor,
            confirmar_factura,
            productos=productos
        )

        # Abrir dialogo como overlay sobre la vista actual
        pagina.overlay.append(dialog)
        dialog.open = True
        pagina.update()

    # Resetea toda la vista a su estado inicial para comenzar una nueva venta.
    # Limpia productos, cliente, tabla, campos de texto y totales.
    def limpiar_factura():

        nonlocal productos
        nonlocal modo_consulta
        nonlocal id_factura_actual
        nonlocal cliente_actual
        nonlocal apartado_actual

        # Vaciar la lista de productos y el cliente seleccionado
        productos = []
        cliente_actual = None

        # Reiniciar la entrega de apartado (venta directa de pasillo)
        apartado_actual = None

        # Limpiar todas las filas de la tabla
        tabla_productos.rows.clear()

        # Vaciar campo de cliente
        nombreCliente.value = ""

        # Ocultar campos de información de factura consultada
        usuarioFactura.value = ""
        usuarioFactura.visible = False
        texto_fecha.value = ""
        texto_fecha.visible = False
        notaFactura.controls.clear()
        notaFactura.visible = False

        # Resetear el número de factura a "Nueva"
        numeroFactura.value = "Número de factura: Nueva"
        numeroFactura.color = ft.Colors.BLACK

        # Ocultar botón de imprimir (solo visible en modo consulta)
        btn_imprimir_consulta.visible = False

        # Recalcular totales (quedará en $0)
        actualizar_totales()

        # Salir del modo consulta
        modo_consulta = False
        id_factura_actual = None

        pagina.update()

    # Carga una factura existente desde la base de datos por su ID.
    # Reconstruye la tabla de productos, muestra datos del cliente,
    # usuario que vendió, fecha, notas y el estado (anulada o activa).
    # Retorna True si se cargó correctamente, False si hubo error.
    def cargar_factura(id_venta):
        nonlocal productos, modo_consulta, id_factura_actual

        # Solicitar los datos al controlador
        datos = ventas_controller.cargar_factura(id_venta)
        if not datos:
            return False

        cliente = datos["cliente"]
        productos = datos["productos"]
        factura = datos["factura"]

        # Limpiar la tabla antes de reconstruirla
        tabla_productos.rows.clear()

        # Mostrar fecha de la factura
        texto_fecha.value = (
            f"Fecha: {factura['fecha'].strftime('%d/%m/%Y %H:%M:%S')}"
        )
        texto_fecha.visible = True

        # Reconstruir cada fila de la tabla con los datos de la factura
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
                    crear_celda_precio(producto),
                    ft.DataCell(ft.Text(f"{producto.get('descuento', 0):,.2f}%")),
                    ft.DataCell(ft.Text(f"${producto['subtotal']:,.2f}")),
                    ft.DataCell(ft.Text(producto["lugar"])),
                    # En modo consulta el botón X está deshabilitado
                    crear_celda_acciones(producto, i, deshabilitado=True)
                ])
            )

        # Mostrar nombre del cliente seleccionado
        nombreCliente.value = f"{cliente['nombre']} - {cliente['rol']}" if cliente else "Sin cliente"

        # Mostrar quién realizó la venta
        usuarioFactura.value = (
            f"Vendido por: {factura.get('nombre_usuario', 'Sin usuario')}"
        )
        usuarioFactura.visible = True

        # Mostrar notas si existen (una por empresa si aplica)
        notas_empresa = factura.get("notas_empresa") or {}
        notaFactura.controls.clear()
        if notas_empresa:
            notaFactura.controls.append(
                ft.Text("Notas:", size=13, weight="bold")
            )
            for empresa, texto in notas_empresa.items():
                notaFactura.controls.append(
                    ft.Text(f"{empresa}: {texto}", size=13)
                )
            notaFactura.visible = True

        # Mostrar número de factura con color según estado
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

        # Activar modo consulta: bloquea edición de productos
        modo_consulta = True
        id_factura_actual = id_venta

        # Mostrar botón de imprimir (solo disponible en modo consulta)
        btn_imprimir_consulta.visible = True
        pagina.update()
        return True

    # Genera el PDF de la factura consultada y lo envía a imprimir.
    # Solo funciona si hay una factura cargada en modo consulta.
    def imprimir_factura_consultada():
        if not modo_consulta or id_factura_actual is None:
            print("Primero consulta una factura para imprimirla")
            return

        # Delegar al controlador la generación del PDF
        ruta_pdf = ventas_controller.imprimir_factura_consultada(
            id_factura_actual,
            usuario
        )
        if not ruta_pdf:
            print("No se pudo imprimir la factura consultada")
            return

        print(f"Factura {id_factura_actual} enviada a imprimir")

    # Maneja la pulsación de F4 para nueva factura.
    # Primera vez: limpia la factura actual en la misma ventana.
    # Segunda vez: abre una nueva ventana con la vista de facturas.
    def nueva_factura():
        nonlocal index_factura, modo_consulta, f4_siguiente_abrir_ventana

        # Si ya se usó el cambio anterior, abro una segunda ventana
        if not f4_siguiente_abrir_ventana:
            abrir_nueva_instancia("factura", usuario)
            f4_siguiente_abrir_ventana = True
            return

        # Si es la primera vez, limpio la factura actual y preparo una nueva en la misma ventana
        facturas.clear()
        index_factura = -1
        modo_consulta = False
        limpiar_factura()
        # Marcar que la próxima pulsación abrirá ventana nueva
        f4_siguiente_abrir_ventana = False

    # Navega a la siguiente factura guardada (F6).
    # Usa navegación circular: al llegar al final vuelve al principio.
    def siguiente_factura():
        nonlocal index_factura
        if not facturas:
            cargar_lista_facturas()
            return
        index_factura = (index_factura + 1) % len(facturas)
        cargar_factura(facturas[index_factura]['id_venta'])

    # Navega a la factura anterior guardada (F7).
    # Usa navegación circular: al llegar al inicio va al final.
    def anterior_factura():
        nonlocal index_factura
        if not facturas:
            cargar_lista_facturas()
            return
        index_factura = (index_factura - 1) % len(facturas)
        cargar_factura(facturas[index_factura]['id_venta'])

    # Carga la lista completa de facturas desde la base de datos
    # y muestra la primera de la lista.
    def cargar_lista_facturas():
        nonlocal facturas, index_factura
        facturas = ventas_controller.listar_facturas()
        if facturas:
            index_factura = 0
            cargar_factura(facturas[0]['id_venta'])
        else:
            limpiar_factura()

    # Borra o anula la factura actual según el modo:
    # - Modo nueva factura: simplemente limpia la tabla
    # - Modo consulta: anula la factura (requiere permisos de admin/Aprendiz)
    # Muestra un diálogo de confirmación antes de ejecutar la acción.
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
        # MODO CONSULTA - ANULAR FACTURA
        # -----------------------------------
        else:
            # Los Aprendices no tienen permisos para anular facturas
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

                # Anular la factura en la base de datos
                if ventas_controller.borrar_factura(
                    id_factura_actual
                ):
                    snack = ft.SnackBar(
                        content=ft.Text("Factura anulada"),
                        bgcolor=ft.Colors.RED
                    )
                    pagina.overlay.append(snack)
                    snack.open = True
                    # Recargar la lista de facturas después de anular
                    facturas.clear()
                    index_factura = -1
                    cargar_lista_facturas()

        # -----------------------------------
        # DIALOGO GENERAL DE CONFIRMACIÓN
        # -----------------------------------
        dialog = confirmar_view(
            pagina,
            mensaje,
            on_confirmar
        )
        pagina.overlay.append(dialog)
        dialog.open = True
        pagina.update()

    # Abre el diálogo de búsqueda de productos (F3).
    # Se pasa la función `agregar_producto_a_tabla` como callback
    # para que cuando el usuario seleccione un producto se inserte en la tabla.
    def buscar_producto():
        if modo_consulta:
            return
        dialog = buscar_producto_view(pagina, agregar_producto_a_tabla)
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
    # Se pasa la función `seleccionar_cliente` como callback
    # para que al seleccionar un cliente se muestre en la interfaz.
    def buscar_cliente():
        if modo_consulta:
            return
        dialog = buscar_cliente_view(pagina, seleccionar_cliente)
        pagina.overlay.append(dialog)
        dialog.open = True
        pagina.update()

    # ------------------------------------------------------------------
    # ENTREGA DE APARTADO WEB (F9)
    # ------------------------------------------------------------------
    # Abre el diálogo que lista los apartados web pendientes. Al seleccionar
    # uno, se precarga el producto reservado en la venta y se asocia el
    # apartado a la factura. Al facturar, no se descuenta limite_venta y el
    # apartado pasa a 'entregado'.
    def entregar_apartado():

        # No permitir entregar apartados en modo consulta
        if modo_consulta:
            return

        dialog = entregar_apartado_view(pagina, seleccionar_apartado)
        pagina.overlay.append(dialog)
        dialog.open = True
        pagina.update()

    # Callback que se ejecuta al elegir un apartado en el diálogo (F9).
    # Precarga el producto reservado en la venta con la cantidad (en unidades)
    # que el cliente apartó en línea, y muestra el cliente en su campo.
    def seleccionar_apartado(apartado):
        nonlocal apartado_actual

        id_apartado = apartado.get('id_apartado')
        cantidad = apartado.get('cantidad', 1)
        id_producto = apartado.get('id_producto')
        nombre_producto = apartado.get('nombre', 'Sin nombre')
        nombre_cliente = apartado.get('nombre_cliente', 'Cliente')

        # Armo el producto a partir del apartado con la cantidad reservada.
        # La cantidad ya viene en unidades (la web convierte cubetas x30).
        # 'precio_aplicado' es el precio unitario real (CON descuento) que el
        # cliente pagó/apartó en la web; se respeta tal cual al facturar.
        precio_aplicado = apartado.get('precio_aplicado')
        producto = {
            'id': id_producto,
            'id_producto': id_producto,
            'codigo': apartado.get('codigo', '-'),
            'nombre': nombre_producto,
            'unidad': apartado.get('unidad', 'UND'),
            'precio': float(precio_aplicado if precio_aplicado is not None else apartado.get('precio', 0)),
            'precio_aplicado': precio_aplicado,
            'cantidad': cantidad,
            'stock': 0,
            'descuento': 0,
            'subtotal': float(cantidad) * float(precio_aplicado if precio_aplicado is not None else apartado.get('precio', 0)),
            # Marca que esta línea es el producto reservado del apartado web.
            # Se usa al facturar para saber que NO debe descontarse limite_venta
            # (ya se restó en la web) y que su cantidad va en unidades.
            'es_apartado': True,
        }

        # Precargo el producto reservado en la tabla de la venta
        agregar_producto_a_tabla(producto)

        # Asocio el apartado a la factura actual y muestro el cliente del
        # apartado en el campo de cliente seleccionado.
        apartado_actual = id_apartado
        nombreCliente.value = f"{nombre_cliente} - Apartado"
        pagina.update()

        mostrar_notificacion(
            pagina,
            f"Apartado #{id_apartado} cargado. Al facturar no se descuenta\n"
            "el límite de venta y el apartado pasa a 'entregado'."
        )

    # Abre el diálogo de creación rápida de productos o clientes (F8).
    # Muestra un menú con opciones "CrearP" (producto) y "CrearU" (usuario).
    def crearP_C():
        dialog = Crear(pagina, lambda _opcion: None)
        pagina.overlay.append(dialog)
        dialog.open = True
        pagina.update()


    # ---------------- TECLADO ----------------

    # Handler principal de atajos de teclado para toda la vista de ventas.
    # Cada tecla de función tiene una acción asignada.
    async def teclado(e: ft.KeyboardEvent):

        # F2 → Facturar la venta actual
        if e.key == "F2":
            facturar()

        # Escape → Volver al menú principal del sistema
        elif e.key == "Escape":
            ir_a_menu(usuario)

        # F3 → Abrir diálogo de búsqueda de productos
        elif e.key == "F3":
            buscar_producto()

        # F1 → Abrir diálogo de búsqueda de clientes
        elif e.key == "F1":
            buscar_cliente()

        # F4 → Nueva factura (limpiar o abrir nueva ventana)
        elif e.key == "F4":
            nueva_factura()

        # F5 → Borrar/Anular factura actual
        elif e.key == "F5":
            borrar_factura_actual()

        # F6 → Navegar a la siguiente factura guardada
        elif e.key == "F6":
            siguiente_factura()

        # F7 → Navegar a la factura anterior guardada
        elif e.key == "F7":
            anterior_factura()
        
        # F8 → Crear producto o cliente
        elif e.key == "F8":
            crearP_C()

        # F9 → Entregar apartado web
        elif e.key == "F9":
            entregar_apartado()


    # ---------------- BOTONES ----------------

    # Botón para volver al menú principal del sistema (atajo: Escape)
    Volver_menu = ft.Button("Volver [Esc]", on_click=lambda _: ir_a_menu(usuario))

    # Botón para abrir el diálogo de búsqueda de productos (atajo: F3)
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

    # Botón para facturar la venta actual (atajo: F2).
    # Color verde para indicar acción positiva/confirmación.
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

    # Botón para abrir el diálogo de búsqueda de clientes (atajo: F1)
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
    
    # Botón para abrir diálogo de creación de productos/clientes (atajo: F8)
    btn_registrar_cliente = ft.Button(
        "Crear P/C [F8]",
        on_click=lambda _: crearP_C(),
        width=190,
        height=40,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            text_style=ft.TextStyle(size=15, weight="bold")
        )
    )

    # Botón para entregar un apartado web (atajo: F9).
    # Abre el diálogo con los apartados pendientes para precargarlo en la venta.
    btn_entregar_apartado = ft.Button(
        "Apartado [F9]",
        on_click=lambda _: entregar_apartado(),
        width=180,
        height=40,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            text_style=ft.TextStyle(size=15, weight="bold")
        )
    )

    # Botón para crear una nueva factura (atajo: F4).
    # Primera pulsación: limpia. Segunda: abre nueva ventana.
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

    # Botón para cargar y consultar facturas guardadas (atajos: F6/F7)
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

    # Botón para imprimir la factura consultada.
    # Solo visible cuando hay una factura cargada en modo consulta.
    # Color azul para diferenciarlo de las acciones principales.
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

    # Botón para borrar la factura actual o anular una consultada (atajo: F5).
    # Color rojo para indicar acción destructiva.
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

    # Tabla principal donde se muestran los productos agregados a la venta.
    # Columnas: Codigo, Producto, Cantidad (editable), Unidad, Precio unitario,
    #           Descuento (editable), Subtotal, Empresa, Acciones (botón X).
    # La cantidad y el descuento se editan haciendo clic en la celda.
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
            ft.DataColumn(ft.Text("")), # Columna para el botón eliminar
        ],
        rows=[],
        border=ft.Border.all(1, ft.Colors.BLACK),
        border_radius=10,
        vertical_lines=ft.BorderSide(1, ft.Colors.BLACK_26),
        horizontal_lines=ft.BorderSide(1, ft.Colors.BLACK),
    )

    # ---------------- PANELES ----------------

    # Panel izquierdo: contiene el encabezado, los botones de acción,
    # el campo del cliente y la tabla de productos con scroll automático.
    # Ocupa todo el espacio disponible (expand=True).
    panel_izquierdo = ft.Container(
        expand=True,
        bgcolor=ft.Colors.WHITE,
        border=ft.Border.all(1, ft.Colors.BLACK),
        border_radius=10,
        padding=20,
        content=ft.Column(
            [
                # Encabezado: título "Nueva venta" a la izquierda,
                # número de factura a la derecha
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

                # Fila de botones principales: nueva factura, buscar producto,
                # buscar cliente, crear producto/cliente, entregar apartado
                ft.Row(
                    [
                        btn_nueva_factura,
                        btn_buscar_producto,
                        btn_buscar_cliente,
                        btn_registrar_cliente,
                        btn_entregar_apartado
                    ],
                    spacing=5
                ),
                ft.Divider(),
                # Fila con el título "Productos agregados" y el campo de cliente
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
                # Contenedor de la tabla con scroll automático vertical y horizontal
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

    # Panel derecho: muestra el resumen de la venta (subtotal, descuento, total),
    # información de la factura consultada, y los botones de acción secundarios
    # (facturar, consultar, imprimir, borrar). Ancho fijo de 230px.
    panel_derecho = ft.Container(
        width=230,
        bgcolor=ft.Colors.WHITE,
        border=ft.Border.all(1, ft.Colors.BLACK),
        border_radius=10,
        padding=20,
        content=ft.Column(
            [
                # Título del resumen
                ft.Text("Resumen de venta", weight="bold", size=17),

                # Totales calculados dinámicamente
                subtotal,
                descuento,

                ft.Divider(),

                total,

                ft.Divider(),

                # Campos visibles solo en modo consulta
                texto_fecha,
                usuarioFactura,
                notaFactura,


                # Botón de facturar (centrado)
                ft.Row(
                    btn_facturar,
                    spacing=10,
                    alignment=ft.MainAxisAlignment.CENTER,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                ),
                # Botón de consultar facturas guardadas
                ft.Row(
                    btn_consultar,
                    spacing=10,
                    alignment=ft.MainAxisAlignment.CENTER,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                ),
                # Botón de imprimir (oculto por defecto)
                ft.Row(
                    btn_imprimir_consulta,
                    spacing=10,
                    alignment=ft.MainAxisAlignment.CENTER,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                ),
                # Botón de borrar/anular (rojo)
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

    # Layout principal: estructura vertical con barra superior y cuerpo dividido
    # en panel izquierdo (tabla) y panel derecho (resumen + acciones).
    pagina.add(
        ft.Column(
            [
                # Barra superior: logo, título, usuario, nombre, reloj y botón volver
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

    # Registrar el handler de atajos de teclado en la página
    pagina.on_keyboard_event = teclado

    # Refresco la pantalla para mostrar todos los elementos
    pagina.update()

    # Cargar la lista de facturas para poder navegar con F6/F7
    # (muestra la primera factura si existe)
    cargar_lista_facturas()

    # Iniciar la tarea asíncrona que actualiza el reloj cada segundo
    pagina.run_task(actualizar_hora)