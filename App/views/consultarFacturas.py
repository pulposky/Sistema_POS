# VISTA PARA CONSULTA DE FACTURAS

import flet as ft
import asyncio 
from datetime import datetime

from controllers.facturasController import (
    listar_documentos,
    filtrar_documentos
)


def consultarFacturas(pagina: ft.Page, ir_a_main, ir_a_menu, usuario):
    print(f"Usuario en consulta facturas: {usuario}")

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

    titulo_consulta = ft.Text("Consulta de Documentos (Facturas)", size=17, weight="bold")
    
    # Etiqueta que muestra la cantidad de documentos
    cantidad_documentos = ft.Text("Documentos encontrados: 0", size=15, weight="bold")
    
    # CAMPOS DE FILTRO
    campo_numero = ft.TextField(
        label="Número",
        width=120
    )

    campo_tercero = ft.TextField(
        label="Cliente/Proveedor",
        width=200
    )

    campo_usuario_busqueda = ft.TextField(
        label="Usuario",
        width=150
    )

    tipo_documento = ft.Dropdown(
        label="Tipo",
        width=130,
        value="TODOS",
        options=[
            ft.dropdown.Option("TODOS"),
            ft.dropdown.Option("VENTA"),
            ft.dropdown.Option("COMPRA"),
            ft.dropdown.Option("REMISION")
        ]
    )

    # NUEVOS CAMPOS: FECHA INICIO Y FIN
    campo_fecha_inicio = ft.TextField(
        label="Fecha Inicio (DD/MM/YYYY)",
        width=180,
        hint_text="01/01/2024"
    )

    campo_fecha_fin = ft.TextField(
        label="Fecha Fin (DD/MM/YYYY)",
        width=180,
        hint_text="31/12/2024"
    )

    # NUEVO CAMPO: PRODUCTO
    campo_producto = ft.TextField(
        label="Producto",
        width=200,
        hint_text="Buscar por nombre de producto"
    )

    # ================== FUNCIONES ==================

    # Mantengo la fecha y hora actualizadas en pantalla
    async def actualizar_hora():
        while True:
            try:
                if fecha_hora.page is None:
                    await asyncio.sleep(0.1)
                    continue
            except RuntimeError:
                await asyncio.sleep(0.1)
                continue
            try:
                fecha_hora.value = datetime.now().strftime("%d/%m/%Y %I:%M:%S %p")
                fecha_hora.update()
            except RuntimeError:
                break
            await asyncio.sleep(1)

    def cargar_documentos():
        """Carga todos los documentos desde la base de datos"""
        try:
            documentos = listar_documentos()
            
            tabla_documentos.rows.clear()
            
            cantidad_documentos.value = f"Documentos encontrados: {len(documentos)}"
            
            for doc in documentos:
                tabla_documentos.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(doc["tipo"])),
                            ft.DataCell(ft.Text(str(doc["numero"]))),
                            ft.DataCell(
                                ft.Text(
                                    doc["fecha"].strftime("%d/%m/%Y %H:%M")
                                )
                            ),
                            ft.DataCell(ft.Text(str(doc["tercero"] or "-"))),
                            ft.DataCell(ft.Text(str(doc["usuario"] or "-"))),
                            ft.DataCell(ft.Text(f"${float(doc['total']):,.0f}")),
                            ft.DataCell(ft.Text(str(doc.get("productos", "-"))))
                        ]
                    )
                )
            
            pagina.update()
        except Exception as e:
            print(f"Error al cargar documentos: {e}")
            cantidad_documentos.value = f"Error al cargar documentos: {e}"
            pagina.update()

    def buscar_documentos():
        """Busca documentos según los filtros aplicados"""
        try:
            documentos = filtrar_documentos(
                numero=campo_numero.value,
                tercero=campo_tercero.value,
                usuario=campo_usuario_busqueda.value,
                tipo=tipo_documento.value,
                fecha_inicio=campo_fecha_inicio.value,
                fecha_fin=campo_fecha_fin.value,
                producto=campo_producto.value
            )

            tabla_documentos.rows.clear()

            cantidad_documentos.value = f"Documentos encontrados: {len(documentos)}"

            for doc in documentos:
                tabla_documentos.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(doc["tipo"])),
                            ft.DataCell(ft.Text(str(doc["numero"]))),
                            ft.DataCell(
                                ft.Text(
                                    doc["fecha"].strftime("%d/%m/%Y %H:%M")
                                )
                            ),
                            ft.DataCell(ft.Text(str(doc["tercero"] or "-"))),
                            ft.DataCell(ft.Text(str(doc["usuario"] or "-"))),
                            ft.DataCell(ft.Text(f"${float(doc['total']):,.0f}")),
                            ft.DataCell(ft.Text(str(doc.get("productos", "-"))))
                        ]
                    )
                )

            pagina.update()
        except Exception as e:
            print(f"Error al buscar documentos: {e}")
            cantidad_documentos.value = f"Error: {e}"
            pagina.update()

    def limpiar_filtros():
        """Limpia todos los campos de filtro"""
        campo_numero.value = ""
        campo_tercero.value = ""
        campo_usuario_busqueda.value = ""
        campo_fecha_inicio.value = ""
        campo_fecha_fin.value = ""
        campo_producto.value = ""
        tipo_documento.value = "TODOS"
        cargar_documentos()

    # Teclado para funciones rápidas
    async def teclado(e: ft.KeyboardEvent):
        if e.key == "Escape":
            ir_a_menu(usuario)
        elif e.key == "F5":
            cargar_documentos()

    # ================== TABLA DE DOCUMENTOS ==================

    tabla_documentos = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Tipo")),
            ft.DataColumn(ft.Text("Número")),
            ft.DataColumn(ft.Text("Fecha")),
            ft.DataColumn(ft.Text("Cliente/Proveedor")),
            ft.DataColumn(ft.Text("Usuario")),
            ft.DataColumn(ft.Text("Total")),
            ft.DataColumn(ft.Text("Productos")),  # NUEVA COLUMNA
        ],
        rows=[],
        border_radius=10,
    )

    # ================== BOTONES ==================

    btn_buscar = ft.Button(
        "Buscar",
        on_click=lambda _: buscar_documentos(),
        width=120,
        height=40,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            text_style=ft.TextStyle(size=14, weight="bold")
        )
    )

    btn_limpiar = ft.Button(
        "Limpiar",
        on_click=lambda _: limpiar_filtros(),
        width=120,
        height=40,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            text_style=ft.TextStyle(size=14, weight="bold")
        )
    )

    btn_recargar = ft.Button(
        "Recargar [F5]",
        on_click=lambda _: cargar_documentos(),
        width=150,
        height=40,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            text_style=ft.TextStyle(size=14, weight="bold")
        )
    )

    # ================== PANELES ==================

    # Panel principal con la tabla
    panel_principal = ft.Container(
        expand=True,
        bgcolor=ft.Colors.WHITE,
        border_radius=10,
        padding=20,
        content=ft.Column(
            [
                ft.Row(
                    [
                        titulo_consulta,
                        cantidad_documentos
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                ft.Divider(),
                # FILTROS EN DOS FILAS
                ft.Row(
                    [
                        campo_numero,
                        campo_tercero,
                        campo_usuario_busqueda,
                        tipo_documento,
                    ],
                    wrap=True,
                    spacing=10
                ),
                ft.Row(
                    [
                        campo_fecha_inicio,
                        campo_fecha_fin,
                        campo_producto,
                        btn_buscar,
                        btn_limpiar,
                    ],
                    wrap=True,
                    spacing=10
                ),
                ft.Row(
                    [btn_recargar],
                    spacing=5
                ),
                ft.Divider(),
                # TABLA CON SCROLL
                ft.Container(
                    expand=True,
                    border_radius=10,
                    content=ft.Column(
                        expand=True,
                        scroll=ft.ScrollMode.AUTO,
                        controls=[
                            ft.Row(
                                scroll=ft.ScrollMode.AUTO,
                                controls=[
                                    tabla_documentos
                                ]
                            )
                        ]
                    )
                )
            ],
            expand=True,
            spacing=15
        )
    )

    # ================== LAYOUT PRINCIPAL ==================

    pagina.add(
        ft.Column(
            [
                # Barra superior
                ft.Container(
                    bgcolor=ft.Colors.WHITE,
                    padding=ft.Padding(10, 10, 20, 10),
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

    # Cargo los documentos al iniciar
    cargar_documentos()

    # Inicio la tarea que actualiza la hora
    pagina.run_task(actualizar_hora)