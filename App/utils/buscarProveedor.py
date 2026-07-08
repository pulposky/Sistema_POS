import asyncio
import flet as ft
from models.comprasModel import buscar_proveedor

# Utilidad para buscar proveedores desde la interfaz de compras.

def buscar_proveedor_view(pagina: ft.Page, mostrar_proveedor_seleccionado):

    proveedores_encontrados = []
    index_seleccionado = 0
    fase = "buscar"

    proveedor_seleccionado = None

    teclado_anterior = pagina.on_keyboard_event
    dialogo_cerrado = False
    botones_proveedores = []

    # ---------------- CAMPOS ----------------

    campo_busqueda = ft.TextField(
        label="Buscar proveedor por nombre",
        width=300,
        autofocus=True,
        on_change=lambda e: limpiar_resultados(),
        on_focus=lambda _: pagina.run_task(
            enfocar_proveedor,
            index_seleccionado
        ) if fase == "resultados" else None,
        on_submit=lambda e: actualizar_resultados()
    )

    resultados_container = ft.Column(
        scroll=ft.ScrollMode.AUTO,
        height=250
    )

    mensaje = ft.Text("", size=12, color="red")

    # ---------------- FUNCIONES ----------------

    def limpiar_resultados():
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
        if botones_proveedores and 0 <= posicion < len(botones_proveedores):
            await botones_proveedores[posicion].focus()

    async def mantener_foco_proveedores():
        await asyncio.sleep(0.05)

        if fase == "resultados" and not dialogo_cerrado:
            await enfocar_proveedor(index_seleccionado)

    def marcar_proveedor(posicion):
        nonlocal index_seleccionado

        if fase != "resultados":
            return

        if index_seleccionado != posicion:
            index_seleccionado = posicion
            renderizar_resultados()

    def hover_proveedor(e, posicion):
        if e.data == "true":
            marcar_proveedor(posicion)
            pagina.run_task(enfocar_proveedor, posicion)

    def mover_foco_proveedor(nuevo_index):
        nonlocal index_seleccionado

        if not proveedores_encontrados:
            return
        
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
        nonlocal botones_proveedores

        resultados_container.controls.clear()
        botones_proveedores = []

        if not proveedores_encontrados:
            mensaje.value = "No se encontraron proveedores"
            pagina.update()
            return
        mensaje.value = ""

        for i, proveedor in enumerate(proveedores_encontrados):
            seleccionado = i == index_seleccionado
            btn = ft.Button(
                content=ft.Row([
                    ft.Text(f"[{i+1}]", width=30),
                    ft.Text(
                        proveedor.get("nombre", "Sin nombre"),
                        expand=True,
                        color=ft.Colors.WHITE if seleccionado else ft.Colors.BLACK
                    ),
                    ft.Text(
                        str(proveedor.get("id_proveedor", "")),
                        width=80,
                        color=ft.Colors.WHITE if seleccionado else ft.Colors.BLACK
                    )
                ]),

                width=380,
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
        nonlocal proveedores_encontrados
        nonlocal index_seleccionado
        nonlocal fase

        texto = campo_busqueda.value.strip()

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
            proveedores_db = buscar_proveedor(texto)
            proveedores_encontrados = (
                proveedores_db if proveedores_db else []
            )
            index_seleccionado = 0

            fase = (
                "resultados"
                if proveedores_encontrados
                else "buscar"
            )
            campo_busqueda.disabled = bool(
                proveedores_encontrados
            )

            renderizar_resultados()

            if proveedores_encontrados:
                pagina.run_task(
                    enfocar_proveedor,
                    0
                )

        except Exception as err:
            mensaje.value = f"Error: {str(err)}"
            pagina.update()

    def seleccionar_proveedor(posicion=None):

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

        nonlocal dialogo_cerrado
        if dialogo_cerrado:
            return
        dialogo_cerrado = True
        dialog.open = False

        if pagina.on_keyboard_event == teclado_pagina:
            pagina.on_keyboard_event = teclado_anterior

        pagina.update()

    def cancelar(e=None):
        cerrar_dialogo()

    async def teclado(e: ft.KeyboardEvent):
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
    pagina.on_keyboard_event = teclado_pagina

    return dialog