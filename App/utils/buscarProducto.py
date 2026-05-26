import asyncio
import flet as ft
from models.ventasModel import buscar_producto


# =========================================================
# VISTA PARA BUSCAR Y SELECCIONAR PRODUCTOS
# =========================================================
def buscar_producto_view(pagina: ft.Page, agregar_producto_a_tabla, mostrar_precio=True):

    # ---------------- ESTADO ----------------

    # Lista de productos encontrados en la base de datos
    productos_encontrados = []

    # Posicion del producto seleccionado con el teclado
    index_seleccionado = 0

    # Fase actual del dialogo: buscar, resultados o cantidad
    fase = "buscar"

    # Producto que el usuario selecciona antes de escribir cantidad
    producto_seleccionado = None

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
        width=300,
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
        height=200
    )

    # Texto para mostrar mensajes de ayuda o errores
    mensaje = ft.Text("", size=12, color="red")

    # -------- FUNCIONES --------

    # Limpio los resultados cuando el usuario cambia la busqueda
    def limpiar_resultados():
        nonlocal productos_encontrados, index_seleccionado, fase, botones_resultado

        # Reinicio datos de busqueda
        productos_encontrados = []
        botones_resultado = []
        index_seleccionado = 0
        fase = "buscar"

        # Activo otra vez el campo por si estaba bloqueado
        campo_busqueda.disabled = False

        # Limpio la lista visual
        resultados_container.controls.clear()
        mensaje.value = "Presiona Enter para buscar"
        pagina.update()

    # Coloco el foco en un boton de producto
    async def enfocar_producto(posicion=0):
        if botones_resultado and 0 <= posicion < len(botones_resultado):
            await botones_resultado[posicion].focus()

    # Mantengo el foco dentro de los productos cuando ya hay resultados
    async def mantener_foco_productos():
        await asyncio.sleep(0.05)
        if fase == "resultados" and not dialogo_cerrado:
            await enfocar_producto(index_seleccionado)

    # Marco como seleccionado el producto que recibe foco o hover
    def marcar_producto(posicion):
        nonlocal index_seleccionado

        # Solo marco productos en la fase de resultados
        if fase != "resultados" or not productos_encontrados:
            return

        # Si cambia la posicion, vuelvo a pintar los botones
        if index_seleccionado != posicion:
            index_seleccionado = posicion
            renderizar_resultados()

    # Cuando el mouse pasa por un producto lo marco y lo enfoco
    def hover_producto(e, posicion):
        if e.data == "true":
            marcar_producto(posicion)
            pagina.run_task(enfocar_producto, posicion)

    # Muevo el foco entre productos con flecha arriba y flecha abajo
    def mover_foco_producto(nuevo_index):
        nonlocal index_seleccionado

        # Si no hay productos no hago nada
        if not productos_encontrados:
            return

        # Limito el indice para que no se salga de la lista
        index_seleccionado = max(0, min(nuevo_index, len(productos_encontrados) - 1))

        # Pinto otra vez y enfoco el producto seleccionado
        renderizar_resultados()
        pagina.run_task(enfocar_producto, index_seleccionado)

    # Pinto los productos encontrados como botones
    def renderizar_resultados():
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

            # Verifico si este es el producto seleccionado
            seleccionado = i == index_seleccionado
            unidad = prod.get('unidad', 'UND')
            detalle_producto = (
                f"${prod.get('precio', 0)} / {unidad}"
                if mostrar_precio
                else str(unidad)
            )

            # Boton del producto
            btn = ft.Button(
                content=ft.Row([
                    ft.Text(f"[{i + 1}]", size=12, width=30),
                    ft.Text(
                        prod.get('nombre', 'Sin nombre'),
                        expand=True,
                        color=ft.Colors.WHITE if seleccionado else ft.Colors.BLACK
                    ),
                    ft.Text(
                        detalle_producto,
                        size=12,
                        width=110,
                        color=ft.Colors.WHITE if seleccionado else ft.Colors.BLACK
                    )
                ]),
                width=380,
                bgcolor=ft.Colors.BLUE if seleccionado else ft.Colors.WHITE,
                color=ft.Colors.WHITE if seleccionado else ft.Colors.BLACK,

                # Estilo azul cuando el boton tiene hover o foco
                style=ft.ButtonStyle(
                    bgcolor={
                        ft.ControlState.HOVERED: ft.Colors.BLUE,
                        ft.ControlState.FOCUSED: ft.Colors.BLUE,
                        ft.ControlState.DEFAULT: ft.Colors.BLUE if seleccionado else ft.Colors.WHITE,
                    },
                    color={
                        ft.ControlState.HOVERED: ft.Colors.WHITE,
                        ft.ControlState.FOCUSED: ft.Colors.WHITE,
                        ft.ControlState.DEFAULT: ft.Colors.WHITE if seleccionado else ft.Colors.BLACK,
                    },
                    overlay_color=ft.Colors.BLUE_700,
                    shape=ft.RoundedRectangleBorder(radius=5),
                ),

                # Eventos del boton de producto
                on_focus=lambda _, pos=i: marcar_producto(pos),
                on_blur=lambda _: pagina.run_task(mantener_foco_productos),
                on_hover=lambda e, pos=i: hover_producto(e, pos),
                on_click=lambda _, pos=i: seleccionar_producto(pos)
            )

            # Guardo el boton para poder enfocarlo con el teclado
            botones_resultado.append(btn)

            # Agrego el boton a la lista visual
            resultados_container.controls.append(btn)

        pagina.update()

    # Busco productos en la base de datos segun el texto escrito
    def actualizar_resultados():
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

            # Enfoco el primer producto encontrado
            if productos_encontrados:
                pagina.run_task(enfocar_producto, 0)

        except Exception as err:
            # Muestro errores de la busqueda
            mensaje.value = f"Error en busqueda: {str(err)}"
            pagina.update()

    # Selecciono un producto y paso a pedir cantidad
    def seleccionar_producto(posicion=None):
        nonlocal producto_seleccionado, fase, index_seleccionado

        # Si llega una posicion por click la uso como seleccion actual
        if posicion is not None:
            index_seleccionado = posicion

        # Valido que exista un producto seleccionado
        if not productos_encontrados or index_seleccionado >= len(productos_encontrados):
            return

        # Guardo el producto seleccionado
        producto_seleccionado = productos_encontrados[index_seleccionado]

        # Oculto busqueda y resultados
        campo_busqueda.visible = False
        resultados_container.visible = False

        # Muestro el campo para cantidad
        unidad = producto_seleccionado.get('unidad', 'UND')
        campo_cantidad.label = f"Cantidad en {unidad}"
        campo_cantidad.visible = True
        mensaje.value = f"Seleccionaste: {producto_seleccionado.get('nombre')}. Ingresa cantidad en {unidad}:"
        fase = "cantidad"

        # Enfoco cantidad para escribir y confirmar con Enter
        pagina.run_task(enfocar_cantidad)
        pagina.update()

    # Coloco el foco en el campo de cantidad
    async def enfocar_cantidad():
        await campo_cantidad.focus()

    # Confirmo la cantidad y envio el producto a vender.py
    def confirmar_cantidad():
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

    # Cierro el dialogo y restauro el teclado anterior
    def cerrar_dialogo():
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

    # Cancelo el dialogo
    def cancelar(e=None):
        cerrar_dialogo()

    # Manejo el teclado mientras el dialogo esta abierto
    async def teclado(e: ft.KeyboardEvent):

        # Escape cierra el dialogo
        if e.key == "Escape":
            cancelar()
            return

        # En resultados las flechas navegan entre botones
        if fase == "resultados":

            # Flecha abajo mueve al siguiente producto
            if e.key == "ArrowDown":
                if productos_encontrados:
                    mover_foco_producto(index_seleccionado + 1)

            # Flecha arriba mueve al producto anterior
            elif e.key == "ArrowUp":
                if productos_encontrados:
                    mover_foco_producto(index_seleccionado - 1)

    # Teclado temporal de la pagina mientras el dialogo esta abierto
    async def teclado_pagina(e: ft.KeyboardEvent):
        await teclado(e)

    # -------- DIALOG --------

    # Dialogo que contiene busqueda, resultados y cantidad
    dialog = ft.AlertDialog(
        title=ft.Text("Buscar Producto (F3)"),
        content=ft.Column([
            campo_busqueda,
            ft.Text("Resultados:", size=13, weight="bold"),
            resultados_container,
            campo_cantidad,
            mensaje
        ], height=350, width=400),
        on_dismiss=cancelar
    )

    # Reemplazo temporalmente el teclado de vender.py
    pagina.on_keyboard_event = teclado_pagina

    # Retorno el dialogo para que vender.py lo abra
    return dialog
