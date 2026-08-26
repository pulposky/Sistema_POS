"""
Vista para registrar entradas de inventario.

Permite agregar productos al inventario sin modificar precios ni costos.
Cada entrada tiene una fecha, una observación y una lista de productos con cantidades.
El usuario busca productos con el diálogo de búsqueda (buscar_producto_view) y
modifica las cantidades directamente en la tabla. Al guardar, se crea un registro
de entrada en la base de datos a través de entradasController.

Esta vista está restringida a usuarios con rol Admin o Administrador.

Atajos de teclado:
    Escape -> Cierra diálogos abiertos o vuelve al menú principal.

Navegación:
    ir_a_menu(usuario) -> Vuelve al menú principal.
"""

from datetime import date
import flet as ft

from controllers import entradasController
from utils.buscarProducto import buscar_producto_view
from utils.notificaciones import mostrar_notificacion


def entradas_view(pagina: ft.Page, ir_a_main, ir_a_menu, usuario):
    """Formulario sencillo para registrar aumentos de inventario sin precios."""
    # Limpio la pantalla
    pagina.clean()

    # Configuro el tamaño de la ventana para esta vista
    pagina.window.width = 900
    pagina.window.height = 650


    def manejar_teclado(e: ft.KeyboardEvent):
        """
        Manejador de teclado global para esta vista.
        Escape: primero intenta cerrar cualquier diálogo abierto en el overlay;
        si no hay diálogos abiertos, vuelve al menú principal.
        """
        if e.key == "Escape":
            # Verifico si hay diálogos abiertos en el overlay
            if pagina.overlay and len(pagina.overlay) > 0:
                for control in list(pagina.overlay):
                    if hasattr(control, "open") and control.open:
                        # Cierro el diálogo encontrado y salgo
                        control.open = False
                        pagina.update()
                        return
            # Si no había diálogos abiertos, vuelvo al menú
            ir_a_menu(usuario)

    # Registro el manejador de teclado en la página
    pagina.on_keyboard_event = manejar_teclado

    # Lista en memoria de los productos que se van agregando a la entrada
    productos = []

    # Campo de fecha con valor por defecto: fecha de hoy en formato ISO (AAAA-MM-DD)
    campo_fecha = ft.TextField(
        label="Fecha (AAAA-MM-DD)", value=date.today().isoformat(), width=180
    )

    # Campo de observación: multilinea para describir el motivo de la entrada
    campo_observacion = ft.TextField(
        label="Observación o motivo", multiline=True, min_lines=2, width=500
    )

    # Texto para mensajes de éxito/error
    mensaje = ft.Text("", color=ft.Colors.RED)

    # Tabla que muestra los productos agregados a la entrada
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
        """
        Muestra un mensaje en la vista y también como notificación temporal (SnackBar).
        Si texto está vacío, limpia el mensaje.
        """
        mensaje.value = texto
        mensaje.color = ft.Colors.RED if error else ft.Colors.GREEN
        pagina.update()
        if texto:
            mostrar_notificacion(pagina, texto, error=error)

    def redibujar_tabla():
        """
        Reconstruye las filas de la tabla de productos.
        Cada fila tiene: nombre del producto, unidad, campo de cantidad editable
        (con evento on_change para validar) y botón de eliminar.
        """
        tabla.rows.clear()
        for indice, producto in enumerate(productos):
            # Campo de cantidad editable con alineación a la derecha
            campo_cantidad = ft.TextField(
                value=str(producto["cantidad"]), width=100, text_align=ft.TextAlign.RIGHT
            )

            def cambiar_cantidad(event, idx=indice, campo=campo_cantidad):
                """
                Se dispara cuando el usuario modifica la cantidad de un producto.
                Valida el valor a través del controller; si es inválido, revierte
                al valor anterior y muestra error.
                """
                try:
                    entradasController.actualizar_cantidad_producto_entrada(
                        productos[idx], campo.value
                    )
                    mostrar_mensaje("", error=False)
                except ValueError as error:
                    mostrar_mensaje(str(error))
                    # Revierto al valor anterior si la validación falla
                    campo.value = str(productos[idx]["cantidad"])
                    pagina.update()

            # Asigno el handler de cambio al campo de cantidad
            campo_cantidad.on_change = cambiar_cantidad

            # Agrego la fila a la tabla
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
                                # Se usa default argument (idx=indice) para capturar el índice correcto
                                on_click=lambda _, idx=indice: quitar_producto(idx),
                            )
                        ),
                    ]
                )
            )
        pagina.update()

    def agregar_producto(producto):
        """
        Callback que se ejecuta cuando el usuario selecciona un producto
        desde el diálogo de búsqueda. Agrega el producto a la lista
        y redibuja la tabla. No se manejan precios en esta vista.
        """
        # El buscador ya solicita una cantidad. No usamos ni guardamos precios.
        entradasController.agregar_producto_a_entrada(productos, producto)
        redibujar_tabla()

    def abrir_busqueda(_):
        """
        Abre el diálogo de búsqueda de productos como overlay modal.
        Cuando el usuario selecciona un producto, se llama a agregar_producto().
        mostrar_precio=False porque las entradas no manejan precios.
        """
        dialogo = buscar_producto_view(pagina, agregar_producto, mostrar_precio=False)
        # Esta versión de Flet abre diálogos desde overlay, igual que
        # Compras, Ventas y Remisiones del proyecto.
        pagina.overlay.append(dialogo)
        dialogo.open = True
        pagina.update()

    def quitar_producto(indice):
        """Elimina un producto de la lista por su índice y redibuja la tabla."""
        entradasController.quitar_producto_de_entrada(productos, indice)
        redibujar_tabla()

    def guardar_entrada(_):
        """
        Guarda la entrada en la base de datos a través del controller.
        Si es exitoso, limpia la lista de productos y el campo de observación.
        Si falla, muestra un mensaje de error.
        """
        try:
            id_entrada = entradasController.guardar_nueva_entrada(
                campo_fecha.value, campo_observacion.value, productos, usuario
            )
            if not id_entrada:
                mostrar_mensaje("No fue posible guardar la entrada.")
                return

            # Limpio el formulario después de guardar exitosamente
            productos.clear()
            campo_observacion.value = ""
            redibujar_tabla()
            mostrar_mensaje(f"Entrada #{id_entrada} guardada correctamente.", error=False)
        except ValueError as error:
            mostrar_mensaje(str(error))

    # ================== INTERFAZ ==================
    # Estructura: Columna principal con fila de título/botón, campos de entrada,
    # botones de acción, mensaje y tabla de productos en un contenedor con borde
    pagina.add(
        ft.Column(
            [
                # Fila superior: título a la izquierda, botón de volver a la derecha
                ft.Row(
                    [
                        ft.Text("Entradas de inventario", size=22, weight="bold"),
                        ft.Button("Volver al menú", on_click=lambda _: ir_a_menu(usuario)),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                # Texto informativo sobre el funcionamiento de las entradas
                ft.Text("Las entradas suman stock; no modifican precio ni costo."),
                # Fila con campo de fecha y campo de observación
                ft.Row([campo_fecha, campo_observacion], vertical_alignment=ft.CrossAxisAlignment.START),
                # Fila con botones de acción: agregar producto y guardar entrada
                ft.Row([
                    ft.Button("Agregar producto", icon=ft.Icons.ADD, on_click=abrir_busqueda),
                    ft.Button("Guardar entrada", icon=ft.Icons.SAVE, on_click=guardar_entrada),
                ]),
                # Mensaje de estado/error
                mensaje,
                # Contenedor de la tabla de productos con borde y scroll automático
                ft.Container(
                    content=ft.Row([tabla], scroll=ft.ScrollMode.AUTO),
                    expand=True,
                    padding=10,
                    border=ft.Border.all(1, ft.Colors.GREY_300),
                ),
            ],
            expand=True,       # Ocupa todo el espacio disponible
            spacing=14,        # Espacio entre elementos
        )
    )
