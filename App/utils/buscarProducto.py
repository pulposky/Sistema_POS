import flet as ft
from models.ventasModel import buscar_producto, actualizar_producto
from utils.notificaciones import mostrar_notificacion
from controllers import ventasController as ventas_controller

# ============================================================================
# MÓDULO DE BÚSQUEDA Y SELECCIÓN DE PRODUCTOS
# ============================================================================
# Diálogo modal que permite buscar productos en la base de datos por nombre,
# seleccionar uno, opcionalmente editarlo antes de usar, y especificar la
# cantidad a vender.
#
# Flujo del diálogo (máquina de estados):
#   1. "buscar"     → El usuario escribe en el campo de búsqueda y presiona Enter.
#   2. "resultados" → Se muestran los productos encontrados como botones.
#   3. "opciones"   → Selecciona un producto y elige entre "Usar sin editar" o "Editar".
#   4. "edicion"    → Si eligió editar, muestra un formulario con los campos del producto.
#   5. "cantidad"   → Se ingresa la cantidad del producto a vender.
#
# Este diálogo reemplaza temporalmente el handler de teclado de la vista
# principal (vender.py) para manejar Escape, Enter y flechas.
#
# Dependencias:
#   - models.ventasModel: funciones buscar_producto() y actualizar_producto().
#   - utils.notificaciones: para mostrar confirmaciones de edición.
# ============================================================================


# =========================================================
# VISTA PARA BUSCAR Y SELECCIONAR PRODUCTOS
# =========================================================
def buscar_producto_view(pagina: ft.Page, agregar_producto_a_tabla, mostrar_precio=True):
    """
    Crea el diálogo de búsqueda de productos.

    Parámetros:
        pagina (ft.Page): Página de Flet donde se mostrará el diálogo.
        agregar_producto_a_tabla (callable): Función callback que recibe
            un diccionario con los datos del producto seleccionado y la
            cantidad, para agregarlo a la tabla de venta en vender.py.
        mostrar_precio (bool): Si True, muestra el precio en los resultados
            y en los detalles del producto. Si False, solo muestra unidad
            (usado en vistas donde no se necesitan precios).

    Retorna:
        ft.AlertDialog: Componente de diálogo listo para mostrarse en vender.py.
    """

    # ---------------- ESTADO ----------------

    # Lista de productos encontrados en la base de datos
    productos_encontrados = []

    # Posicion del producto seleccionado con el teclado
    index_seleccionado = 0

    # Fase actual del dialogo: buscar, resultados, opciones, edición o cantidad
    fase = "buscar"

    # Producto que el usuario selecciona antes de escribir cantidad
    producto_seleccionado = None
    producto_datos_editables = {}

    # Guardo el teclado anterior para restaurarlo al cerrar el dialogo
    teclado_anterior = pagina.on_keyboard_event

    # Evita que el dialogo se cierre mas de una vez
    dialogo_cerrado = False

    # Lista de botones que representan los productos encontrados
    botones_resultado = []

    # Evita agregar el mismo producto dos veces
    producto_confirmado = False

    # -------- CONTROLES --------

    # Campo donde el usuario escribe el nombre del producto
    campo_busqueda = ft.TextField(
        label="Buscar producto por nombre",
        width=340,
        autofocus=True,

        # Cuando cambia el texto limpio los resultados anteriores
        on_change=lambda e: limpiar_resultados(),

        # Si intenta tomar foco en resultados, lo regreso al producto seleccionado
        on_focus=lambda _: pagina.run_task(enfocar_producto, index_seleccionado) if fase == "resultados" else None,

        # Enter en este campo ejecuta la busqueda
        on_submit=lambda e: actualizar_resultados()
    )

    # Campo donde el usuario escribe la cantidad del producto seleccionado
    campo_cantidad = ft.TextField(
        label="Cantidad",
        width=100,
        value="1",
        visible=False,

        # Enter en cantidad confirma el producto
        on_submit=lambda e: confirmar_cantidad()
    )

    # Contenedor donde se muestran los botones de productos encontrados
    resultados_container = ft.Column(
        scroll=ft.ScrollMode.AUTO,
        # Sin una altura fija la lista puede crecer para mostrar todas las
        # coincidencias. Antes quedaba limitada a unas cinco filas y obligaba
        # a recorrer el resto con las flechas.
        spacing=4,
    )

    # Texto para mostrar mensajes de ayuda o errores
    mensaje = ft.Text("", size=12, color="red")

    # ---- Campos del formulario de edición de producto ----
    campo_nombre = ft.TextField(label="Nombre", width=340)
    campo_unidad = ft.TextField(label="Unidad", width=340)
    campo_lugar = ft.TextField(label="Empresa/Lugar", width=340)
    campo_precio = ft.TextField(label="Precio", width=340)
    campo_stock = ft.TextField(label="Stock", width=340)
    campo_descripcion = ft.TextField(label="Descripción", width=340, multiline=True, min_lines=2, max_lines=4)
    # Lista de categorías disponibles para los productos
    categoria_options = [
        "Abonos y Sustratos",
        "Frutas y Hortalizas",
        "Cereales, Granos y Forrajes",
        "Material Vegetal y Flores",
        "Embutidos y Cárnicos",
        "Bebidas y Refrescos",
        "Salsas y Conservas",
        "Lácteos y Derivados",
        "Repostería, Dulces y Licores",
        "Pecuario y Acuícola",
    ]
    campo_categoria = ft.Dropdown(
        label="Categoría",
        width=340,
        options=[ft.dropdown.Option(item) for item in categoria_options],
    )

    # Panel de solo lectura que muestra los datos del producto seleccionado
    # antes de decidir si se usa o se edita
    info_producto = ft.Column(
        [
            ft.Text("Datos del producto seleccionado", size=14, weight="bold"),
            ft.Text("", size=13),  # nombre
            ft.Text("", size=13),  # unidad
            ft.Text("", size=13),  # empresa/lugar
            ft.Text("", size=13),  # precio
            ft.Text("", size=13),  # stock
            ft.Text("", size=13),  # descripción
            ft.Text("", size=13),  # categoría
        ],
        visible=False,
        spacing=6,
    )

    # Formulario editable con los campos del producto para modificar antes de usar
    form_edicion = ft.Column(
        [
            ft.Text("Verificar y editar datos del producto", size=13, weight="bold"),
            campo_nombre, campo_unidad, campo_lugar, campo_precio, campo_stock, campo_descripcion, campo_categoria,
        ],
        visible=False,
        spacing=10,
    )

    # Botones de opciones: "Usar sin editar" o "Editar →"
    botones_opciones = ft.Row(
        [
            ft.Button(
                      "Usar sin editar ✓", width=230, bgcolor=ft.Colors.AMBER,
                      color=ft.Colors.BLACK,
                      style=ft.ButtonStyle(
                          bgcolor={
                              ft.ControlState.DEFAULT: ft.Colors.AMBER,
                              ft.ControlState.HOVERED: ft.Colors.AMBER_800,
                              ft.ControlState.FOCUSED: ft.Colors.AMBER_800,
                          },
                          color={
                              ft.ControlState.DEFAULT: ft.Colors.BLACK,
                              ft.ControlState.HOVERED: ft.Colors.WHITE,
                              ft.ControlState.FOCUSED: ft.Colors.WHITE,
                          },
                          side={
                              ft.ControlState.HOVERED: ft.BorderSide(3, ft.Colors.BLACK),
                              ft.ControlState.FOCUSED: ft.BorderSide(3, ft.Colors.BLACK),
                          },
                          elevation={
                              ft.ControlState.DEFAULT: 2,
                              ft.ControlState.HOVERED: 8,
                              ft.ControlState.FOCUSED: 8,
                          },
                          animation_duration=150,
                      ),
                      on_click=lambda _: usar_producto_sin_editar()),
            ft.Button("Editar →", width=180, bgcolor=ft.Colors.BLUE,
                      color=ft.Colors.WHITE,
                      style=ft.ButtonStyle(
                          bgcolor={
                              ft.ControlState.DEFAULT: ft.Colors.BLUE,
                              ft.ControlState.HOVERED: ft.Colors.BLUE_900,
                              ft.ControlState.FOCUSED: ft.Colors.BLUE_900,
                          },
                          side={
                              ft.ControlState.HOVERED: ft.BorderSide(3, ft.Colors.BLACK),
                              ft.ControlState.FOCUSED: ft.BorderSide(3, ft.Colors.BLACK),
                          },
                          elevation={
                              ft.ControlState.DEFAULT: 2,
                              ft.ControlState.HOVERED: 8,
                              ft.ControlState.FOCUSED: 8,
                          },
                          animation_duration=150,
                      ),
                      on_click=lambda _: mostrar_formulario_edicion()),
        ], visible=False, spacing=10, alignment=ft.MainAxisAlignment.CENTER,
    )

    # Botones de edición: "Confirmar ✓" o "Cancelar ✗"
    botones_edicion = ft.Row(
        [
            ft.Button("Confirmar ✓", width=230, bgcolor=ft.Colors.GREEN,
                      color=ft.Colors.WHITE,
                      style=ft.ButtonStyle(
                          bgcolor={
                              ft.ControlState.DEFAULT: ft.Colors.GREEN,
                              ft.ControlState.HOVERED: ft.Colors.GREEN_800,
                              ft.ControlState.FOCUSED: ft.Colors.GREEN_800,
                          },
                          side={
                              ft.ControlState.HOVERED: ft.BorderSide(3, ft.Colors.BLACK),
                              ft.ControlState.FOCUSED: ft.BorderSide(3, ft.Colors.BLACK),
                          },
                          elevation={
                              ft.ControlState.DEFAULT: 2,
                              ft.ControlState.HOVERED: 8,
                              ft.ControlState.FOCUSED: 8,
                          },
                          animation_duration=150,
                      ),
                      on_click=lambda _: confirmar_producto_editado()),
            ft.Button("Cancelar ✗", width=180, bgcolor=ft.Colors.RED,
                      color=ft.Colors.WHITE,
                      style=ft.ButtonStyle(
                          bgcolor={
                              ft.ControlState.DEFAULT: ft.Colors.RED,
                              ft.ControlState.HOVERED: ft.Colors.RED_800,
                              ft.ControlState.FOCUSED: ft.Colors.RED_800,
                          },
                          side={
                              ft.ControlState.HOVERED: ft.BorderSide(3, ft.Colors.BLACK),
                              ft.ControlState.FOCUSED: ft.BorderSide(3, ft.Colors.BLACK),
                          },
                          elevation={
                              ft.ControlState.DEFAULT: 2,
                              ft.ControlState.HOVERED: 8,
                              ft.ControlState.FOCUSED: 8,
                          },
                          animation_duration=150,
                      ),
                      on_click=lambda _: volver_a_resultados()),
        ], visible=False, spacing=10, alignment=ft.MainAxisAlignment.CENTER,
    )

    # -------- FUNCIONES --------

    def limpiar_resultados():
        """
        Reinicia el estado del diálogo a la fase de búsqueda.
        Limpia la lista de resultados, oculta paneles secundarios
        y restaura el campo de búsqueda.
        """
        nonlocal productos_encontrados, index_seleccionado, fase, botones_resultado

        # Reinicio datos de busqueda
        productos_encontrados = []
        botones_resultado = []
        index_seleccionado = 0
        fase = "buscar"

        # Activo otra vez el campo por si estaba bloqueado
        campo_busqueda.disabled = False
        campo_busqueda.visible = True

        # Limpio la lista visual
        resultados_container.controls.clear()
        resultados_container.visible = True
        info_producto.visible = False
        form_edicion.visible = False
        botones_opciones.visible = False
        botones_edicion.visible = False
        campo_cantidad.visible = False
        mensaje.value = "Presiona Enter para buscar"
        pagina.update()

    async def enfocar_producto(posicion=0):
        """
        Coloca el foco en un botón de producto específico.
        Se ejecuta de forma asíncrona porque el foco puede fallar
        si el diálogo se cerró mientras se esperaba.
        """
        if botones_resultado and 0 <= posicion < len(botones_resultado):
            try:
                await botones_resultado[posicion].focus()
            except RuntimeError:
                # La página o el diálogo se cerró mientras se esperaba el
                # foco. No hay nada que actualizar en ese caso.
                return

    def marcar_producto(posicion):
        """
        Marca un producto como seleccionado sin redibujar la lista.
        Esto evita invalidar las referencias de foco cuando se mantiene
        pulsada una flecha.
        """
        nonlocal index_seleccionado

        # Solo marco productos en la fase de resultados
        if fase != "resultados" or not productos_encontrados:
            return

        # No se vuelve a pintar toda la lista al cambiar el foco. Al mantener
        # una flecha pulsada, redibujar los botones invalida sus referencias y
        # genera tareas de foco pendientes.
        if index_seleccionado != posicion:
            index_seleccionado = posicion

    def hover_producto(e, posicion):
        """Marca y enfoca un producto cuando el mouse pasa por encima."""
        if e.data == "true":
            marcar_producto(posicion)
            pagina.run_task(enfocar_producto, posicion)

    def mover_foco_producto(nuevo_index):
        """
        Mueve la selección entre productos con las flechas del teclado.
        Redibuja la lista para resaltar el producto seleccionado.
        """
        nonlocal index_seleccionado

        # Si no hay productos no hago nada
        if not productos_encontrados:
            return

        # Limito el indice para que no se salga de la lista
        index_seleccionado = max(0, min(nuevo_index, len(productos_encontrados) - 1))

        # Pinto otra vez y enfoco el producto seleccionado
        renderizar_resultados()
        pagina.run_task(enfocar_producto, index_seleccionado)

    def renderizar_resultados():
        """
        Dibuja los productos encontrados como botones dentro del contenedor
        de resultados. Cada botón muestra: número de posición, nombre y
        precio/unidad.
        """
        nonlocal botones_resultado

        # Limpio botones anteriores
        resultados_container.controls.clear()
        botones_resultado = []

        # Si no encontro productos muestro mensaje
        if not productos_encontrados:
            mensaje.value = "No se encontraron productos"
            pagina.update()
            return

        mensaje.value = ""

        # Creo un boton por cada producto encontrado
        for i, prod in enumerate(productos_encontrados):

            unidad = prod.get('unidad', 'UND')

            # Calcula el precio final aplicando la oferta vigente del producto,
            # para mostrar el descuento correcto en los resultados de búsqueda.
            precio_mostrar = ventas_controller.calcular_precio_oferta(
                prod.get('precio', 0),
                prod.get('descuento', 0),
                prod.get('fecha_inicio_oferta'),
                prod.get('fecha_fin_oferta'),
            )

            # Muestro precio (con oferta aplicada) o solo unidad según la configuración
            detalle_producto = (
                f"${precio_mostrar:,.2f} / {unidad}"
                if mostrar_precio
                else str(unidad)
            )

            # Boton del producto con layout: [número] nombre  precio/unidad
            btn = ft.Button(
                content=ft.Row([
                    ft.Text(f"[{i + 1}]", size=12, width=30),
                    ft.Text(
                        prod.get('nombre', 'Sin nombre'),
                        expand=True,
                        color=ft.Colors.BLACK
                    ),
                    ft.Text(
                        detalle_producto,
                        size=12,
                        width=110,
                        color=ft.Colors.BLACK
                    )
                ]),
                width=440,
                height=30,
                bgcolor=ft.Colors.WHITE,
                color=ft.Colors.BLACK,

                # Estilo azul cuando el boton tiene hover o foco
                style=ft.ButtonStyle(
                    bgcolor={
                        ft.ControlState.HOVERED: ft.Colors.BLUE,
                        ft.ControlState.FOCUSED: ft.Colors.BLUE,
                        ft.ControlState.DEFAULT: ft.Colors.WHITE,
                    },
                    color={
                        ft.ControlState.HOVERED: ft.Colors.WHITE,
                        ft.ControlState.FOCUSED: ft.Colors.WHITE,
                        ft.ControlState.DEFAULT: ft.Colors.BLACK,
                    },
                    overlay_color=ft.Colors.BLUE_700,
                    shape=ft.RoundedRectangleBorder(radius=5),
                ),

                # Eventos del boton de producto
                on_focus=lambda _, pos=i: marcar_producto(pos),
                on_hover=lambda e, pos=i: hover_producto(e, pos),
                on_click=lambda _, pos=i: seleccionar_producto(pos)
            )

            # Guardo el boton para poder enfocarlo con el teclado
            botones_resultado.append(btn)

            # Agrego el boton a la lista visual
            resultados_container.controls.append(btn)

        pagina.update()

    def actualizar_resultados():
        """
        Ejecuta la búsqueda en la base de datos según el texto escrito
        por el usuario. Actualiza la lista de resultados y cambia la
        fase del diálogo.
        """
        nonlocal productos_encontrados, index_seleccionado, fase, botones_resultado

        # Tomo el texto escrito por el usuario
        texto = campo_busqueda.value.strip()

        # Si esta vacio limpio todo y no busco
        if len(texto) < 1:
            resultados_container.controls.clear()
            productos_encontrados = []
            botones_resultado = []
            index_seleccionado = 0
            fase = "buscar"
            campo_busqueda.disabled = False
            mensaje.value = ""
            pagina.update()
            return

        try:
            # Consulto productos en la base de datos
            productos_db = buscar_producto(texto)
            productos_encontrados = productos_db if productos_db else []

            # Inicio la seleccion en el primer producto
            index_seleccionado = 0

            # Si hay productos paso a resultados, si no sigo en buscar
            fase = "resultados" if productos_encontrados else "buscar"

            # Bloqueo el campo de busqueda cuando ya hay resultados
            campo_busqueda.disabled = bool(productos_encontrados)

            # Pinto la lista de productos
            renderizar_resultados()

        except Exception as err:
            # Muestro errores de la busqueda
            mensaje.value = f"Error en busqueda: {str(err)}"
            pagina.update()

    def seleccionar_producto(posicion=None):
        """
        Selecciona un producto de la lista y pasa a la fase de opciones
        donde el usuario puede elegir usarlo sin editar o editarlo.
        """
        nonlocal producto_seleccionado, producto_datos_editables, fase, index_seleccionado

        # Si llega una posicion por click la uso como seleccion actual
        if posicion is not None:
            index_seleccionado = posicion

        # Valido que exista un producto seleccionado
        if not productos_encontrados or index_seleccionado >= len(productos_encontrados):
            return

        # Guardo el producto seleccionado
        producto_seleccionado = productos_encontrados[index_seleccionado]
        producto_datos_editables = producto_seleccionado.copy()

        mostrar_opciones_edicion()

    def mostrar_opciones_edicion():
        """
        Muestra los datos del producto seleccionado en un panel de solo
        lectura, con los botones "Usar sin editar" y "Editar →".
        """
        nonlocal fase

        fase = "opciones"
        # Cargo los datos del producto en el panel informativo
        info_producto.controls[1].value = f"Nombre: {producto_datos_editables.get('nombre', '')}"
        info_producto.controls[2].value = f"Unidad: {producto_datos_editables.get('unidad', '')}"
        info_producto.controls[3].value = f"Empresa/Lugar: {producto_datos_editables.get('lugar', '')}"
        # Precio base y, si hay oferta vigente, el precio final con el descuento aplicado
        _base = float(producto_datos_editables.get('precio', 0))
        _fin = ventas_controller.calcular_precio_oferta(
            _base,
            producto_datos_editables.get('descuento', 0),
            producto_datos_editables.get('fecha_inicio_oferta'),
            producto_datos_editables.get('fecha_fin_oferta'),
        )
        if _fin < _base - 0.0001:
            info_producto.controls[4].value = (
                f"Precio: ${_base:,.2f} → ${_fin:,.2f} "
                f"(-{producto_datos_editables.get('descuento', 0):.0f}% OFERTA)"
            )
        else:
            info_producto.controls[4].value = f"Precio: ${_base:,.2f}"
        info_producto.controls[5].value = f"Stock: {producto_datos_editables.get('stock', 0)}"
        info_producto.controls[6].value = f"Descripción: {producto_datos_editables.get('descripcion', '') or 'Sin descripción'}"
        info_producto.controls[7].value = f"Categoría: {producto_datos_editables.get('categoria', 'Abonos y Sustratos')}"

        # Oculto la búsqueda y muestro la info del producto
        campo_busqueda.visible = False
        resultados_container.visible = False
        mensaje.value = ""
        info_producto.visible = True
        botones_opciones.visible = True
        pagina.update()

    def mostrar_formulario_edicion():
        """
        Muestra el formulario editable con los datos del producto,
        permitiendo al usuario modificar cualquier campo antes de usarlo.
        """
        nonlocal fase

        fase = "edicion"
        # Cargo los datos actuales en los campos editables
        campo_nombre.value = producto_datos_editables.get('nombre', '')
        campo_unidad.value = producto_datos_editables.get('unidad', '')
        campo_lugar.value = producto_datos_editables.get('lugar', '')
        campo_precio.value = str(producto_datos_editables.get('precio', 0))
        campo_stock.value = str(producto_datos_editables.get('stock', 0))
        campo_descripcion.value = producto_datos_editables.get('descripcion', '')
        campo_categoria.value = producto_datos_editables.get('categoria', 'Abonos y Sustratos')

        # Oculto panel informativo y opciones, muestro formulario
        info_producto.visible = False
        botones_opciones.visible = False
        form_edicion.visible = True
        botones_edicion.visible = True
        pagina.update()
        # Enfoco el primer campo del formulario
        pagina.run_task(enfocar_campo, campo_nombre)

    async def enfocar_campo(campo):
        """Coloca el foco en un campo de texto de forma asíncrona."""
        await campo.focus()

    def confirmar_producto_editado():
        """
        Valida y guarda los cambios editados del producto en la base de datos.
        Si todo está correcto, muestra notificación y pasa a la fase de cantidad.
        """
        nonlocal producto_seleccionado
        try:
            # Leo los valores de los campos y los guardo en el diccionario
            producto_datos_editables['nombre'] = campo_nombre.value.strip()
            producto_datos_editables['unidad'] = campo_unidad.value.strip()
            producto_datos_editables['lugar'] = campo_lugar.value.strip()
            producto_datos_editables['precio'] = float(campo_precio.value.replace(',', '.'))
            producto_datos_editables['stock'] = float(campo_stock.value.replace(',', '.'))
            producto_datos_editables['descripcion'] = campo_descripcion.value.strip()
            producto_datos_editables['categoria'] = campo_categoria.value.strip() if campo_categoria.value else 'Abonos y Sustratos'

            # Valido campos obligatorios
            if not producto_datos_editables['nombre'] or not producto_datos_editables['unidad']:
                raise ValueError("Nombre y unidad son obligatorios")

            # Guardo los cambios en la base de datos
            actualizar_producto(producto_datos_editables)
            producto_seleccionado = producto_datos_editables.copy()
            mostrar_notificacion(pagina, "Producto actualizado correctamente.")
            mostrar_cantidad()
        except ValueError as err:
            mensaje.value = str(err) or "Precio y stock deben ser números válidos"
            pagina.update()

    def usar_producto_sin_editar():
        """Salta directamente a la fase de cantidad sin editar el producto."""
        mostrar_cantidad()

    def volver_a_resultados():
        """Regresa a la lista de resultados de búsqueda desde las opciones o edición."""
        nonlocal fase
        fase = "resultados"
        form_edicion.visible = False
        botones_edicion.visible = False
        info_producto.visible = False
        botones_opciones.visible = False
        campo_busqueda.visible = True
        resultados_container.visible = True
        pagina.update()
        pagina.run_task(enfocar_producto, index_seleccionado)

    def mostrar_cantidad():
        """
        Muestra el campo para ingresar la cantidad del producto.
        Oculta todos los demás paneles y enfoca el campo de cantidad.
        """
        nonlocal fase

        # Oculto busqueda y resultados
        campo_busqueda.visible = False
        resultados_container.visible = False
        info_producto.visible = False
        botones_opciones.visible = False
        form_edicion.visible = False
        botones_edicion.visible = False

        # Muestro el campo para cantidad, ajustando la etiqueta con la unidad
        unidad = producto_seleccionado.get('unidad', 'UND')
        campo_cantidad.label = f"Cantidad en {unidad}"
        campo_cantidad.visible = True
        mensaje.value = f"Seleccionaste: {producto_seleccionado.get('nombre')}. Ingresa cantidad en {unidad}:"
        fase = "cantidad"

        # Enfoco cantidad para escribir y confirmar con Enter
        pagina.run_task(enfocar_cantidad)
        pagina.update()

    async def enfocar_cantidad():
        """Coloca el foco en el campo de cantidad de forma asíncrona."""
        await campo_cantidad.focus()

    def confirmar_cantidad():
        """
        Procesa la cantidad ingresada, calcula el subtotal y envía
        el producto completo a la tabla de vender.py. Luego cierra el diálogo.
        """
        nonlocal producto_seleccionado, fase, producto_confirmado

        # Si ya se confirmo, no dejo agregar otra vez
        if producto_confirmado:
            return

        try:
            # Tomo la cantidad escrita o uso 1 por defecto
            cantidad = float(campo_cantidad.value.replace(",", ".")) if campo_cantidad.value else 1

            # Valido que la cantidad sea mayor a cero
            if cantidad <= 0:
                mensaje.value = "La cantidad debe ser mayor a 0"
                pagina.update()
                return

            # Guardo cantidad y subtotal dentro del producto
            producto_seleccionado['cantidad'] = int(cantidad) if cantidad.is_integer() else cantidad
            producto_seleccionado['subtotal'] = cantidad * float(producto_seleccionado.get('precio', 0))

            # Aseguro que tenga el campo 'id' para la tabla de vender.py
            if 'id' not in producto_seleccionado and 'id_producto' in producto_seleccionado:
                producto_seleccionado['id'] = producto_seleccionado['id_producto']

            # Marco confirmado y envio el producto a la tabla de vender.py
            producto_confirmado = True
            agregar_producto_a_tabla(producto_seleccionado)
            cerrar_dialogo()

        except ValueError:
            # Si la cantidad no es valida muestro error
            mensaje.value = "Ingresa un numero valido"
            pagina.update()

    def cerrar_dialogo():
        """
        Cierra el diálogo y restaura el handler de teclado de la vista anterior.
        Usa una bandera para evitar que se cierre más de una vez.
        """
        nonlocal dialogo_cerrado

        # Evito cerrar dos veces
        if dialogo_cerrado:
            return

        dialogo_cerrado = True
        dialog.open = False

        # Devuelvo el teclado a la vista que estaba antes
        if pagina.on_keyboard_event == teclado_pagina:
            pagina.on_keyboard_event = teclado_anterior

        pagina.update()

    def cancelar(e=None):
        """Cierra el diálogo sin seleccionar ningún producto."""
        cerrar_dialogo()

    async def teclado(e: ft.KeyboardEvent):
        """
        Handler de teclado del diálogo.

        - Escape: cierra el diálogo.
        - En fase "resultados", las flechas no están habilitadas para evitar
          desestabilizar el diálogo al redibujar con muchas coincidencias.
          Los productos se seleccionan directamente con clic.
        """
        # Escape cierra el dialogo
        if e.key == "Escape":
            cancelar()
            return

        # En resultados no se redibuja la lista al usar flechas. Con muchas
        # coincidencias ese redibujado podía desestabilizar el diálogo; los
        # productos quedan visibles para seleccionarlos directamente con clic.
        if fase == "resultados":
            return

    async def teclado_pagina(e: ft.KeyboardEvent):
        """Wrapper del handler de teclado para la página."""
        await teclado(e)

    # -------- DIALOG --------

    # Dialogo que contiene busqueda, resultados y cantidad
    dialog = ft.AlertDialog(
        title=ft.Text("Buscar Producto (F3)"),
        content=ft.Column([
            campo_busqueda,
            ft.Text("Resultados:", size=13, weight="bold"),
            resultados_container,
            info_producto,
            botones_opciones,
            form_edicion,
            botones_edicion,
            campo_cantidad,
            mensaje
        ], height=650, width=460, scroll=ft.ScrollMode.AUTO),
        on_dismiss=cancelar
    )

    # Reemplazo temporalmente el teclado de vender.py
    pagina.on_keyboard_event = teclado_pagina

    # Retorno el dialogo para que vender.py lo abra
    return dialog
