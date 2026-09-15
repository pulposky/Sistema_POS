"""
Pantalla para modificar facturas de venta, compra y remisión.

Permite cargar un documento existente por tipo y número, modificar sus líneas
(productos, cantidades, precios), cambiar datos de cabecera (fecha, tercero,
método de pago, notas) y guardar los cambios.

Características principales:
  - Carga documentos de tipo VENTA, COMPRA o REMISIÓN.
  - Los documentos anulados no se pueden editar.
  - Para VENTAS: muestra campos de método de pago, dinero recibido y cambio.
  - Para COMPRAS: busca proveedores en vez de clientes.
  - Para REMISIONES: muestra campo de tipo de remisión y oculta precios.
  - La tabla permite editar cantidades y precios línea por línea, o eliminar líneas.
  - Se pueden agregar nuevos productos al documento.

Atajos de teclado:
    Escape -> Vuelve al menú principal.

Navegación:
    ir_a_menu(usuario) -> Vuelve al menú principal.
"""

from datetime import datetime
import flet as ft

from controllers.actualizarDocumentosController import cargar_documento, actualizar_documento
from utils.buscarProducto import buscar_producto_view
from utils.buscarCliente import buscar_cliente_view
from utils.buscarProveedor import buscar_proveedor_view
from utils.notificaciones import mostrar_notificacion


def actualizar_facturas_view(pagina: ft.Page, ir_a_menu, usuario):
    """
    Renderiza la vista de actualización de documentos (facturas).

    Parámetros:
        pagina    -> Instancia de la página Flet.
        ir_a_menu -> Callback para volver al menú principal.
        usuario   -> Diccionario con datos del usuario logueado.
    """
    # Limpio la pantalla
    pagina.clean()

    # Configuro el tamaño de la ventana
    pagina.window.width = 1280
    pagina.window.height = 780

    # ================== ESTADO ==================

    # Lista de productos del documento cargado (se modifica en memoria)
    productos = []

    # Tercero (cliente o proveedor) actualmente seleccionado
    tercero_actual = None

    # Tipo de documento que se está editando (VENTA, COMPRA, REMISION)
    # Se usa para validar que no se cambie el tipo después de cargar
    tipo_actual = None

    # ================== CAMPOS DE FORMULARIO ==================

    # Dropdown para seleccionar el tipo de documento a editar
    tipo = ft.Dropdown(
        label="Tipo de documento", width=190, value="VENTA",
        options=[ft.dropdown.Option("VENTA"), ft.dropdown.Option("COMPRA"), ft.dropdown.Option("REMISION")],
    )

    # Campo de número de documento (para buscar el documento a cargar)
    numero = ft.TextField(label="Número", width=120)

    # Campo de fecha (se carga automáticamente al cargar el documento)
    fecha = ft.TextField(label="Fecha (DD/MM/AAAA HH:MM)", width=220)

    # Campo de tercero (cliente o proveedor): solo lectura, se selecciona con el botón de búsqueda
    tercero = ft.TextField(label="Cliente / proveedor", width=260, read_only=True)

    # Campo de método de pago (solo visible para VENTAS)
    metodo_pago = ft.TextField(label="Método de pago", width=180)

    # Campo de dinero recibido (solo visible para VENTAS)
    dinero_recibido = ft.TextField(label="Dinero recibido", width=150)

    # Campo de cambio/devolución (solo visible para VENTAS)
    cambio = ft.TextField(label="Cambio", width=120)

    # Campo de tipo de remisión (solo visible para REMISIONES)
    tipo_remision = ft.TextField(label="Tipo de remisión", width=260)

    # Campo de notas: multilinea para observaciones adicionales
    notas = ft.TextField(label="Notas", width=400, multiline=True, min_lines=1, max_lines=2)

    # Texto que muestra el total calculado de la factura
    total = ft.Text("Total: $0", size=16, weight="bold")

    # Texto de estado que indica qué se está editando o si hay errores
    estado = ft.Text("Seleccione el tipo y número, luego cargue el documento.")

    # Tabla de productos del documento
    tabla = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Producto")),
            ft.DataColumn(ft.Text("Cantidad")),
            ft.DataColumn(ft.Text("Precio unitario")),
            ft.DataColumn(ft.Text("Subtotal")),
            ft.DataColumn(ft.Text("Acción")),
        ],
        rows=[],
        border_radius=10,
    )

    # ================== FUNCIONES AUXILIARES ==================

    def numero_decimal(valor, nombre):
        """
        Convierte un valor a float, reemplazando comas por puntos.
        Lanza ValueError con un mensaje descriptivo si el valor no es válido.
        """
        try:
            return float(str(valor).replace(",", "."))
        except (TypeError, ValueError):
            raise ValueError(f"{nombre} inválido.")

    def formatear(valor):
        """
        Formatea un número: si es entero sin decimales, si tiene decimales
        muestra hasta 3 cifras eliminando ceros innecesarios.
        """
        valor = float(valor or 0)
        return str(int(valor)) if valor.is_integer() else f"{valor:.3f}".rstrip("0").rstrip(".")

    def recalcular():
        """
        Recalcula el total sumando (cantidad * precio) de todos los productos.
        Para REMISIONES muestra "Remisión sin valor comercial" en vez del total.
        """
        valor = sum(float(p.get("cantidad", 0)) * float(p.get("precio", 0) or 0) for p in productos)
        total.value = "Remisión sin valor comercial" if tipo.value == "REMISION" else f"Total: ${valor:,.2f}"

    # ================== FUNCIONES DE TABLA ==================

    def pintar_tabla():
        """
        Reconstruye las filas de la tabla con los productos actuales.
        Cada fila tiene campos editables de cantidad y precio, subcalculado automático,
        y botones para aplicar cambios línea por línea o eliminar la línea.
        """
        tabla.rows.clear()
        for indice, producto in enumerate(productos):
            # Campo de cantidad editable
            cantidad = ft.TextField(value=formatear(producto.get("cantidad", 0)), width=100, dense=True)

            # Campo de precio unitario: visible solo si NO es remisión
            precio = ft.TextField(value=f"{float(producto.get('precio', 0) or 0):.2f}", width=120, dense=True,
                                  visible=tipo.value != "REMISION")

            def guardar_linea(_, i=indice, campo_cantidad=cantidad, campo_precio=precio):
                """
                Aplica los cambios de una línea: actualiza cantidad y precio en la lista
                de productos, recalcula el subtotal y repinta la tabla.
                Valida que la cantidad sea mayor que cero.
                """
                try:
                    productos[i]["cantidad"] = numero_decimal(campo_cantidad.value, "Cantidad")
                    productos[i]["precio"] = 0 if tipo.value == "REMISION" else numero_decimal(campo_precio.value, "Precio")
                    if productos[i]["cantidad"] <= 0 or productos[i]["precio"] < 0:
                        raise ValueError("La cantidad debe ser mayor que cero.")
                    productos[i]["subtotal"] = productos[i]["cantidad"] * productos[i]["precio"]
                    pintar_tabla()
                    pagina.update()
                except ValueError as error:
                    mostrar_notificacion(pagina, str(error), error=True)

            def borrar_linea(_, i=indice):
                """Elimina un producto de la lista por su índice y repinta la tabla."""
                productos.pop(i)
                pintar_tabla()
                pagina.update()

            # Agrego la fila a la tabla con todos los campos y botones de acción
            tabla.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(str(producto.get("id", "-")))),
                ft.DataCell(ft.Text(producto.get("nombre", "Sin nombre"))),
                ft.DataCell(cantidad), ft.DataCell(precio),
                ft.DataCell(ft.Text(f"${float(producto.get('subtotal', 0) or 0):,.2f}")),
                ft.DataCell(ft.Row([
                    # Botón de guardar línea: aplica los cambios de esta fila
                    ft.IconButton(icon=ft.Icons.SAVE, tooltip="Aplicar línea", on_click=guardar_linea),
                    # Botón de eliminar línea: quita este producto del documento
                    ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, tooltip="Quitar línea", on_click=borrar_linea),
                ], tight=True)),
            ]))

        # Recalculo el total después de repintar
        recalcular()

    def actualizar_campos_tipo():
        """
        Muestra u oculta campos según el tipo de documento seleccionado:
          - VENTA: muestra método de pago, dinero recibido y cambio.
          - REMISION: muestra tipo de remisión, oculta precios.
          - COMPRA: oculta todos los campos especiales.
        """
        es_venta = tipo.value == "VENTA"
        es_remision = tipo.value == "REMISION"
        metodo_pago.visible = es_venta
        dinero_recibido.visible = es_venta
        cambio.visible = es_venta
        tipo_remision.visible = es_remision
        pagina.update()

    # ================== FUNCIONES DE BÚSQUEDA ==================

    def seleccionar_tercero(seleccionado):
        """
        Callback que se ejecuta cuando el usuario selecciona un cliente o proveedor
        desde el diálogo de búsqueda. Actualiza el campo de tercero y la variable de estado.
        """
        nonlocal tercero_actual
        tercero_actual = seleccionado
        tercero.value = seleccionado.get("nombre", "Sin nombre")
        pagina.update()

    def buscar_tercero(_=None):
        """
        Abre el diálogo de búsqueda de tercero según el tipo de documento:
          - COMPRA: busca proveedores.
          - VENTA/REMISION: busca clientes.
        """
        if tipo.value == "COMPRA":
            dialogo = buscar_proveedor_view(pagina, seleccionar_tercero)
        else:
            dialogo = buscar_cliente_view(pagina, seleccionar_tercero)
        pagina.overlay.append(dialogo)
        dialogo.open = True
        pagina.update()

    def agregar_producto(seleccionado):
        """
        Callback que se ejecuta cuando el usuario selecciona un producto desde
        el diálogo de búsqueda. Crea una copia del producto, ajusta precio según
        el tipo (0 para remisiones) y lo agrega a la lista.
        """
        producto = dict(seleccionado)
        # Normalizo el campo id (puede venir como 'id' o 'id_producto')
        producto["id"] = producto.get("id") or producto.get("id_producto")
        producto["cantidad"] = float(producto.get("cantidad", 1) or 1)
        # En remisiones el precio siempre es 0
        producto["precio"] = 0 if tipo.value == "REMISION" else float(producto.get("precio", 0) or 0)
        producto["subtotal"] = producto["cantidad"] * producto["precio"]
        productos.append(producto)
        pintar_tabla()
        pagina.update()

    def buscar_producto(_=None):
        """
        Abre el diálogo de búsqueda de productos.
        Si es remisión, oculta el campo de precio en el diálogo.
        """
        dialogo = buscar_producto_view(pagina, agregar_producto, mostrar_precio=tipo.value != "REMISION")
        pagina.overlay.append(dialogo)
        dialogo.open = True
        pagina.update()

    # ================== FUNCIONES PRINCIPALES ==================

    def cargar(_=None):
        """
        Carga un documento existente desde la base de datos.
        Valida que el documento exista y que no esté anulado.
        Carga todos los campos de cabecera y las líneas de producto.
        """
        nonlocal productos, tercero_actual, tipo_actual
        try:
            datos = cargar_documento(tipo.value, int(numero.value))
        except ValueError:
            datos = None

        if not datos:
            mostrar_notificacion(pagina, "No se encontró el documento solicitado.", error=True)
            return

        cabecera = datos["cabecera"]

        # No permito editar documentos anulados
        if cabecera.get("estado") != "ACTIVA":
            mostrar_notificacion(pagina, "No puede editar un documento anulado.", error=True)
            return

        # Registro el tipo actual para validar que no se cambie después
        tipo_actual = tipo.value
        tercero_actual = datos.get("tercero")

        # Cargo todos los campos de cabecera
        tercero.value = (tercero_actual or {}).get("nombre", "")
        fecha_valor = cabecera.get("fecha")
        fecha.value = fecha_valor.strftime("%d/%m/%Y %H:%M") if hasattr(fecha_valor, "strftime") else str(fecha_valor)
        metodo_pago.value = cabecera.get("metodo_pago", "")
        dinero_recibido.value = str(cabecera.get("dinero_recibido", 0) or 0)
        cambio.value = str(cabecera.get("cambio", 0) or 0)
        tipo_remision.value = cabecera.get("tipo_remision", "")
        notas.value = cabecera.get("notas", "") or ""

        # Cargo los productos del documento
        productos = [dict(p) for p in datos["productos"]]
        for producto in productos:
            # En remisiones el precio es 0
            producto["precio"] = 0 if tipo.value == "REMISION" else float(producto.get("precio", 0) or 0)
            producto["subtotal"] = float(producto.get("cantidad", 0)) * producto["precio"]

        # Actualizo la visibilidad de campos según el tipo
        actualizar_campos_tipo()

        # Pinto la tabla con los productos cargados
        pintar_tabla()

        # Muestro mensaje de estado
        estado.value = f"Editando {tipo.value.lower()} #{numero.value}. Modifique las líneas y guarde."
        pagina.update()

    def guardar(_=None):
        """
        Guarda los cambios del documento en la base de datos.
        Valida que se haya cargado un documento previamente, que tenga un tercero
        seleccionado y que todos los campos sean válidos.
        Si el guardado es exitoso, recarga el documento para reflejar los cambios.
        """
        # Valido que se haya cargado un documento del mismo tipo
        if not tipo_actual or tipo_actual != tipo.value:
            mostrar_notificacion(pagina, "Cargue primero el documento del tipo seleccionado.", error=True)
            return

        # Valido que haya un tercero seleccionado
        if not tercero_actual:
            mostrar_notificacion(pagina, "Seleccione un cliente o proveedor.", error=True)
            return

        try:
            # Convierto la fecha del formato DD/MM/YYYY HH:MM al formato de base de datos
            fecha_db = datetime.strptime(fecha.value.strip(), "%d/%m/%Y %H:%M").strftime("%Y-%m-%d %H:%M:%S")

            # Obtengo el ID del tercero según el tipo de documento
            id_tercero = tercero_actual.get("id_proveedor") if tipo.value == "COMPRA" else tercero_actual.get("id_cliente")

            # Construyo la cabecera del documento
            cabecera = {"fecha": fecha_db, "id_tercero": id_tercero, "notas": notas.value or ""}

            # Agrego campos específicos según el tipo
            if tipo.value == "VENTA":
                cabecera.update({
                    "metodo_pago": metodo_pago.value.strip(),
                    "dinero_recibido": numero_decimal(dinero_recibido.value, "Dinero recibido"),
                    "cambio": numero_decimal(cambio.value, "Cambio")
                })
            elif tipo.value == "REMISION":
                cabecera["tipo_remision"] = tipo_remision.value.strip()

            # Valido que el tercero tenga un ID válido
            if not id_tercero:
                raise ValueError("El tercero seleccionado no es válido.")
        except ValueError as error:
            mostrar_notificacion(pagina, str(error), error=True)
            return

        # Llamo al controller para actualizar el documento
        correcto, mensaje = actualizar_documento(tipo.value, numero.value, cabecera, productos)
        mostrar_notificacion(pagina, mensaje, error=not correcto)

        # Si se guardó correctamente, recargo el documento para reflejar los cambios
        if correcto:
            cargar()

    # ================== CONSTRUCCIÓN DE LA INTERFAZ ==================

    # Configuro la visibilidad inicial de los campos según el tipo por defecto (VENTA)
    actualizar_campos_tipo()

    # Estructura: Columna principal con:
    #   1. Fila de título con botón de volver
    #   2. Separador
    #   3. Fila de selección de tipo/número con botón de carga
    #   4. Fila de campos de fecha y tercero con botón de búsqueda
    #   5. Fila de campos específicos del tipo (pago, remisión, etc.)
    #   6. Campo de notas
    #   7. Fila de botones de acción (agregar producto, guardar)
    #   8. Tabla de productos con scroll
    pagina.add(ft.Column([
        # Fila superior: título, usuario y botón de volver
        ft.Row([ft.Text("Actualizar documentos", size=22, weight="bold"),
                ft.Text(f"Usuario: {usuario.get('usuario', '')}"),
                ft.Button("Volver", on_click=lambda _: ir_a_menu(usuario))],
               alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Divider(),
        # Fila de selección: tipo de documento, número y botón de carga
        ft.Row([tipo, numero, ft.Button("Cargar documento", icon=ft.Icons.SEARCH, on_click=cargar), estado], wrap=True),
        # Fila de fecha y tercero: con botón de búsqueda de cliente/proveedor
        ft.Row([fecha, tercero, ft.Button("Buscar cliente/proveedor", on_click=buscar_tercero)], wrap=True),
        # Fila de campos específicos del tipo (se muestran/ocultan dinámicamente)
        ft.Row([metodo_pago, dinero_recibido, cambio, tipo_remision], wrap=True),
        # Campo de notas
        notas,
        # Fila de botones de acción: agregar producto, guardar y total
        ft.Row([ft.Button("Agregar producto", icon=ft.Icons.ADD, on_click=buscar_producto),
                ft.Button("Guardar actualización", icon=ft.Icons.SAVE, on_click=guardar), total]),
        # Tabla de productos con scroll horizontal y vertical
        ft.Container(content=ft.Column([ft.Row([tabla], scroll=ft.ScrollMode.AUTO)], scroll=ft.ScrollMode.AUTO), expand=True),
    ], expand=True, scroll=ft.ScrollMode.AUTO, spacing=12))

    # Cuando cambia el tipo de documento, actualizo la visibilidad de los campos
    tipo.on_change = lambda _: actualizar_campos_tipo()

    # Atajo de teclado: Escape vuelve al menú principal
    pagina.on_keyboard_event = lambda e: ir_a_menu(usuario) if e.key == "Escape" else None

    # Refresco la pantalla
    pagina.update()
