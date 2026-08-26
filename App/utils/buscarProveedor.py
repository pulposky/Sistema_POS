import asyncio
import flet as ft
from models.comprasModel import buscar_proveedor

# ============================================================================
# MÓDULO DE BÚSQUEDA Y SELECCIÓN DE PROVEEDORES
# ============================================================================
# Diálogo modal que permite buscar proveedores en la base de datos por
# nombre y seleccionar uno para asignarlo a una compra.
#
# Este es un diálogo más simple que buscarProducto o buscarCliente:
#   - Solo tiene fase de búsqueda y selección (sin edición).
#   - Al seleccionar un proveedor, lo envía directamente a compras.py.
#
# Flujo:
#   1. "buscar"     → El usuario escribe el nombre del proveedor y presiona Enter.
#   2. "resultados" → Se muestran los proveedores encontrados como botones.
#   3. Selección   → Al hacer clic o Enter, se selecciona y cierra el diálogo.
#
# Dependencias:
#   - models.comprasModel: función buscar_proveedor().
# ============================================================================


def buscar_proveedor_view(pagina: ft.Page, mostrar_proveedor_seleccionado):
    """
    Crea el diálogo de búsqueda de proveedores.

    Parámetros:
        pagina (ft.Page): Página de Flet donde se mostrará el diálogo.
        mostrar_proveedor_seleccionado (callable): Función callback que recibe
            un diccionario con los datos del proveedor seleccionado para
            asignarlo en la vista de compras.

    Retorna:
        ft.AlertDialog: Componente de diálogo listo para mostrarse.
    """

    # ---------------- ESTADO ----------------

    proveedores_encontrados = []
    index_seleccionado = 0
    fase = "buscar"

    proveedor_seleccionado = None

    teclado_anterior = pagina.on_keyboard_event
    dialogo_cerrado = False
    botones_proveedores = []

    # ---------------- CAMPOS ----------------

    # Campo de búsqueda: el usuario escribe el nombre del proveedor
    campo_busqueda = ft.TextField(
        label="Buscar proveedor por nombre",
        width=300,
        autofocus=True,
        # Al cambiar el texto, limpio los resultados anteriores
        on_change=lambda e: limpiar_resultados(),
        # Si el campo recibe foco estando en resultados, devuelvo el foco al proveedor seleccionado
        on_focus=lambda _: pagina.run_task(
            enfocar_proveedor,
            index_seleccionado
        ) if fase == "resultados" else None,
        # Enter ejecuta la búsqueda
        on_submit=lambda e: actualizar_resultados()
    )

    # Contenedor con scroll donde se muestran los botones de resultados
    resultados_container = ft.Column(
        scroll=ft.ScrollMode.AUTO,
        height=250
    )

    # Texto para mensajes de error o ayuda
    mensaje = ft.Text("", size=12, color="red")

    # ---------------- FUNCIONES ----------------

    def limpiar_resultados():
        """
        Reinicia el estado del diálogo a la fase de búsqueda.
        Limpia la lista de resultados y el campo de búsqueda.
        """
        nonlocal proveedores_encontrados
        nonlocal index_seleccionado
        nonlocal fase
        nonlocal botones_proveedores

        proveedores_encontrados = []
        botones_proveedores = []
        index_seleccionado = 0
        fase = "buscar"

        campo_busqueda.disabled = False
        resultados_container.controls.clear()
        mensaje.value = "Presiona Enter para buscar"
        pagina.update()

    async def enfocar_proveedor(posicion=0):
        """
        Coloca el foco en un botón de proveedor específico.
        Se ejecuta de forma asíncrona porque el foco puede fallar
        si el diálogo se cerró mientras se esperaba.
        """
        if botones_proveedores and 0 <= posicion < len(botones_proveedores):
            await botones_proveedores[posicion].focus()

    async def mantener_foco_proveedores():
        """
        Mantiene el foco en el proveedor seleccionado después de un blur.
        Se ejecuta con un pequeño delay para evitar condiciones de carrera
        cuando el foco sale de un botón y se pierde la selección.
        """
        await asyncio.sleep(0.05)

        if fase == "resultados" and not dialogo_cerrado:
            await enfocar_proveedor(index_seleccionado)

    def marcar_proveedor(posicion):
        """
        Marca un proveedor como seleccionado y redibuja la lista
        para resaltarlo visualmente.
        """
        nonlocal index_seleccionado

        if fase != "resultados":
            return

        if index_seleccionado != posicion:
            index_seleccionado = posicion
            renderizar_resultados()

    def hover_proveedor(e, posicion):
        """Marca y enfoca un proveedor cuando el mouse pasa por encima."""
        if e.data == "true":
            marcar_proveedor(posicion)
            pagina.run_task(enfocar_proveedor, posicion)

    def mover_foco_proveedor(nuevo_index):
        """
        Mueve la selección entre proveedores con las flechas del teclado.
        Redibuja la lista para resaltar el proveedor seleccionado.
        """
        nonlocal index_seleccionado

        if not proveedores_encontrados:
            return

        # Limito el índice para que no se salga de la lista
        index_seleccionado = max(
            0,
            min(nuevo_index, len(proveedores_encontrados) - 1)
        )

        renderizar_resultados()

        pagina.run_task(
            enfocar_proveedor,
            index_seleccionado
        )

    def renderizar_resultados():
        """
        Dibuja los proveedores encontrados como botones.
        El proveedor seleccionado se resalta en azul, los demás en blanco.
        """
        nonlocal botones_proveedores

        resultados_container.controls.clear()
        botones_proveedores = []

        if not proveedores_encontrados:
            mensaje.value = "No se encontraron proveedores"
            pagina.update()
            return
        mensaje.value = ""

        for i, proveedor in enumerate(proveedores_encontrados):
            # Determino si este proveedor es el seleccionado actualmente
            seleccionado = i == index_seleccionado
            btn = ft.Button(
                content=ft.Row([
                    ft.Text(f"[{i+1}]", width=30),
                    ft.Text(
                        proveedor.get("nombre", "Sin nombre"),
                        expand=True,
                        # Texto blanco si está seleccionado, negro si no
                        color=ft.Colors.WHITE if seleccionado else ft.Colors.BLACK
                    ),
                    ft.Text(
                        str(proveedor.get("id_proveedor", "")),
                        width=80,
                        color=ft.Colors.WHITE if seleccionado else ft.Colors.BLACK
                    )
                ]),

                width=380,
                # Fondo azul si está seleccionado, blanco si no
                bgcolor=ft.Colors.BLUE if seleccionado else ft.Colors.WHITE,
                style=ft.ButtonStyle(
                    bgcolor={
                        ft.ControlState.HOVERED: ft.Colors.BLUE,
                        ft.ControlState.FOCUSED: ft.Colors.BLUE,
                        ft.ControlState.DEFAULT:
                            ft.Colors.BLUE if seleccionado
                            else ft.Colors.WHITE
                    },
                    color={
                        ft.ControlState.HOVERED: ft.Colors.WHITE,
                        ft.ControlState.FOCUSED: ft.Colors.WHITE,
                        ft.ControlState.DEFAULT:
                            ft.Colors.WHITE if seleccionado
                            else ft.Colors.BLACK
                    }
                ),

                on_focus=lambda _, pos=i: marcar_proveedor(pos),
                on_blur=lambda _:
                    # Cuando pierde el foco, reestablezco el foco al proveedor seleccionado
                    pagina.run_task(
                        mantener_foco_proveedores
                    ),
                on_hover=lambda e, pos=i:
                    hover_proveedor(e, pos),
                on_click=lambda _, pos=i:
                    seleccionar_proveedor(pos)
            )

            botones_proveedores.append(btn)
            resultados_container.controls.append(btn)

        pagina.update()

    def actualizar_resultados():
        """
        Ejecuta la búsqueda de proveedores en la base de datos.
        Actualiza la lista de resultados y cambia la fase del diálogo.
        """
        nonlocal proveedores_encontrados
        nonlocal index_seleccionado
        nonlocal fase

        texto = campo_busqueda.value.strip()

        # Si el texto está vacío, limpio todo
        if len(texto) < 1:

            resultados_container.controls.clear()
            proveedores_encontrados = []
            botones_proveedores.clear()
            index_seleccionado = 0
            fase = "buscar"
            campo_busqueda.disabled = False
            mensaje.value = ""
            pagina.update()

            return

        try:
            # Consulto proveedores en la base de datos
            proveedores_db = buscar_proveedor(texto)
            proveedores_encontrados = (
                proveedores_db if proveedores_db else []
            )
            index_seleccionado = 0

            # Cambio de fase según si hay resultados
            fase = (
                "resultados"
                if proveedores_encontrados
                else "buscar"
            )
            # Bloqueo el campo de búsqueda si hay resultados
            campo_busqueda.disabled = bool(
                proveedores_encontrados
            )

            renderizar_resultados()

            # Si hay resultados, enfoco el primer proveedor
            if proveedores_encontrados:
                pagina.run_task(
                    enfocar_proveedor,
                    0
                )

        except Exception as err:
            mensaje.value = f"Error: {str(err)}"
            pagina.update()

    def seleccionar_proveedor(posicion=None):
        """
        Selecciona un proveedor de la lista, lo envía a la vista de
        compras y cierra el diálogo inmediatamente.
        """
        nonlocal proveedor_seleccionado
        nonlocal index_seleccionado
        if posicion is not None:
            index_seleccionado = posicion
        if not proveedores_encontrados:
            return
        proveedor_seleccionado = proveedores_encontrados[index_seleccionado]
        mostrar_proveedor_seleccionado(
            proveedor_seleccionado
        )

        cerrar_dialogo()

    def cerrar_dialogo():
        """
        Cierra el diálogo y restaura el handler de teclado anterior.
        Usa una bandera para evitar que se cierre más de una vez.
        """
        nonlocal dialogo_cerrado
        if dialogo_cerrado:
            return
        dialogo_cerrado = True
        dialog.open = False

        if pagina.on_keyboard_event == teclado_pagina:
            pagina.on_keyboard_event = teclado_anterior

        pagina.update()

    def cancelar(e=None):
        """Cierra el diálogo sin seleccionar ningún proveedor."""
        cerrar_dialogo()

    async def teclado(e: ft.KeyboardEvent):
        """
        Handler de teclado del diálogo.

        - Escape: cierra el diálogo.
        - ArrowDown: mueve la selección al siguiente proveedor.
        - ArrowUp: mueve la selección al proveedor anterior.
        - Enter: selecciona el proveedor actualmente resaltado.
        """
        if e.key == "Escape":
            cancelar()
            return
        if fase == "resultados":
            if e.key == "ArrowDown":
                mover_foco_proveedor(
                    index_seleccionado + 1
                )
            elif e.key == "ArrowUp":
                mover_foco_proveedor(
                    index_seleccionado - 1
                )
            elif e.key == "Enter":
                seleccionar_proveedor()

    async def teclado_pagina(e: ft.KeyboardEvent):
        """Wrapper del handler de teclado para la página."""
        await teclado(e)

    # ---------------- DIALOG ----------------

    dialog = ft.AlertDialog(
        title=ft.Text("Buscar proveedor (F1)"),
        content=ft.Column(
            [
                campo_busqueda,
                ft.Text(
                    "Resultados:",
                    size=13,
                    weight="bold"
                ),
                resultados_container,
                mensaje
            ],
            height=350,
            width=400
        ),
        on_dismiss=cancelar
    )
    # Reemplazo el teclado temporalmente para manejar flechas y Enter
    pagina.on_keyboard_event = teclado_pagina

    return dialog
