# VISTA PARA INVENTARIO
# Muestra el stock calculado desde entradas, compras, ventas y remisiones.
import flet as ft
import asyncio 
from datetime import datetime

from models.inventarioModel import obtener_informe_inventario
from utils.InformeExcel import crear_informe_inventario, mostrar_mensaje


def inventario(pagina: ft.Page, ir_a_main, ir_a_menu, usuario):
    # Lista con los movimientos y stock calculado de cada producto.
    productos = []
    print(f"Usuario en inventario: {usuario}")

    # Limpio la consola y la pantalla
    pagina.clean()

    # Tamaño de la ventana
    pagina.window.width = 1400
    pagina.window.height = 800

    # Centro todo el contenido
    pagina.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    pagina.vertical_alignment = ft.MainAxisAlignment.CENTER

    # ================== ELEMENTOS UI ==================

    logo = ft.Image(
        src="assets/Logo_sena.png",
        width=50,
        height=50
    )

    titulo = ft.Text("Sistema POS", size=15, weight="bold")
    fecha_hora = ft.Text("", size=15)
    texto_usuario = ft.Text(f"Usuario: {usuario['usuario']}", size=15, weight="bold")
    texto_nombre = ft.Text(f"Nombre: {usuario['nombre']}", size=15, weight="bold")
    
    Volver_menu = ft.Button("Volver [Esc]", on_click=lambda _: ir_a_menu(usuario))

    titulo_inventario = ft.Text("Informe de Inventario", size=17, weight="bold")
    
    cantidad_productos = ft.Text("Productos en informe: 0", size=15, weight="bold")

    # ================== FUNCIONES ==================

    # Mantengo la fecha y hora actualizadas en pantalla
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
                # Coloco la fecha y hora actual
                fecha_hora.value = datetime.now().strftime("%d/%m/%Y %I:%M:%S %p")
                fecha_hora.update()
            except RuntimeError:
                # Si la vista ya no existe corto el ciclo
                break
            await asyncio.sleep(1)

    def cargar_productos():
        """Consulta movimientos y pinta el stock final de cada producto."""
        nonlocal productos
        
        try:
            productos = obtener_informe_inventario()
            cantidad_productos.value = f"Productos en informe: {len(productos)}"
            
            # Limpiar las filas existentes
            tabla_productos.rows.clear()
            
            # Agregar cada producto a la tabla
            for producto in productos:
                stock = float(producto.get("stock_final", 0))
                color_stock = ft.Colors.RED if stock < 0 else ft.Colors.GREEN
                
                tabla_productos.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(str(producto.get("codigo", "-")))),
                            ft.DataCell(ft.Text(producto.get("nombre", "Sin nombre"))),
                            ft.DataCell(ft.Text(formatear_cantidad(producto.get("entradas", 0)))),
                            ft.DataCell(ft.Text(formatear_cantidad(producto.get("compras", 0)))),
                            ft.DataCell(ft.Text(formatear_cantidad(producto.get("ventas", 0)))),
                            ft.DataCell(ft.Text(formatear_cantidad(producto.get("remisiones", 0)))),
                            ft.DataCell(
                                ft.Text(
                                    formatear_cantidad(stock),
                                    color=color_stock,
                                    weight="bold"
                                )
                            ),
                            ft.DataCell(ft.Text(str(producto.get("unidad", "UND")))),
                        ]
                    )
                )
            
            pagina.update()
        except Exception as e:
            print(f"Error al cargar productos: {e}")
            cantidad_productos.value = f"Error al cargar productos: {e}"
            pagina.update()

    # Teclado para funciones rápidas
    async def teclado(e: ft.KeyboardEvent):
        # Escape vuelve al menu
        if e.key == "Escape":
            ir_a_menu(usuario)
        # F5 para recargar la lista
        elif e.key == "F5":
            cargar_productos()

    def formatear_cantidad(cantidad):
        """Evita mostrar .0 cuando el movimiento es un número entero."""
        cantidad = float(cantidad or 0)
        return str(int(cantidad)) if cantidad.is_integer() else f"{cantidad:.2f}"

    def exportar_excel(_):
        """Consulta datos recientes y guarda el informe en App como .xlsx."""
        try:
            datos_actuales = obtener_informe_inventario()
            ruta = crear_informe_inventario(datos_actuales)
            mostrar_mensaje(pagina, f"Excel generado en: {ruta}")
        except Exception as error:
            print(f"Error al exportar inventario a Excel: {error}")
            mostrar_mensaje(pagina, f"No se pudo generar el Excel: {error}", ft.Colors.RED)

    # ================== TABLA DE PRODUCTOS ==================

    tabla_productos = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Codigo")),
            ft.DataColumn(ft.Text("Producto")),
            ft.DataColumn(ft.Text("Entradas")),
            ft.DataColumn(ft.Text("Compras")),
            ft.DataColumn(ft.Text("Ventas")),
            ft.DataColumn(ft.Text("Remisiones")),
            ft.DataColumn(ft.Text("Stock")),
            ft.DataColumn(ft.Text("Unidad")),
        ],
        rows=[],
        border=ft.Border.all(1, ft.Colors.BLACK),
        border_radius=10,
        vertical_lines=ft.BorderSide(1, ft.Colors.BLACK_26),
        horizontal_lines=ft.BorderSide(1, ft.Colors.BLACK),
    )

    # Botones
    btn_recargar = ft.Button(
        "Recargar [F5]",
        on_click=lambda _: cargar_productos(),
        width=200,
        height=40,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            text_style=ft.TextStyle(size=15, weight="bold")
        )
    )

    btn_exportar_excel = ft.Button(
        "Exportar Excel",
        icon=ft.Icons.DOWNLOAD,
        on_click=exportar_excel,
        width=200,
        height=40,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            text_style=ft.TextStyle(size=15, weight="bold")
        )
    )

    # ================== PANELES ==================

    # Panel principal con la tabla
    panel_principal = ft.Container(
        expand=True,
        bgcolor=ft.Colors.WHITE,
        border=ft.Border.all(1, ft.Colors.BLACK),
        border_radius=10,
        padding=20,
        content=ft.Column(
            [
                ft.Row(
                    [
                        titulo_inventario,
                        cantidad_productos
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                ft.Row(
                    [btn_recargar, btn_exportar_excel],
                    spacing=5
                ),
                ft.Divider(),
                # TABLA CON SCROLL
                ft.Container(
                    expand=True,
                    border_radius=10,
                    content=ft.Column(
                        expand=True,
                        # Desplazamiento vertical para informes con muchas filas.
                        scroll=ft.ScrollMode.ALWAYS,
                        controls=[
                            ft.Row(
                                # Desplazamiento horizontal para ver todas las columnas.
                                scroll=ft.ScrollMode.ALWAYS,
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

    # ================== LAYOUT PRINCIPAL ==================

    pagina.add(
        ft.Column(
            [
                # Barra superior con logo, titulo, hora y boton volver
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
                # Panel principal
                ft.Row(
                    [
                        panel_principal
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

    # Activo los atajos de teclado
    pagina.on_keyboard_event = teclado

    # Refresco la pantalla
    pagina.update()

    # Cargo los productos con stock bajo o negativo
    cargar_productos()

    # Inicio la tarea que actualiza la hora
    pagina.run_task(actualizar_hora)
