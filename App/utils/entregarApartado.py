import flet as ft
from controllers import ventasController as ventas_controller


# ============================================================================
# MÓDULO DE ENTREGA DE APARTADOS WEB EN EL POS
# ============================================================================
# Diálogo modal que lista los apartados web pendientes de entrega (estado
# 'pendiente' o 'confirmado') y permite al cajero seleccionar uno para
# entregarlo en el punto de venta.
#
# Al seleccionar un apartado se llama al callback `on_apartado_seleccionado`
# con el registro del apartado (que ya trae unido los datos del producto).
# La vista vender.py se encarga de precargar el producto con la cantidad
# reservada y de asociar el id_apartado a la factura.
#
# Dependencias:
#   - controllers.ventasController.obtener_apartados_pendientes()
# ============================================================================


def entregar_apartado_view(pagina: ft.Page, on_apartado_seleccionado):
    """
    Crea el diálogo de entrega de apartados web.

    Parámetros:
        pagina (ft.Page): Página de Flet donde se mostrará el diálogo.
        on_apartado_seleccionado (callable): Función que recibe el diccionario
            del apartado seleccionado para precargarlo en la venta.

    Retorna:
        ft.AlertDialog: Componente de diálogo listo para mostrarse en vender.py.
    """

    # ---------------- ESTADO ----------------

    # Apartados pendientes obtenidos de la base de datos
    apartados = []

    # Evita que el diálogo se cierre más de una vez
    dialogo_cerrado = False

    # ---------------- CONTROLES ----------------

    # Contenedor donde se listan los apartados pendientes
    lista_apartados = ft.Column(
        scroll=ft.ScrollMode.AUTO,
        spacing=4,
    )

    # Texto para mensajes de ayuda o errores
    mensaje = ft.Text("", size=12, color="red")

    # ---------------- FUNCIONES ----------------

    def renderizar_apartados():
        """
        Dibuja cada apartado pendiente como un botón con el cliente,
        el producto y la cantidad reservada.
        """
        # Limpio la lista visual
        lista_apartados.controls.clear()

        # Consulto los apartados pendientes de la base de datos
        try:
            datos = ventas_controller.obtener_apartados_pendientes()
            apartados.extend(datos if datos else [])
        except Exception as err:
            print(f"Error al obtener apartados: {err}")
            mensaje.value = f"Error al cargar apartados: {err}"
            pagina.update()
            return

        if not apartados:
            mensaje.value = "No hay apartados pendientes de entrega."
            pagina.update()
            return

        mensaje.value = ""

        # Creo un botón por cada apartado
        for i, ap in enumerate(apartados):
            cliente = ap.get('nombre_cliente', 'Cliente')
            producto = ap.get('nombre', 'Producto')
            cantidad = ap.get('cantidad', 0)
            unidad = ap.get('unidad', 'UND')
            precio = ap.get('precio', 0)
            # El precio que cobrará el POS es el precio_aplicado (con descuento)
            # que se capturó al apartar en la web. Si no existe, se muestra el
            # precio actual del producto.
            precio_aplicado = ap.get('precio_aplicado')
            precio_mostrar = (
                float(precio_aplicado)
                if precio_aplicado is not None
                else float(precio)
            )

            btn = ft.Button(
                content=ft.Column([
                    ft.Text(
                        f"[{i + 1}] {cliente}",
                        size=13,
                        weight="bold",
                        color=ft.Colors.BLACK
                    ),
                    ft.Text(
                        f"{producto} - {cantidad} {unidad}  (${precio_mostrar:,.2f}/{unidad})",
                        size=12,
                        color=ft.Colors.BLACK
                    ),
                ], spacing=2),
                width=460,
                bgcolor=ft.Colors.WHITE,
                color=ft.Colors.BLACK,
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
                on_click=lambda _, ap=ap: seleccionar_apartado(ap)
            )

            lista_apartados.controls.append(btn)

        pagina.update()

    def seleccionar_apartado(apartado):
        """
        Envía el apartado seleccionado a vender.py y cierra el diálogo.
        """
        on_apartado_seleccionado(apartado)
        cerrar_dialogo()

    def cerrar_dialogo():
        """
        Cierra el diálogo y restaura el handler de teclado de la vista anterior.
        """
        nonlocal dialogo_cerrado

        if dialogo_cerrado:
            return

        dialogo_cerrado = True
        dialog.open = False

        # Devuelvo el teclado a la vista que estaba antes
        if pagina.on_keyboard_event == teclado_pagina:
            pagina.on_keyboard_event = teclado_anterior

        pagina.update()

    def cancelar(e=None):
        """Cierra el diálogo sin seleccionar ningún apartado."""
        cerrar_dialogo()

    async def teclado(e: ft.KeyboardEvent):
        """Handler de teclado del diálogo: Escape cierra el diálogo."""
        if e.key == "Escape":
            cancelar()
            return

    async def teclado_pagina(e: ft.KeyboardEvent):
        """Wrapper del handler de teclado para la página."""
        await teclado(e)

    # Guardo el teclado anterior para restaurarlo al cerrar el diálogo
    teclado_anterior = pagina.on_keyboard_event

    # ---------------- DIALOG ----------------

    dialog = ft.AlertDialog(
        title=ft.Text("Entregar Apartado Web (F9)"),
        content=ft.Column([
            ft.Text(
                "Selecciona el apartado que se va a entregar:",
                size=13,
                weight="bold"
            ),
            lista_apartados,
            mensaje
        ], width=500, height=500, scroll=ft.ScrollMode.AUTO),
        on_dismiss=cancelar
    )

    # Reemplazo temporalmente el teclado de vender.py
    pagina.on_keyboard_event = teclado_pagina

    # Pinto la lista de apartados pendientes
    renderizar_apartados()

    # Retorno el diálogo para que vender.py lo abra
    return dialog
