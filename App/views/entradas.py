from datetime import date
import flet as ft

from controllers import entradasController
from utils.buscarProducto import buscar_producto_view
from utils.notificaciones import mostrar_notificacion


def entradas_view(pagina: ft.Page, ir_a_main, ir_a_menu, usuario):
    """Formulario sencillo para registrar aumentos de inventario sin precios."""
    pagina.clean()
    pagina.window.width = 900
    pagina.window.height = 650

    productos = []
    campo_fecha = ft.TextField(
        label="Fecha (AAAA-MM-DD)", value=date.today().isoformat(), width=180
    )
    campo_observacion = ft.TextField(
        label="Observación o motivo", multiline=True, min_lines=2, width=500
    )
    mensaje = ft.Text("", color=ft.Colors.RED)
    tabla = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Producto")),
            ft.DataColumn(ft.Text("Unidad")),
            ft.DataColumn(ft.Text("Cantidad")),
            ft.DataColumn(ft.Text("Acción")),
        ],
        rows=[],
    )

    def mostrar_mensaje(texto, error=True):
        mensaje.value = texto
        mensaje.color = ft.Colors.RED if error else ft.Colors.GREEN
        pagina.update()
        if texto:
            mostrar_notificacion(pagina, texto, error=error)

    def redibujar_tabla():
        tabla.rows.clear()
        for indice, producto in enumerate(productos):
            campo_cantidad = ft.TextField(
                value=str(producto["cantidad"]), width=100, text_align=ft.TextAlign.RIGHT
            )

            def cambiar_cantidad(event, idx=indice, campo=campo_cantidad):
                try:
                    entradasController.actualizar_cantidad_producto_entrada(
                        productos[idx], campo.value
                    )
                    mostrar_mensaje("", error=False)
                except ValueError as error:
                    mostrar_mensaje(str(error))
                    campo.value = str(productos[idx]["cantidad"])
                    pagina.update()

            campo_cantidad.on_change = cambiar_cantidad
            tabla.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(producto.get("nombre", "Sin nombre"))),
                        ft.DataCell(ft.Text(producto.get("unidad", "UND"))),
                        ft.DataCell(campo_cantidad),
                        ft.DataCell(
                            ft.IconButton(
                                icon=ft.Icons.DELETE_OUTLINE,
                                tooltip="Quitar producto",
                                on_click=lambda _, idx=indice: quitar_producto(idx),
                            )
                        ),
                    ]
                )
            )
        pagina.update()

    def agregar_producto(producto):
        # El buscador ya solicita una cantidad. No usamos ni guardamos precios.
        entradasController.agregar_producto_a_entrada(productos, producto)
        redibujar_tabla()

    def abrir_busqueda(_):
        dialogo = buscar_producto_view(pagina, agregar_producto, mostrar_precio=False)
        # Esta versión de Flet abre diálogos desde overlay, igual que
        # Compras, Ventas y Remisiones del proyecto.
        pagina.overlay.append(dialogo)
        dialogo.open = True
        pagina.update()

    def quitar_producto(indice):
        entradasController.quitar_producto_de_entrada(productos, indice)
        redibujar_tabla()

    def guardar_entrada(_):
        try:
            id_entrada = entradasController.guardar_nueva_entrada(
                campo_fecha.value, campo_observacion.value, productos, usuario
            )
            if not id_entrada:
                mostrar_mensaje("No fue posible guardar la entrada.")
                return

            productos.clear()
            campo_observacion.value = ""
            redibujar_tabla()
            mostrar_mensaje(f"Entrada #{id_entrada} guardada correctamente.", error=False)
        except ValueError as error:
            mostrar_mensaje(str(error))

    pagina.add(
        ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Entradas de inventario", size=22, weight="bold"),
                        ft.Button("Volver al menú", on_click=lambda _: ir_a_menu(usuario)),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Text("Las entradas suman stock; no modifican precio ni costo."),
                ft.Row([campo_fecha, campo_observacion], vertical_alignment=ft.CrossAxisAlignment.START),
                ft.Row([
                    ft.Button("Agregar producto", icon=ft.Icons.ADD, on_click=abrir_busqueda),
                    ft.Button("Guardar entrada", icon=ft.Icons.SAVE, on_click=guardar_entrada),
                ]),
                mensaje,
                ft.Container(
                    content=ft.Row([tabla], scroll=ft.ScrollMode.AUTO),
                    expand=True,
                    padding=10,
                    border=ft.Border.all(1, ft.Colors.GREY_300),
                ),
            ],
            expand=True,
            spacing=14,
        )
    )
