"""
Vista de consulta de facturas y documentos del sistema POS.

Permite filtrar y consultar documentos por tipo (VENTA, COMPRA, REMISIÓN, TODOS),
número, cliente/proveedor, usuario, rango de fechas y producto. Tiene dos modos
de visualización:
  - Normal: muestra una fila por documento con su total.
  - Detallado (VENTAS DETALLADAS): muestra una fila por línea de producto.

También permite generar informes Excel con los datos filtrados.

Esta vista tiene un diseño de pantalla completa con barra superior (header)
que muestra información del sistema, usuario y hora actualizándose en tiempo real.

Atajos de teclado:
    Escape -> Vuelve al menú principal.
    F2     -> Genera un informe Excel con los datos actuales de la tabla.
    F5     -> Recarga la lista de documentos.

Navegación:
    ir_a_menu(usuario) -> Vuelve al menú principal.
"""

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
    """
    Renderiza la vista de consulta de facturas con filtros avanzados.

    Parámetros:
        pagina     -> Instancia de la página Flet.
        ir_a_main  -> Callback para ir a la pantalla de bienvenida (no usado directamente).
        ir_a_menu  -> Callback para volver al menú principal.
        usuario    -> Diccionario con datos del usuario logueado.
    """
    print(f"Usuario en consulta facturas: {usuario}")

    # Limpio la pantalla
    pagina.clean()

    # Configuro el tamaño de la ventana
    pagina.window.width = 1400
    pagina.window.height = 800

    # Centro todo el contenido
    pagina.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    pagina.vertical_alignment = ft.MainAxisAlignment.CENTER

    # ================== ELEMENTOS UI ==================

    # Logo del SENA en la barra superior
    logo = ft.Image(src="Logo_sena.png", width=50, height=50)

    # Texto del título del sistema
    titulo = ft.Text("Sistema POS", size=15, weight="bold")

    # Texto que muestra la fecha y hora actual, se actualiza cada segundo
    fecha_hora = ft.Text("", size=15)

    # Texto con el nombre de usuario logueado
    texto_usuario = ft.Text(f"Usuario: {usuario['usuario']}", size=15, weight="bold")

    # Texto con el nombre completo del usuario logueado
    texto_nombre = ft.Text(f"Nombre: {usuario['nombre']}", size=15, weight="bold")

    # Botón para volver al menú principal
    Volver_menu = ft.Button("Volver [Esc]", on_click=lambda _: ir_a_menu(usuario))

    # Título de la sección de consulta
    titulo_consulta = ft.Text("Consulta de Documentos (Facturas)", size=17, weight="bold")

    # Contador de documentos/ítems encontrados
    cantidad_documentos = ft.Text("Documentos encontrados: 0", size=15, weight="bold")

    # ================== CAMPOS DE FILTRO ==================

    # Campo de filtro por número de documento
    campo_numero = ft.TextField(label="Número", width=120)

    # Campo de filtro por nombre de cliente o proveedor
    campo_tercero = ft.TextField(label="Cliente/Proveedor", width=200)

    # Campo de filtro por usuario que creó el documento
    campo_usuario_busqueda = ft.TextField(label="Usuario", width=150)

    # Dropdown para filtrar por tipo de documento
    tipo_documento = ft.Dropdown(
        label="Tipo",
        width=180,
        value="TODOS",           # Valor por defecto: muestra todos los tipos
        options=[
            ft.dropdown.Option("TODOS"),               # Sin filtro de tipo
            ft.dropdown.Option("VENTA"),               # Solo ventas
            ft.dropdown.Option("VENTAS DETALLADAS"),   # Modo detallado: una fila por línea
            ft.dropdown.Option("COMPRA"),              # Solo compras
            ft.dropdown.Option("REMISION"),            # Solo remisiones
        ],
    )

    # Campo de fecha de inicio del rango (formato DD/MM/YYYY)
    campo_fecha_inicio = ft.TextField(
        label="Fecha Inicio (DD/MM/YYYY)",
        width=180,
        hint_text="01/01/2024"
    )

    # Campo de fecha de fin del rango (formato DD/MM/YYYY)
    campo_fecha_fin = ft.TextField(
        label="Fecha Fin (DD/MM/YYYY)",
        width=180,
        hint_text="31/12/2024"
    )

    # Campo de filtro por nombre de producto
    campo_producto = ft.TextField(
        label="Producto",
        width=200,
        hint_text="Buscar por nombre de producto"
    )

    # ================== COLUMNAS DE LA TABLA ==================

    # Columnas para el modo normal (una fila por documento)
    COLUMNAS_NORMAL = [
        ft.DataColumn(ft.Text("Tipo")),
        ft.DataColumn(ft.Text("Número")),
        ft.DataColumn(ft.Text("Fecha")),
        ft.DataColumn(ft.Text("Cliente/Proveedor")),
        ft.DataColumn(ft.Text("Usuario")),
        ft.DataColumn(ft.Text("Total")),
        ft.DataColumn(ft.Text("Productos")),
        ft.DataColumn(ft.Text("Notas")),
    ]

    # Columnas para el modo detallado (una fila por línea de producto)
    COLUMNAS_DETALLADO = [
        ft.DataColumn(ft.Text("N° Venta")),
        ft.DataColumn(ft.Text("Fecha")),
        ft.DataColumn(ft.Text("Cliente")),
        ft.DataColumn(ft.Text("Usuario")),
        ft.DataColumn(ft.Text("Producto")),
        ft.DataColumn(ft.Text("Cantidad")),
        ft.DataColumn(ft.Text("V. Unitario")),
        ft.DataColumn(ft.Text("Subtotal")),
        ft.DataColumn(ft.Text("Notas")),
    ]

    # Tabla principal de documentos
    tabla_documentos = ft.DataTable(
        columns=COLUMNAS_NORMAL,     # Inicia en modo normal
        rows=[],
        border_radius=10,
    )

    # ================== FUNCIONES ==================

    def _es_modo_detallado():
        """Verifica si el tipo seleccionado es 'VENTAS DETALLADAS'."""
        return tipo_documento.value == "VENTAS DETALLADAS"

    def _pintar_detallado(documentos):
        """
        Pinta la tabla en modo detallado: una fila por línea de producto.
        Cambia las columnas de la tabla y construye las filas manualmente.
        """
        documentos = documentos or []

        # Cambio las columnas a las del modo detallado
        tabla_documentos.columns = COLUMNAS_DETALLADO
        tabla_documentos.rows.clear()

        for d in documentos:
            # Formateo la fecha para mostrarla en formato legible
            fecha = d.get("fecha")
            fecha_txt = (
                fecha.strftime("%d/%m/%Y %I:%M %p")
                if hasattr(fecha, "strftime") else str(fecha)
            )

            # Formateo la cantidad: si es entero sin decimales
            cantidad = d.get("cantidad", 0)
            cantidad_txt = (
                str(int(cantidad))
                if isinstance(cantidad, (int, float)) and cantidad == int(cantidad)
                else str(cantidad)
            )

            # Agrego la fila con los datos del producto
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
                    ft.DataCell(ft.Text(str(d.get("notas", "-")))),
                ])
            )

        # Actualizo el contador con el número de líneas encontradas
        cantidad_documentos.value = f"Líneas encontradas: {len(documentos)}"

    def _pintar_normal(documentos):
        """
        Pinta la tabla en modo normal: una fila por documento.
        Usa la utilidad pintar_documentos() del proyecto.
        """
        documentos = documentos or []

        # Cambio las columnas a las del modo normal
        tabla_documentos.columns = COLUMNAS_NORMAL

        # Pinto los documentos usando la función auxiliar
        pintar_documentos(tabla_documentos, cantidad_documentos, documentos)

    def abrir_calendario(campo_fecha: ft.TextField, titulo_calendario: str):
        """
        Abre un diálogo de selección de fecha (DatePicker) para el campo indicado.
        Al seleccionar una fecha, actualiza el campo de texto con formato DD/MM/YYYY.
        """
        def seleccionar_fecha(e):
            """Callback que se ejecuta cuando el usuario selecciona una fecha."""
            if e.control.value:
                campo_fecha.value = e.control.value.strftime("%d/%m/%Y")
                campo_fecha.update()

        # Intento parsear la fecha actual del campo como fecha inicial del calendario
        fecha_inicial = datetime.now()
        if campo_fecha.value:
            try:
                fecha_inicial = datetime.strptime(campo_fecha.value, "%d/%m/%Y")
            except ValueError:
                pass

        # Muestro el diálogo de selección de fecha
        pagina.show_dialog(
            ft.DatePicker(
                help_text=titulo_calendario,
                field_label_text="Fecha",
                field_hint_text="DD/MM/YYYY",
                cancel_text="Cancelar",
                confirm_text="Aceptar",
                first_date=datetime(2000, 1, 1),     # Fecha mínima
                last_date=datetime(2100, 12, 31),     # Fecha máxima
                current_date=datetime.now(),
                value=fecha_inicial,
                on_change=seleccionar_fecha
            )
        )

    # Campo de fecha de inicio con ícono de calendario
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
        tight=True       # Sin espacio extra entre el campo y el ícono
    )

    # Campo de fecha de fin con ícono de calendario
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
        """
        Tarea asíncrona que actualiza el texto de fecha/hora cada segundo.
        Se detiene automáticamente cuando la vista ya no existe.
        """
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
        """
        Carga los documentos según el modo seleccionado:
          - Modo detallado: trae todas las ventas con sus líneas de producto.
          - Modo normal: trae todos los documentos resumidos.
        Se ejecuta al iniciar la vista, al recargar (F5) y al cambiar el tipo.
        """
        try:
            if _es_modo_detallado():
                # Modo detallado: una fila por línea de producto
                documentos = filtrar_documentos(tipo="VENTAS DETALLADAS")
                _pintar_detallado(documentos)
            else:
                # Modo normal: una fila por documento
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
        """
        Filtra los documentos según los valores de los campos de filtro.
        Pasa todos los campos al controller de filtrado y pinta los resultados
        en el modo correspondiente (normal o detallado).
        """
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

            # Pinto según el modo actual
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
        """
        Limpia todos los campos de filtro y recarga los documentos.
        Restablece el tipo a "TODOS".
        """
        campo_numero.value = ""
        campo_tercero.value = ""
        campo_usuario_busqueda.value = ""
        campo_fecha_inicio.value = ""
        campo_fecha_fin.value = ""
        campo_producto.value = ""
        tipo_documento.value = "TODOS"
        # Recargo los documentos sin filtros
        cargar_documentos()

    # Cuando cambia el tipo de documento en el dropdown, recargo automáticamente
    # para cambiar entre modo normal y detallado
    try:
        tipo_documento.on_change = lambda _: cargar_documentos()
    except Exception as err:
        print(f"No se pudo asignar on_change al dropdown: {err}")

    async def teclado(e: ft.KeyboardEvent):
        """
        Manejador de atajos de teclado:
          Escape -> Vuelve al menú principal.
          F2     -> Genera informe Excel con los datos de la tabla.
          F5     -> Recarga los documentos.
        """
        if e.key == "Escape":
            ir_a_menu(usuario)
        elif e.key == "F2":
            # Genero un informe Excel con los datos actuales de la tabla
            crear_informe_tabla(pagina, tabla_documentos)
        elif e.key == "F5":
            # Recargo los documentos desde la base de datos
            cargar_documentos()

    # ================== BOTONES ==================

    # Botón de búsqueda: filtra los documentos según los campos de filtro
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

    # Botón de limpiar: restablece todos los filtros y recarga
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

    # Botón de recarga: recarga los documentos desde la base de datos
    # También accesible con F5
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

    # Botón de crear informe Excel: genera un archivo .xlsx con los datos actuales
    # También accesible con F2
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

    # Panel que contiene: título, filtros, botones de acción y la tabla de resultados
    panel_principal = ft.Container(
        expand=True,                              # Ocupa todo el espacio disponible
        bgcolor=ft.Colors.WHITE,
        border_radius=10,
        padding=20,
        content=ft.Column(
            [
                # Fila superior: título del informe a la izquierda, contador a la derecha
                ft.Row(
                    [titulo_consulta, cantidad_documentos],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                ft.Divider(),
                # Primera fila de filtros: número, tercero, usuario y tipo
                ft.Row(
                    [
                        campo_numero,
                        campo_tercero,
                        campo_usuario_busqueda,
                        tipo_documento,
                    ],
                    wrap=True,         # Permite saltos de línea si no cabe
                    spacing=10
                ),
                # Segunda fila de filtros: fechas con calendario, producto y botones
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
                # Botones de recarga e informe Excel
                ft.Row(
                    [btn_recargar, btn_crear_informe],
                    spacing=5
                ),
                ft.Divider(),
                # Tabla de resultados con scroll horizontal y vertical
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

    # Estructura de pantalla completa:
    #   1. Barra superior (header) con logo, título, usuario, hora y botón volver
    #   2. Panel principal con filtros y tabla de resultados
    pagina.add(
        ft.Column(
            [
                # Barra superior con información del sistema
                ft.Container(
                    bgcolor=ft.Colors.WHITE,
                    padding=ft.Padding(10, 10, 20, 10),
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
                # Panel principal con filtros y tabla
                ft.Row(
                    [panel_principal],
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

    # Activo los atajos de teclado (Escape, F2, F5)
    pagina.on_keyboard_event = teclado

    # Refresco la pantalla
    pagina.update()

    # Cargo los documentos iniciales (sin filtros)
    cargar_documentos()

    # Inicio la tarea que actualiza la hora cada segundo
    pagina.run_task(actualizar_hora)
