# VISTA PARA CONSULTA DE FACTURAS
# Pantalla para ver, filtrar y consultar documentos del sistema.
import flet as ft
import asyncio
from datetime import datetime

from controllers.facturasController import (
    listar_documentos,
    filtrar_documentos
)
from utils.InformeExcel import crear_informe_tabla
from utils.tablaDocumentos import pintar_documentos


def consultarFacturas(pagina: ft.Page, ir_a_main, ir_a_menu, usuario):
    print(f"Usuario en consulta facturas: {usuario}")

    pagina.clean()
    pagina.window.width = 1400
    pagina.window.height = 800
    pagina.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    pagina.vertical_alignment = ft.MainAxisAlignment.CENTER

    # ================== ELEMENTOS UI ==================

    logo = ft.Image(src="assets/Logo_sena.png", width=50, height=50)
    titulo = ft.Text("Sistema POS", size=15, weight="bold")
    fecha_hora = ft.Text("", size=15)
    texto_usuario = ft.Text(f"Usuario: {usuario['usuario']}", size=15, weight="bold")
    texto_nombre = ft.Text(f"Nombre: {usuario['nombre']}", size=15, weight="bold")

    Volver_menu = ft.Button("Volver [Esc]", on_click=lambda _: ir_a_menu(usuario))

    titulo_consulta = ft.Text("Consulta de Documentos (Facturas)", size=17, weight="bold")
    cantidad_documentos = ft.Text("Documentos encontrados: 0", size=15, weight="bold")

    # ================== CAMPOS DE FILTRO ==================

    campo_numero = ft.TextField(label="Número", width=120)
    campo_tercero = ft.TextField(label="Cliente/Proveedor", width=200)
    campo_usuario_busqueda = ft.TextField(label="Usuario", width=150)

    tipo_documento = ft.Dropdown(
        label="Tipo",
        width=180,
        value="TODOS",
        options=[
            ft.dropdown.Option("TODOS"),
            ft.dropdown.Option("VENTA"),
            ft.dropdown.Option("VENTAS DETALLADAS"),
            ft.dropdown.Option("COMPRA"),
            ft.dropdown.Option("REMISION"),
        ],
    )

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
    campo_producto = ft.TextField(
        label="Producto",
        width=200,
        hint_text="Buscar por nombre de producto"
    )

    # ================== COLUMNAS DE LA TABLA ==================

    COLUMNAS_NORMAL = [
        ft.DataColumn(ft.Text("Tipo")),
        ft.DataColumn(ft.Text("Número")),
        ft.DataColumn(ft.Text("Fecha")),
        ft.DataColumn(ft.Text("Cliente/Proveedor")),
        ft.DataColumn(ft.Text("Usuario")),
        ft.DataColumn(ft.Text("Total")),
        ft.DataColumn(ft.Text("Productos")),
    ]

    COLUMNAS_DETALLADO = [
        ft.DataColumn(ft.Text("N° Venta")),
        ft.DataColumn(ft.Text("Fecha")),
        ft.DataColumn(ft.Text("Cliente")),
        ft.DataColumn(ft.Text("Usuario")),
        ft.DataColumn(ft.Text("Producto")),
        ft.DataColumn(ft.Text("Cantidad")),
        ft.DataColumn(ft.Text("V. Unitario")),
        ft.DataColumn(ft.Text("Subtotal")),
    ]

    tabla_documentos = ft.DataTable(
        columns=COLUMNAS_NORMAL,
        rows=[],
        border_radius=10,
    )

    # ================== FUNCIONES ==================

    def _es_modo_detallado():
        return tipo_documento.value == "VENTAS DETALLADAS"

    def _pintar_detallado(documentos):

        documentos = documentos or []

        tabla_documentos.columns = COLUMNAS_DETALLADO
        tabla_documentos.rows.clear()

        for d in documentos:
            fecha = d.get("fecha")
            fecha_txt = (
                fecha.strftime("%d/%m/%Y %I:%M %p")
                if hasattr(fecha, "strftime") else str(fecha)
            )

            cantidad = d.get("cantidad", 0)
            cantidad_txt = (
                str(int(cantidad))
                if isinstance(cantidad, (int, float)) and cantidad == int(cantidad)
                else str(cantidad)
            )

            tabla_documentos.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(str(d["numero"]))),
                    ft.DataCell(ft.Text(fecha_txt)),
                    ft.DataCell(ft.Text(str(d.get("tercero", "-")))),
                    ft.DataCell(ft.Text(str(d.get("usuario", "-")))),
                    ft.DataCell(ft.Text(str(d.get("producto", "-")))),
                    ft.DataCell(ft.Text(cantidad_txt)),
                    ft.DataCell(ft.Text(f"${d.get('precio_unitario', 0):,.2f}")),
                    ft.DataCell(ft.Text(f"${d.get('subtotal', 0):,.2f}")),
                ])
            )

        cantidad_documentos.value = f"Líneas encontradas: {len(documentos)}"

    def _pintar_normal(documentos):

        documentos = documentos or []

        tabla_documentos.columns = COLUMNAS_NORMAL
        pintar_documentos(tabla_documentos, cantidad_documentos, documentos)

    def abrir_calendario(campo_fecha: ft.TextField, titulo_calendario: str):
        def seleccionar_fecha(e):
            if e.control.value:
                campo_fecha.value = e.control.value.strftime("%d/%m/%Y")
                campo_fecha.update()

        fecha_inicial = datetime.now()
        if campo_fecha.value:
            try:
                fecha_inicial = datetime.strptime(campo_fecha.value, "%d/%m/%Y")
            except ValueError:
                pass

        pagina.show_dialog(
            ft.DatePicker(
                help_text=titulo_calendario,
                field_label_text="Fecha",
                field_hint_text="DD/MM/YYYY",
                cancel_text="Cancelar",
                confirm_text="Aceptar",
                first_date=datetime(2000, 1, 1),
                last_date=datetime(2100, 12, 31),
                current_date=datetime.now(),
                value=fecha_inicial,
                on_change=seleccionar_fecha
            )
        )

    selector_fecha_inicio = ft.Row(
        [
            campo_fecha_inicio,
            ft.IconButton(
                icon=ft.Icons.CALENDAR_MONTH,
                tooltip="Seleccionar fecha inicio",
                on_click=lambda _: abrir_calendario(
                    campo_fecha_inicio, "Seleccionar fecha inicio"
                )
            )
        ],
        spacing=0,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        tight=True
    )

    selector_fecha_fin = ft.Row(
        [
            campo_fecha_fin,
            ft.IconButton(
                icon=ft.Icons.CALENDAR_MONTH,
                tooltip="Seleccionar fecha fin",
                on_click=lambda _: abrir_calendario(
                    campo_fecha_fin, "Seleccionar fecha fin"
                )
            )
        ],
        spacing=0,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        tight=True
    )

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
        try:
            if _es_modo_detallado():
                documentos = filtrar_documentos(tipo="VENTAS DETALLADAS")
                _pintar_detallado(documentos)
            else:
                documentos = listar_documentos()
                print(f"[DEBUG] normal → {type(documentos)} con "
                    f"{len(documentos) if documentos else 0} elementos")
                _pintar_normal(documentos)
            pagina.update()
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error al cargar documentos: {e}")
            cantidad_documentos.value = f"Error al cargar documentos: {e}"
            pagina.update()

    def buscar_documentos():
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

            if _es_modo_detallado():
                _pintar_detallado(documentos)
            else:
                _pintar_normal(documentos)

            pagina.update()
        except Exception as e:
            print(f"Error al buscar documentos: {e}")
            cantidad_documentos.value = f"Error: {e}"
            pagina.update()

    def limpiar_filtros():
        campo_numero.value = ""
        campo_tercero.value = ""
        campo_usuario_busqueda.value = ""
        campo_fecha_inicio.value = ""
        campo_fecha_fin.value = ""
        campo_producto.value = ""
        tipo_documento.value = "TODOS"
        cargar_documentos()

    try:
        tipo_documento.on_change = lambda _: cargar_documentos()
    except Exception as err:
        print(f"No se pudo asignar on_change al dropdown: {err}")

    async def teclado(e: ft.KeyboardEvent):
        if e.key == "Escape":
            ir_a_menu(usuario)
        elif e.key == "F2":
            crear_informe_tabla(pagina, tabla_documentos)
        elif e.key == "F5":
            cargar_documentos()

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

    btn_crear_informe = ft.Button(
        "Crear Informe [F2]",
        on_click=lambda _: crear_informe_tabla(pagina, tabla_documentos),
        width=180,
        height=40,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            text_style=ft.TextStyle(size=14, weight="bold")
        )
    )

    # ================== PANEL PRINCIPAL ==================

    panel_principal = ft.Container(
        expand=True,
        bgcolor=ft.Colors.WHITE,
        border_radius=10,
        padding=20,
        content=ft.Column(
            [
                ft.Row(
                    [titulo_consulta, cantidad_documentos],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                ft.Divider(),
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
                        ft.Row(
                            [selector_fecha_inicio, selector_fecha_fin],
                            spacing=10,
                            tight=True,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER
                        ),
                        campo_producto,
                        btn_buscar,
                        btn_limpiar,
                    ],
                    wrap=True,
                    spacing=10
                ),
                ft.Row(
                    [btn_recargar, btn_crear_informe],
                    spacing=5
                ),
                ft.Divider(),
                ft.Container(
                    expand=True,
                    border_radius=10,
                    content=ft.Column(
                        expand=True,
                        scroll=ft.ScrollMode.AUTO,
                        controls=[
                            ft.Row(
                                scroll=ft.ScrollMode.AUTO,
                                controls=[tabla_documentos]
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
                ft.Row(
                    [panel_principal],
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

    pagina.on_keyboard_event = teclado
    pagina.update()
    cargar_documentos()
    pagina.run_task(actualizar_hora)