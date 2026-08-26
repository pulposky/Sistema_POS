"""
Vista de informe de inventario del sistema POS.

Muestra una tabla con el stock calculado de cada producto sumando entradas,
compras, ventas y remisiones. Permite recargar los datos, exportar a Excel
y navegar con el teclado.

Esta vista tiene un diseño de pantalla completa con barra superior (header)
que muestra información del sistema, usuario y hora actualizándose en tiempo real.

Atajos de teclado:
    Escape -> Vuelve al menú principal.
    F5     -> Recarga la lista de productos.

Navegación:
    ir_a_menu(usuario) -> Vuelve al menú principal.
"""

# VISTA PARA INVENTARIO
# Muestra el stock calculado desde entradas, compras, ventas y remisiones.
import flet as ft
import asyncio 
from datetime import datetime

from models.inventarioModel import obtener_informe_inventario
from utils.InformeExcel import crear_informe_inventario, mostrar_mensaje


def inventario(pagina: ft.Page, ir_a_main, ir_a_menu, usuario):
    """
    Renderiza el informe de inventario con tabla de productos y barra superior.

    Parámetros:
        pagina     -> Instancia de la página Flet.
        ir_a_main  -> Callback para ir a la pantalla de bienvenida (no usado directamente).
        ir_a_menu  -> Callback para volver al menú principal.
        usuario    -> Diccionario con datos del usuario logueado (usuario, nombre, rol, etc.).
    """
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

    # Logo del SENA en la barra superior
    logo = ft.Image(
        src="Logo_sena.png",
        width=50,
        height=50
    )

    # Texto del título del sistema en la barra superior
    titulo = ft.Text("Sistema POS", size=15, weight="bold")

    # Texto que muestra la fecha y hora actual, se actualiza cada segundo
    fecha_hora = ft.Text("", size=15)

    # Texto con el nombre de usuario logueado
    texto_usuario = ft.Text(f"Usuario: {usuario['usuario']}", size=15, weight="bold")

    # Texto con el nombre completo del usuario logueado
    texto_nombre = ft.Text(f"Nombre: {usuario['nombre']}", size=15, weight="bold")
    
    # Botón para volver al menú principal (también accesible con Escape)
    Volver_menu = ft.Button("Volver [Esc]", on_click=lambda _: ir_a_menu(usuario))

    # Título de la sección de inventario
    titulo_inventario = ft.Text("Informe de Inventario", size=17, weight="bold")
    
    # Contador de productos mostrados en el informe
    cantidad_productos = ft.Text("Productos en informe: 0", size=15, weight="bold")

    # ================== FUNCIONES ==================

    # Mantengo la fecha y hora actualizadas en pantalla
    async def actualizar_hora():
        """
        Tarea asíncrona que actualiza el texto de fecha/hora cada segundo.
        Se ejecuta como task de Flet y se detiene automáticamente cuando
        la vista ya no existe (captura RuntimeError).
        """
        # Ciclo infinito mientras la vista siga activa
        while True:
            try:
                # Espero a que el control esté disponible en la página
                if fecha_hora.page is None:
                    await asyncio.sleep(0.1)
                    continue
            except RuntimeError:
                await asyncio.sleep(0.1)
                continue
            try:
                # Coloco la fecha y hora actual en formato legible
                fecha_hora.value = datetime.now().strftime("%d/%m/%Y %I:%M:%S %p")
                fecha_hora.update()
            except RuntimeError:
                # Si la vista ya no existe corto el ciclo
                break
            # Espero 1 segundo antes de actualizar de nuevo
            await asyncio.sleep(1)

    def cargar_productos():
        """Consulta movimientos y pinta el stock final de cada producto."""
        nonlocal productos
        
        try:
            # Obtengo los datos del informe de inventario desde el modelo
            productos = obtener_informe_inventario()

            # Actualizo el contador de productos
            cantidad_productos.value = f"Productos en informe: {len(productos)}"
            
            # Limpiar las filas existentes en la tabla
            tabla_productos.rows.clear()
            
            # Agregar cada producto como fila en la tabla
            for producto in productos:
                # Calculo el stock final y asigno color: rojo si es negativo, verde si es positivo
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
                                    color=color_stock,    # Rojo si stock negativo, verde si positivo
                                    weight="bold"
                                )
                            ),
                            ft.DataCell(ft.Text(str(producto.get("unidad", "UND")))),
                        ]
                    )
                )
            
            # Refresco la pantalla para mostrar los datos actualizados
            pagina.update()
        except Exception as e:
            print(f"Error al cargar productos: {e}")
            cantidad_productos.value = f"Error al cargar productos: {e}"
            pagina.update()

    # Teclado para funciones rápidas
    async def teclado(e: ft.KeyboardEvent):
        """
        Manejador de atajos de teclado:
          Escape -> Vuelve al menú principal.
          F5     -> Recarga los datos del inventario.
        """
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
            # Obtengo los datos actuales del inventario
            datos_actuales = obtener_informe_inventario()
            # Genero el archivo Excel con la utilidad del proyecto
            ruta = crear_informe_inventario(datos_actuales)
            mostrar_mensaje(pagina, f"Excel generado en: {ruta}")
        except Exception as error:
            print(f"Error al exportar inventario a Excel: {error}")
            mostrar_mensaje(pagina, f"No se pudo generar el Excel: {error}", ft.Colors.RED)

    # ================== TABLA DE PRODUCTOS ==================

    # Tabla principal con 8 columnas: Codigo, Producto, Entradas, Compras,
    # Ventas, Remisiones, Stock y Unidad
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

    # Botón de recarga: llama a cargar_productos() al hacer clic
    # También accesible con F5
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

    # Botón de exportar a Excel: genera un archivo .xlsx con los datos actuales
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
    # Contiene: título del informe, contador de productos, botones de acción,
    # separador y la tabla de productos con scroll vertical y horizontal
    panel_principal = ft.Container(
        expand=True,                              # Ocupa todo el espacio disponible
        bgcolor=ft.Colors.WHITE,
        border=ft.Border.all(1, ft.Colors.BLACK),
        border_radius=10,
        padding=20,
        content=ft.Column(
            [
                # Fila superior: título del informe a la izquierda, contador a la derecha
                ft.Row(
                    [
                        titulo_inventario,
                        cantidad_productos
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                # Fila de botones: Recargar y Exportar Excel
                ft.Row(
                    [btn_recargar, btn_exportar_excel],
                    spacing=5
                ),
                # Separador visual
                ft.Divider(),
                # TABLA CON SCROLL
                # Contenedor con scroll vertical (ALWAYS) que envuelve un Row
                # con scroll horizontal para ver todas las columnas
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

    # Estructura de pantalla completa:
    #   1. Barra superior (header) con logo, título, usuario, hora y botón volver
    #   2. Panel principal con la tabla de inventario
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
                            # Lado izquierdo: información del sistema y usuario
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
                            # Lado derecho: logo del SENA
                            logo
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        expand=True
                    )
                ),
                # Panel principal con la tabla de inventario
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
            spacing=0             # Sin espacio entre header y panel principal
        )
    )

    # Activo los atajos de teclado (Escape y F5)
    pagina.on_keyboard_event = teclado

    # Refresco la pantalla
    pagina.update()

    # Cargo los productos con stock bajo o negativo
    cargar_productos()

    # Inicio la tarea que actualiza la hora cada segundo
    pagina.run_task(actualizar_hora)
