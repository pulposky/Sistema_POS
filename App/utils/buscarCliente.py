
import asyncio
import flet as ft
from models.ventasModel import buscar_cliente, actualizar_cliente
from utils.notificaciones import mostrar_notificacion

# Utilidad para buscar y seleccionar clientes desde una ventana emergente.


# Vista secundaria que abre el dialogo para buscar y seleccionar clientes
def buscar_cliente_view(pagina: ft.Page, mostrar_cliente_seleccionado):

    # ---------------- ESTADO ----------------

    # Lista de clientes encontrados en la base de datos
    clientes_encontrados = []

    # Posicion del cliente seleccionado con el teclado
    index_seleccionado = 0

    # Fase actual del dialogo: buscar, resultados o edición
    fase = "buscar"

    # Cliente que el usuario selecciona
    cliente_seleccionado = None

    # Datos editables del cliente
    cliente_datos_editables = {}

    # Guardo el teclado anterior para restaurarlo al cerrar el dialogo
    teclado_anterior = pagina.on_keyboard_event

    # Evita que el dialogo se cierre mas de una vez
    dialogo_cerrado = False

    # Lista de botones que representan los clientes encontrados
    botones_clientes = []

    # Evita seleccionar el mismo cliente dos veces
    cliente_confirmado = False

    # -------- CONTROLES --------

    # Campo donde el usuario escribe el nombre del cliente
    campo_busqueda = ft.TextField(
        label="Buscar cliente por nombre o cédula",
        width=340,
        autofocus=True,

        # Cuando cambia el texto limpio los resultados anteriores
        on_change=lambda e: limpiar_resultados(),

        # Si intenta tomar foco en resultados, lo regreso al cliente seleccionado
        on_focus=lambda _: pagina.run_task(enfocar_cliente, index_seleccionado) if fase == "resultados" else None,

        # Enter en este campo ejecuta la busqueda
        on_submit=lambda e: actualizar_resultados()
    )

    # Contenedor donde se muestran los botones de clientes encontrados
    resultados_container = ft.Column(
        scroll=ft.ScrollMode.AUTO,
        spacing=4,
    )

    # Texto para mostrar mensajes de ayuda o errores
    mensaje = ft.Text("", size=12, color="red")

    # Campos editables para los datos del cliente
    campo_nombre = ft.TextField(label="Nombre", width=340)
    campo_documento = ft.TextField(label="Documento", width=340)
    campo_rol = ft.TextField(label="Rol/Cargo", width=340)
    campo_direccion = ft.TextField(label="direccion", width=340)
    campo_telefono = ft.TextField(label="Teléfono", width=340)

    # Contenedor para los campos de edición
    form_edicion = ft.Column(
        [
            ft.Text("Verificar y editar datos del cliente", size=13, weight="bold"),
            campo_nombre,
            campo_documento,
            campo_rol,
            campo_direccion,
            campo_telefono,
        ],
        visible=False,
        spacing=10
    )

    # Contenedor de solo lectura que muestra los datos del cliente seleccionado
    # antes de decidir si se usa o se edita
    info_cliente = ft.Column(
        [
            ft.Text("Datos del cliente seleccionado", size=14, weight="bold"),
            ft.Text("", size=13),  # nombre
            ft.Text("", size=13),  # documento
            ft.Text("", size=13),  # rol
            ft.Text("", size=13),  # direccion
            ft.Text("", size=13),  # telefono
        ],
        visible=False,
        spacing=6
    )

    # Botones para confirmar o editar
    btn_confirmar_edicion = ft.Button(
        "Confirmar ✓",
        width=230,
        bgcolor=ft.Colors.GREEN,
        color=ft.Colors.WHITE,
        style=ft.ButtonStyle(
            bgcolor={
                ft.ControlState.DEFAULT: ft.Colors.GREEN,
                ft.ControlState.HOVERED: ft.Colors.GREEN_800,
                ft.ControlState.FOCUSED: ft.Colors.GREEN_800,
            },
            color=ft.Colors.WHITE,
            overlay_color=ft.Colors.GREEN_200,
            side={
                ft.ControlState.HOVERED: ft.BorderSide(3, ft.Colors.BLACK),
                ft.ControlState.FOCUSED: ft.BorderSide(3, ft.Colors.BLACK),
            },
            elevation={
                ft.ControlState.DEFAULT: 2,
                ft.ControlState.HOVERED: 8,
                ft.ControlState.FOCUSED: 8,
            },
            animation_duration=200
        ),
        on_click=lambda _: confirmar_cliente_editado()
    )

    btn_cancelar_edicion = ft.Button(
        "Cancelar ✗",
        width=180,
        bgcolor=ft.Colors.RED,
        color=ft.Colors.WHITE,
        style=ft.ButtonStyle(
            bgcolor={
                ft.ControlState.DEFAULT: ft.Colors.RED,
                ft.ControlState.HOVERED: ft.Colors.RED_800,
                ft.ControlState.FOCUSED: ft.Colors.RED_800,
            },
            color=ft.Colors.WHITE,
            overlay_color=ft.Colors.RED_200,
            side={
                ft.ControlState.HOVERED: ft.BorderSide(3, ft.Colors.BLACK),
                ft.ControlState.FOCUSED: ft.BorderSide(3, ft.Colors.BLACK),
            },
            elevation={
                ft.ControlState.DEFAULT: 2,
                ft.ControlState.HOVERED: 8,
                ft.ControlState.FOCUSED: 8,
            },
            animation_duration=200
        ),
        on_click=lambda _: volver_a_resultados()
    )

    btn_usar_sin_editar = ft.Button(
        "Usar sin editar ✓",
        width=230,
        bgcolor=ft.Colors.AMBER,
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
            overlay_color=ft.Colors.AMBER_200,
            side={
                ft.ControlState.HOVERED: ft.BorderSide(3, ft.Colors.BLACK),
                ft.ControlState.FOCUSED: ft.BorderSide(3, ft.Colors.BLACK),
            },
            elevation={
                ft.ControlState.DEFAULT: 2,
                ft.ControlState.HOVERED: 8,
                ft.ControlState.FOCUSED: 8,
            },
            animation_duration=200
        ),
        on_click=lambda _: usar_cliente_sin_editar()
    )

    botones_edicion = ft.Row(
        [btn_confirmar_edicion, btn_cancelar_edicion],
        visible=False,
        spacing=10,
        alignment=ft.MainAxisAlignment.CENTER
    )

    botones_opciones = ft.Row(
        [
            btn_usar_sin_editar,

            ft.Button(
                "Editar →",
                width=180,
                bgcolor=ft.Colors.BLUE,
                color=ft.Colors.WHITE,
                style=ft.ButtonStyle(
                    bgcolor={
                        ft.ControlState.DEFAULT: ft.Colors.BLUE,
                        ft.ControlState.HOVERED: ft.Colors.BLUE_900,
                        ft.ControlState.FOCUSED: ft.Colors.BLUE_900,
                    },
                    overlay_color=ft.Colors.BLUE_200,
                    side={
                        ft.ControlState.HOVERED: ft.BorderSide(3, ft.Colors.BLACK),
                        ft.ControlState.FOCUSED: ft.BorderSide(3, ft.Colors.BLACK),
                    },
                    elevation={
                        ft.ControlState.DEFAULT: 2,
                        ft.ControlState.HOVERED: 8,
                        ft.ControlState.FOCUSED: 8,
                    },
                    animation_duration=200
                ),
                on_click=lambda _: mostrar_formulario_edicion()
            )
        ],
        visible=False,
        spacing=10,
        alignment=ft.MainAxisAlignment.CENTER
    )

    # -------- FUNCIONES --------

    # Limpio los resultados cuando el usuario cambia la busqueda
    def limpiar_resultados():
        nonlocal clientes_encontrados, index_seleccionado, fase, botones_clientes

        # Reinicio datos de busqueda
        clientes_encontrados = []
        botones_clientes = []
        index_seleccionado = 0
        fase = "buscar"

        # Activo otra vez el campo por si estaba bloqueado
        campo_busqueda.disabled = False

        # Limpio la lista visual
        resultados_container.controls.clear()
        mensaje.value = "Presiona Enter para buscar"

        # Oculto el formulario de edición y el panel de info
        form_edicion.visible = False
        botones_edicion.visible = False
        info_cliente.visible = False

        pagina.update()

    # Coloco el foco en un boton de cliente
    async def enfocar_cliente(posicion=0):
        if botones_clientes and 0 <= posicion < len(botones_clientes):
            try:
                await botones_clientes[posicion].focus()
            except RuntimeError:
                return

    # Marco como seleccionado el cliente que recibe foco o hover
    def marcar_cliente(posicion):
        nonlocal index_seleccionado

        # Solo marco clientes en la fase de resultados
        if fase != "resultados" or not clientes_encontrados:
            return

        # No se vuelve a pintar toda la lista al cambiar el foco. Esto evita
        # tareas pendientes al mantener una flecha pulsada.
        if index_seleccionado != posicion:
            index_seleccionado = posicion

    # Cuando el mouse pasa por un cliente lo marco y lo enfoco
    def hover_cliente(e, posicion):
        if e.data == "true":
            marcar_cliente(posicion)
            pagina.run_task(enfocar_cliente, posicion)

    # Muevo el foco entre clientes con flecha arriba y flecha abajo
    def mover_foco_cliente(nuevo_index):
        nonlocal index_seleccionado

        # Si no hay clientes no hago nada
        if not clientes_encontrados:
            return

        # Limito el indice para que no se salga de la lista
        index_seleccionado = max(0, min(nuevo_index, len(clientes_encontrados) - 1))

        # Pinto otra vez y enfoco el cliente seleccionado
        renderizar_resultados()
        pagina.run_task(enfocar_cliente, index_seleccionado)

    # Pinto los clientes encontrados como botones
    def renderizar_resultados():
        nonlocal botones_clientes

        # Limpio botones anteriores
        resultados_container.controls.clear()
        botones_clientes = []

        # Si no encontro clientes muestro mensaje
        if not clientes_encontrados:
            mensaje.value = "No se encontraron clientes"
            pagina.update()
            return

        mensaje.value = ""

        # Creo un boton por cada cliente encontrado
        for i, cliente in enumerate(clientes_encontrados):

            # Boton del cliente
            btn = ft.Button(
                content=ft.Row([
                    ft.Text(f"[{i + 1}]", size=12, width=30),
                    ft.Text(
                        cliente.get('nombre', 'Sin nombre'),
                        expand=True,
                        color=ft.Colors.BLACK
                    ),
                    ft.Text(
                        str(cliente.get('documento', cliente.get('id', ''))),
                        size=12,
                        width=100,
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

                # Eventos del boton de cliente
                on_focus=lambda _, pos=i: marcar_cliente(pos),
                on_hover=lambda e, pos=i: hover_cliente(e, pos),
                on_click=lambda _, pos=i: seleccionar_cliente(pos)
            )

            # Guardo el boton para poder enfocarlo con el teclado
            botones_clientes.append(btn)

            # Agrego el boton a la lista visual
            resultados_container.controls.append(btn)

        pagina.update()

    # Busco clientes en la base de datos segun el texto escrito
    def actualizar_resultados():
        nonlocal clientes_encontrados, index_seleccionado, fase, botones_clientes

        # Tomo el texto escrito por el usuario
        texto = campo_busqueda.value.strip()

        # Si esta vacio limpio todo y no busco
        if len(texto) < 1:
            resultados_container.controls.clear()
            clientes_encontrados = []
            botones_clientes = []
            index_seleccionado = 0
            fase = "buscar"
            campo_busqueda.disabled = False
            mensaje.value = ""
            pagina.update()
            return

        try:
            # Consulto clientes en la base de datos
            clientes_db = buscar_cliente(texto)
            clientes_encontrados = clientes_db if clientes_db else []

            # Inicio la seleccion en el primer cliente
            index_seleccionado = 0

            # Si hay clientes paso a resultados, si no sigo en buscar
            fase = "resultados" if clientes_encontrados else "buscar"

            # Bloqueo el campo de busqueda cuando ya hay resultados
            campo_busqueda.disabled = bool(clientes_encontrados)

            # Pinto la lista de clientes
            renderizar_resultados()

        except Exception as err:
            # Muestro errores de la busqueda
            mensaje.value = f"Error en busqueda: {str(err)}"
            pagina.update()

    # Selecciono un cliente y lo envio a la vista de venta
    def seleccionar_cliente(posicion=None):
        nonlocal cliente_seleccionado, index_seleccionado, cliente_confirmado, fase, cliente_datos_editables

        # Si llega una posicion por click la uso como seleccion actual
        if posicion is not None:
            index_seleccionado = posicion

        # Valido que exista un cliente seleccionado
        if not clientes_encontrados or index_seleccionado >= len(clientes_encontrados):
            return

        # Evito seleccionar dos veces el mismo cliente
        if cliente_confirmado:
            return

        # Guardo el cliente seleccionado
        cliente_seleccionado = clientes_encontrados[index_seleccionado]
        cliente_datos_editables = cliente_seleccionado.copy()

        # Muestro las opciones de editar o no editar
        mostrar_opciones_edicion()

    # Muestro el formulario con los datos del cliente
    def mostrar_formulario_edicion():
        nonlocal fase

        # Cambio a fase de edición
        fase = "edicion"

        # Cargo los datos en los campos editables
        campo_nombre.value = cliente_datos_editables.get('nombre', '')
        campo_documento.value = str(cliente_datos_editables.get('documento', ''))
        campo_rol.value = cliente_datos_editables.get('rol', '')
        campo_direccion.value = cliente_datos_editables.get('direccion', '')
        campo_telefono.value = cliente_datos_editables.get('telefono', '')

        # Oculto resultados, info y opciones
        resultados_container.visible = False
        campo_busqueda.visible = False
        botones_opciones.visible = False
        info_cliente.visible = False
        mensaje.value = ""

        # Muestro formulario
        form_edicion.visible = True
        botones_edicion.visible = True

        pagina.update()

        # Enfoco el primer campo
        pagina.run_task(enfocar, campo_nombre)

    # Enfoco un campo de texto de forma segura
    async def enfocar(campo: ft.TextField):
        for intento in range(2):
            try:
                await asyncio.sleep(0.01)
                await campo.focus()
                return
            except Exception as err:
                if intento == 0:
                    await asyncio.sleep(0.1)

    # Confirmo el cliente editado y lo envío a la vista principal
    def confirmar_cliente_editado():
        nonlocal cliente_confirmado

        # Actualizo los datos con los valores editados
        cliente_datos_editables['nombre'] = campo_nombre.value
        cliente_datos_editables['documento'] = campo_documento.value
        cliente_datos_editables['rol'] = campo_rol.value
        cliente_datos_editables['direccion'] = campo_direccion.value
        cliente_datos_editables['telefono'] = campo_telefono.value

        try:
            # Guardo los cambios en la base de datos
            actualizar_cliente(cliente_datos_editables)

            # Marco confirmado y muestro el cliente en la vista principal
            cliente_confirmado = True
            mostrar_cliente_seleccionado(cliente_datos_editables)
            cerrar_dialogo()
            mostrar_notificacion(pagina, "Cliente actualizado correctamente.")
        except Exception as err:
            # Muestro error si algo sale mal
            mensaje.value = f"Error al guardar: {str(err)}"
            pagina.update()

    # Vuelvo a los resultados sin confirmar
    def volver_a_resultados():
        nonlocal fase

        # Cambio a fase de resultados
        fase = "resultados"

        # Oculto formulario, info y opciones
        form_edicion.visible = False
        botones_edicion.visible = False
        botones_opciones.visible = False
        info_cliente.visible = False

        # Muestro resultados
        resultados_container.visible = True
        campo_busqueda.visible = True

        pagina.update()

        # Enfoco el cliente seleccionado
        pagina.run_task(enfocar_cliente, index_seleccionado)

    # Muestro las opciones de editar o no editar
    def mostrar_opciones_edicion():
        nonlocal fase

        # Cambio a fase de opciones
        fase = "opciones"

        # Cargo los datos del cliente en el panel de solo lectura
        info_cliente.controls[1].value = f"Nombre: {cliente_datos_editables.get('nombre', '')}"
        info_cliente.controls[2].value = f"Documento: {cliente_datos_editables.get('documento', '')}"
        info_cliente.controls[3].value = f"Rol/Cargo: {cliente_datos_editables.get('rol', '')}"
        info_cliente.controls[4].value = f"Dirección: {cliente_datos_editables.get('direccion', '')}"
        info_cliente.controls[5].value = f"Teléfono: {cliente_datos_editables.get('telefono', '')}"

        # Oculto resultados
        resultados_container.visible = False
        campo_busqueda.visible = False
        mensaje.value = ""

        # Muestro datos del cliente y opciones
        info_cliente.visible = True
        botones_opciones.visible = True

        pagina.update()

    # Uso el cliente sin editar sus datos
    def usar_cliente_sin_editar():
        nonlocal cliente_confirmado

        try:
            cliente_confirmado = True
            mostrar_cliente_seleccionado(cliente_datos_editables)
            cerrar_dialogo()
        except Exception as err:
            mensaje.value = f"Error: {str(err)}"
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

        # La lista queda completa y estable para seleccionar con clic.
        if fase == "resultados":
            return

    # Teclado temporal de la pagina mientras el dialogo esta abierto
    async def teclado_pagina(e: ft.KeyboardEvent):
        await teclado(e)

    # -------- DIALOG --------

    # Dialogo que contiene busqueda y resultados de clientes
    dialog = ft.AlertDialog(
        title=ft.Text("Buscar Cliente (F1)"),
        content=ft.Column([
            campo_busqueda,
            ft.Text("Resultados:", size=13, weight="bold"),
            resultados_container,
            mensaje,
            info_cliente,
            botones_opciones,
            form_edicion,
            botones_edicion
        ], height=650, width=460, scroll=ft.ScrollMode.AUTO),
        on_dismiss=cancelar
    )

    # Reemplazo temporalmente el teclado de vender.py
    pagina.on_keyboard_event = teclado_pagina

    # Retorno el dialogo para que vender.py lo abra
    return dialog
