"""
Vista del Panel de Administración del sistema POS.

Es el módulo exclusivo del administrador para administrar la aplicación.
Se abre desde la pantalla de bienvenida mediante el botón "Administración",
que solicita la contraseña de un administrador antes de mostrar el panel.

El panel tiene 4 secciones:
  - 📊 Indicadores: ventas/compras del día, productos, stock bajo,
    clientes, proveedores, usuarios y últimas ventas.
  - 👥 Usuarios: crear, editar (nombre/login/rol), cambiar contraseña y
    eliminar usuarios del sistema.
  - 📦 Productos: catálogo completo con búsqueda, alta, edición y baja.
  - 💾 Respaldo: genera un archivo .sql de la base de datos con mysqldump.

Al cerrar la sesión del panel se vuelve a la pantalla de bienvenida,
donde el cajero puede iniciar sesión normalmente con "SenaEmpresa".

Atajos de teclado:
    Escape -> Cierra la sesión de administración y vuelve a la bienvenida.
    F5     -> Recarga los datos de la sección actual.

Navegación:
    ir_a_inicio() -> Pantalla de bienvenida (inicio_view).
"""

import flet as ft
from datetime import datetime

from controllers import adminController
from database.bd import DB_HOST, DB_NAME, DB_PORT, DB_USER
from utils.confirmacion import confirmar_view
from utils.notificaciones import mostrar_notificacion

# =========================================================
# OPCIONES FIJAS DEL PANEL
# =========================================================
# Categorías, unidades y empresas de los formularios son listas fijas,
# iguales a las del formulario de productos (utils/crearP_C.py).

ROLES = ["Admin", "Administrador", "Facturador"]
ESTADOS_PRODUCTO = ["activo", "inactivo"]


# =========================================================
# PANEL DE ADMINISTRACIÓN
# =========================================================

def admin_panel_view(pagina: ft.Page, ir_a_inicio, admin):
    """
    Renderiza el panel completo de administración con sus 4 secciones.

    Parámetros:
        pagina     -> Instancia de la página Flet.
        ir_a_inicio -> Callback para volver a la pantalla de bienvenida
                       (se usa como "Cerrar sesión").
        admin      -> Diccionario del administrador autenticado
                      (id_usuario, nombre, usuario, rol).
    """

    # Limpio la pantalla y doy tamaño al panel
    pagina.clean()
    pagina.window.width = 1280
    pagina.window.height = 820

    pagina.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    pagina.vertical_alignment = ft.MainAxisAlignment.START

    # FilePicker: necesario para elegir dónde guardar el respaldo .sql
    selector_archivos = ft.FilePicker()
    pagina.services.append(selector_archivos)

    # Sección actualmente visible (se usa para F5 y para resaltar el botón)
    seccion_actual = {"valor": "indicadores"}

    # ================== FUNCIONES GENERALES ==================

    def money(valor):
        """Formatea un número como moneda sin decimales innecesarios."""
        valor = float(valor or 0)
        return f"${valor:,.2f}" if not valor.is_integer() else f"${valor:,.0f}"

    def formatear_fecha(valor):
        """Convierte una fecha de la BD en texto legible (dd/mm/aaaa hh:mm)."""
        try:
            return valor.strftime("%d/%m/%Y %H:%M")
        except AttributeError:
            return str(valor or "-")

    def preparar_dialogo(dialogo):
        """
        Prepara un AlertDialog para abrirse/cerrarse desde el panel.

        Retorna (abrir, cerrar): funciones para mostrar el diálogo y para
        cerrarlo restaurando el manejo de teclado del panel.
        """
        teclado_anterior = pagina.on_keyboard_event
        estado = {"cerrado": False}

        def cerrar(e=None):
            """Cierra el diálogo y restaura el teclado del panel."""
            if estado["cerrado"]:
                return
            estado["cerrado"] = True
            dialogo.open = False
            if pagina.on_keyboard_event is teclado_dialogo:
                pagina.on_keyboard_event = teclado_anterior
            pagina.update()

        async def teclado_dialogo(e: ft.KeyboardEvent):
            """Escape cierra el diálogo sin perder la sesión de administración."""
            if e.key == "Escape":
                cerrar()

        def abrir(e=None):
            """Muestra el diálogo sobre el panel."""
            pagina.overlay.append(dialogo)
            dialogo.open = True
            pagina.on_keyboard_event = teclado_dialogo
            pagina.update()

        return abrir, cerrar

    def crear_tarjeta(valor, etiqueta, color_valor=ft.Colors.BLACK):
        """Crea una tarjeta de indicador (valor grande + etiqueta)."""
        return ft.Container(
            width=210,
            padding=15,
            border_radius=12,
            bgcolor=ft.Colors.WHITE,
            shadow=ft.BoxShadow(
                blur_radius=8,
                spread_radius=1,
                color=ft.Colors.BLACK_12
            ),
            content=ft.Column(
                [
                    ft.Text(valor, size=24, weight="bold", color=color_valor),
                    ft.Text(etiqueta, size=13, color=ft.Colors.BLACK54),
                ],
                spacing=4,
                horizontal_alignment=ft.CrossAxisAlignment.START,
            ),
        )

    def botones_tabla(items):
        """Crea la fila de acciones (Editar / Eliminar) de una fila de tabla."""
        return ft.Row(
            [ft.TextButton(texto, on_click=accion) for texto, accion in items],
            spacing=2,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    # ================== SECCIÓN: INDICADORES ==================

    fila_tarjetas = ft.Column(spacing=12)
    tabla_ventas = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("#")),
            ft.DataColumn(ft.Text("Fecha")),
            ft.DataColumn(ft.Text("Cliente")),
            ft.DataColumn(ft.Text("Método de pago")),
            ft.DataColumn(ft.Text("Total")),
            ft.DataColumn(ft.Text("Estado")),
            ft.DataColumn(ft.Text("Usuario")),
        ],
        rows=[],
        border=ft.Border.all(1, ft.Colors.BLACK_26),
        border_radius=10,
        vertical_lines=ft.BorderSide(1, ft.Colors.BLACK_26),
        horizontal_lines=ft.BorderSide(1, ft.Colors.BLACK_26),
    )

    def cargar_indicadores():
        """Consulta los indicadores del sistema y pinta tarjetas y últimas ventas."""
        stats = adminController.obtener_estadisticas()
        if not stats:
            mostrar_notificacion(pagina, "No se pudieron cargar los indicadores.", error=True)
            return

        # -------- Tarjetas (en filas de 4) --------
        tarjetas = [
            crear_tarjeta(str(stats.get("ventas_hoy", 0)), "Ventas de hoy", ft.Colors.GREEN_900),
            crear_tarjeta(str(stats.get("pedidos_web_hoy", 0)), f"Pedidos web entregados · {money(stats.get('pedidos_web_total_hoy', 0))}", ft.Colors.GREEN_900),
            crear_tarjeta(str(stats.get("compras_hoy", 0)), f"Compras de hoy · {money(stats.get('compras_total_hoy', 0))}", ft.Colors.BLUE_900),
            crear_tarjeta(str(stats.get("remisiones_hoy", 0)), "Remisiones de hoy", ft.Colors.BLUE_900),
            crear_tarjeta(str(stats.get("productos_total", 0)), f"Productos ({stats.get('productos_activos', 0)} activos)", ft.Colors.BLACK),
            crear_tarjeta(str(stats.get("productos_stock_bajo", 0)), "Productos con stock bajo", ft.Colors.RED_900),
            crear_tarjeta(str(stats.get("clientes", 0)), "Clientes registrados", ft.Colors.BLACK),
            crear_tarjeta(str(stats.get("proveedores", 0)), "Proveedores registrados", ft.Colors.BLACK),
            crear_tarjeta(str(stats.get("usuarios_total", 0)), f"Usuarios ({stats.get('usuarios_admin', 0)} admin · {stats.get('usuarios_facturador', 0)} facturadores)", ft.Colors.BLACK),
        ]

        fila_tarjetas.controls.clear()
        for inicio_fila in range(0, len(tarjetas), 4):
            fila_tarjetas.controls.append(
                ft.Row(tarjetas[inicio_fila:inicio_fila + 4], spacing=12)
            )

        # -------- Últimas ventas --------
        tabla_ventas.rows.clear()
        for venta in stats.get("ultimas_ventas", []):
            estado = str(venta.get("estado", "")).upper()
            color_estado = ft.Colors.GREEN if estado == "ACTIVA" else ft.Colors.RED
            tabla_ventas.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(venta.get("id_venta", "-")))),
                        ft.DataCell(ft.Text(formatear_fecha(venta.get("fecha")))),
                        ft.DataCell(ft.Text(str(venta.get("cliente", "-")))),
                        ft.DataCell(ft.Text(str(venta.get("metodo_pago", "-")))),
                        ft.DataCell(ft.Text(money(venta.get("total")), weight="bold")),
                        ft.DataCell(ft.Text(estado, color=color_estado)),
                        ft.DataCell(ft.Text(str(venta.get("usuario", "-")))),
                    ]
                )
            )

        pagina.update()

    # ================== SECCIÓN: USUARIOS ==================

    contador_usuarios = ft.Text("", size=15, weight="bold")

    tabla_usuarios = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Nombre")),
            ft.DataColumn(ft.Text("Login")),
            ft.DataColumn(ft.Text("Rol")),
            ft.DataColumn(ft.Text("Acciones")),
        ],
        rows=[],
        border=ft.Border.all(1, ft.Colors.BLACK_26),
        border_radius=10,
        vertical_lines=ft.BorderSide(1, ft.Colors.BLACK_26),
        horizontal_lines=ft.BorderSide(1, ft.Colors.BLACK_26),
    )

    def cargar_usuarios():
        """Consulta los usuarios y pinta una fila por cada uno."""
        usuarios = adminController.listar_usuarios()
        contador_usuarios.value = f"Usuarios registrados: {len(usuarios)}"
        tabla_usuarios.rows.clear()

        for u in usuarios:
            es_fila_actual = u.get("id_usuario") == admin.get("id_usuario")
            tabla_usuarios.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(u.get("id_usuario", "-")))),
                        ft.DataCell(ft.Text(str(u.get("nombre", "-")) + (" (tú)" if es_fila_actual else ""))),
                        ft.DataCell(ft.Text(str(u.get("usuario", "-")))),
                        ft.DataCell(ft.Text(str(u.get("rol", "-")), weight="bold")),
                        ft.DataCell(
                            botones_tabla([
                                ("✏️ Editar", lambda e, u=u: dialogo_usuario(u)),
                                ("🔑 Contraseña", lambda e, u=u: dialogo_password(u)),
                                ("🗑️ Eliminar", lambda e, u=u: eliminar_usuario(u)),
                            ])
                        ),
                    ]
                )
            )
        pagina.update()

    def dialogo_usuario(u=None):
        """Abre el diálogo para crear un usuario o editar uno existente."""
        es_edicion = u is not None
        datos = u or {}

        campo_nombre = ft.TextField(label="Nombre completo", width=320, value=str(datos.get("nombre", "")), autofocus=True)
        campo_login = ft.TextField(label="Usuario (login)", width=320, value=str(datos.get("usuario", "")))
        campo_password = ft.TextField(label="Contraseña", password=True, can_reveal_password=True, width=320)
        campo_rol = ft.Dropdown(
            label="Rol",
            width=320,
            value=str(datos.get("rol", "Admin")),
            options=[ft.dropdown.Option(r) for r in ROLES],
        )
        mensaje = ft.Text("", color=ft.Colors.RED, size=12)

        dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Text("Editar usuario" if es_edicion else "Nuevo usuario", weight="bold"),
            content=ft.Column(
                [
                    campo_nombre,
                    campo_login,
                    *([] if es_edicion else [campo_password]),
                    campo_rol,
                    mensaje,
                ],
                width=340,
                spacing=12,
                tight=True,
            ),
        )
        abrir, cerrar = preparar_dialogo(dialogo)

        def guardar(e=None):
            """Valida y guarda los cambios del usuario."""
            try:
                if es_edicion:
                    adminController.actualizar_usuario(
                        u["id_usuario"],
                        campo_nombre.value,
                        campo_login.value,
                        campo_rol.value,
                        admin.get("id_usuario"),
                    )
                    texto = f"Usuario '{campo_login.value}' actualizado."
                else:
                    adminController.crear_usuario_admin(
                        campo_nombre.value,
                        campo_login.value,
                        campo_password.value,
                        campo_rol.value,
                    )
                    texto = f"Usuario '{campo_login.value}' creado."
            except ValueError as error:
                mensaje.value = str(error)
                pagina.update()
                return
            except Exception as error:
                print(f"Error al guardar usuario: {error}")
                mensaje.value = "No fue posible guardar el usuario."
                pagina.update()
                return

            cerrar()
            mostrar_notificacion(pagina, texto)
            cargar_usuarios()

        dialogo.actions = [
            ft.TextButton("Cancelar [Esc]", on_click=cerrar),
            ft.Button("Guardar", bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE, on_click=guardar),
        ]
        dialogo.actions_alignment = ft.MainAxisAlignment.END
        abrir()

    def dialogo_password(u):
        """Abre el diálogo para cambiar la contraseña de un usuario."""
        campo_password = ft.TextField(label="Nueva contraseña", password=True, can_reveal_password=True, width=320, autofocus=True)
        campo_confirmacion = ft.TextField(label="Repetir contraseña", password=True, can_reveal_password=True, width=320)
        mensaje = ft.Text("", color=ft.Colors.RED, size=12)

        dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Contraseña de {u.get('usuario', '')}", weight="bold"),
            content=ft.Column(
                [campo_password, campo_confirmacion, mensaje],
                width=340,
                spacing=12,
                tight=True,
            ),
        )
        abrir, cerrar = preparar_dialogo(dialogo)

        def guardar(e=None):
            """Valida y guarda la nueva contraseña."""
            try:
                adminController.cambiar_password(
                    u["id_usuario"], campo_password.value, campo_confirmacion.value
                )
            except ValueError as error:
                mensaje.value = str(error)
                pagina.update()
                return
            except Exception as error:
                print(f"Error al cambiar contraseña: {error}")
                mensaje.value = "No fue posible cambiar la contraseña."
                pagina.update()
                return

            cerrar()
            mostrar_notificacion(pagina, f"Contraseña de '{u.get('usuario', '')}' actualizada.")

        dialogo.actions = [
            ft.TextButton("Cancelar [Esc]", on_click=cerrar),
            ft.Button("Guardar", bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE, on_click=guardar),
        ]
        dialogo.actions_alignment = ft.MainAxisAlignment.END
        abrir()

    def eliminar_usuario(u):
        """Pide confirmación y elimina al usuario seleccionado."""
        def al_confirmar(confirmado):
            if not confirmado:
                return
            try:
                adminController.eliminar_usuario(u["id_usuario"], admin.get("id_usuario"))
                mostrar_notificacion(pagina, f"Usuario '{u.get('usuario', '')}' eliminado.")
                cargar_usuarios()
            except ValueError as error:
                mostrar_notificacion(pagina, str(error), error=True)
            except Exception as error:
                print(f"Error al eliminar usuario: {error}")
                mostrar_notificacion(pagina, "No fue posible eliminar el usuario.", error=True)

        dialogo = confirmar_view(
            pagina,
            f"¿Eliminar el usuario '{u.get('usuario', '')}'? Esta acción no se puede deshacer.",
            al_confirmar,
        )
        pagina.overlay.append(dialogo)
        dialogo.open = True
        pagina.update()

    # ================== SECCIÓN: PRODUCTOS ==================

    contador_productos = ft.Text("", size=15, weight="bold")
    campo_buscar = ft.TextField(
        label="Buscar por código, nombre o categoría",
        width=350,
        on_submit=lambda e: cargar_productos(),
    )

    tabla_productos = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Código")),
            ft.DataColumn(ft.Text("Nombre")),
            ft.DataColumn(ft.Text("Categoría")),
            ft.DataColumn(ft.Text("Unidad")),
            ft.DataColumn(ft.Text("Precio")),
            ft.DataColumn(ft.Text("Stock")),
            ft.DataColumn(ft.Text("Estado")),
            ft.DataColumn(ft.Text("Acciones")),
        ],
        rows=[],
        border=ft.Border.all(1, ft.Colors.BLACK_26),
        border_radius=10,
        vertical_lines=ft.BorderSide(1, ft.Colors.BLACK_26),
        horizontal_lines=ft.BorderSide(1, ft.Colors.BLACK_26),
    )

    def cargar_productos():
        """Consulta el catálogo (con el filtro activo) y pinta las filas."""
        productos = adminController.listar_productos(campo_buscar.value)
        contador_productos.value = f"Productos: {len(productos)}"
        tabla_productos.rows.clear()

        for p in productos:
            activo = str(p.get("estado", "")).strip().lower() == "activo"
            tabla_productos.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(p.get("codigo", "-")))),
                        ft.DataCell(ft.Text(str(p.get("nombre", "-")))),
                        ft.DataCell(ft.Text(str(p.get("categoria", "-")))),
                        ft.DataCell(ft.Text(str(p.get("unidad", "-")))),
                        ft.DataCell(ft.Text(money(p.get("precio")))),
                        ft.DataCell(ft.Text(str(int(float(p.get("stock", 0) or 0))))),
                        ft.DataCell(
                            ft.Text(
                                "Activo" if activo else "Inactivo",
                                color=ft.Colors.GREEN if activo else ft.Colors.RED,
                                weight="bold",
                            )
                        ),
                        ft.DataCell(
                            botones_tabla([
                                ("✏️ Editar", lambda e, p=p: dialogo_producto(p)),
                                ("🗑️ Eliminar", lambda e, p=p: eliminar_producto(p)),
                            ])
                        ),
                    ]
                )
            )
        pagina.update()

    def opciones_con_valor(opciones, valor):
        """Devuelve las opciones garantizando que el valor actual esté incluido."""
        valor = str(valor or "").strip()
        if valor and valor not in opciones:
            return [valor] + list(opciones)
        return list(opciones)

    def dialogo_producto(p=None):
        """Abre el diálogo para crear un producto o editar uno existente."""
        es_edicion = p is not None
        datos = p or {}

        campo_codigo = ft.TextField(label="Código", width=320, value=str(datos.get("codigo", "")), autofocus=True)
        campo_nombre = ft.TextField(label="Nombre", width=320, value=str(datos.get("nombre", "")))
        # Opciones de los desplegables (las mismas del formulario de productos)
        opciones_unidad = ["UND", "Kg", "Gr", "Lt"]
        opciones_lugar = ["SenaEmpresa", "Campesena"]
        opciones_categoria = [
            "Abonos y Sustratos",
            "Frutas y Hortalizas",
            "Cereales, Granos y Forrajes",
            "Material Vegetal y Flores",
            "Embutidos y Cárnicos",
            "Bebidas y Refrescos",
            "Salsas y Conservas",
            "Lácteos y Derivados",
            "Repostería, Dulces y Licores",
            "Pecuario y Acuícola",
        ]

        campo_unidad = ft.Dropdown(
            label="Unidad",
            width=320,
            value=str(datos.get("unidad") or opciones_unidad[0]),
            options=[ft.dropdown.Option(o) for o in opciones_con_valor(opciones_unidad, datos.get("unidad"))],
        )
        campo_lugar = ft.Dropdown(
            label="¿De dónde viene?",
            width=320,
            value=str(datos.get("lugar") or opciones_lugar[0]),
            options=[ft.dropdown.Option(o) for o in opciones_con_valor(opciones_lugar, datos.get("lugar"))],
        )
        campo_categoria = ft.Dropdown(
            label="Categoría",
            width=320,
            value=str(datos.get("categoria") or opciones_categoria[0]),
            options=[ft.dropdown.Option(o) for o in opciones_con_valor(opciones_categoria, datos.get("categoria"))],
        )
        campo_precio = ft.TextField(label="Precio", width=320, value=str(datos.get("precio", "")), keyboard_type=ft.KeyboardType.NUMBER)
        campo_stock = ft.TextField(label="Stock", width=320, value=str(datos.get("stock", "")), keyboard_type=ft.KeyboardType.NUMBER)
        campo_estado = ft.Dropdown(
            label="Estado",
            width=320,
            value=str(datos.get("estado", "inactivo")).strip().lower(),
            options=[ft.dropdown.Option(o) for o in opciones_con_valor(ESTADOS_PRODUCTO, str(datos.get("estado", "")).strip().lower())],
        )
        campo_descripcion = ft.TextField(
            label="Descripción",
            width=320,
            value=str(datos.get("descripcion") or ""),
            multiline=True,
            min_lines=2,
            max_lines=3,
        )
        mensaje = ft.Text("", color=ft.Colors.RED, size=12)

        dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Text("Editar producto" if es_edicion else "Nuevo producto", weight="bold"),
            content=ft.Column(
                [
                    campo_codigo,
                    campo_nombre,
                    campo_unidad,
                    campo_lugar,
                    campo_categoria,
                    campo_precio,
                    campo_stock,
                    campo_estado,
                    campo_descripcion,
                    mensaje,
                ],
                width=340,
                height=520,
                spacing=10,
                tight=True,
                scroll=ft.ScrollMode.AUTO,
            ),
        )
        abrir, cerrar = preparar_dialogo(dialogo)

        def guardar(e=None):
            """Valida y guarda los datos del producto."""
            nuevos_datos = {
                "codigo": campo_codigo.value,
                "nombre": campo_nombre.value,
                "unidad": campo_unidad.value,
                "lugar": campo_lugar.value,
                "categoria": campo_categoria.value,
                "precio": campo_precio.value,
                "stock": campo_stock.value,
                "estado": campo_estado.value,
                "descripcion": campo_descripcion.value,
            }
            try:
                adminController.guardar_producto(
                    nuevos_datos,
                    p["id_producto"] if es_edicion else None,
                )
            except ValueError as error:
                mensaje.value = str(error)
                pagina.update()
                return
            except Exception as error:
                print(f"Error al guardar producto: {error}")
                mensaje.value = "No fue posible guardar el producto."
                pagina.update()
                return

            cerrar()
            mostrar_notificacion(
                pagina,
                f"Producto '{nuevos_datos['nombre']}' "
                f"{'actualizado' if es_edicion else 'creado'}.",
            )
            cargar_productos()

        dialogo.actions = [
            ft.TextButton("Cancelar [Esc]", on_click=cerrar),
            ft.Button("Guardar", bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE, on_click=guardar),
        ]
        dialogo.actions_alignment = ft.MainAxisAlignment.END
        abrir()

    def eliminar_producto(p):
        """Pide confirmación y elimina el producto seleccionado."""
        def al_confirmar(confirmado):
            if not confirmado:
                return
            try:
                adminController.eliminar_producto(p["id_producto"])
                mostrar_notificacion(pagina, f"Producto '{p.get('nombre', '')}' eliminado.")
                cargar_productos()
            except ValueError as error:
                mostrar_notificacion(pagina, str(error), error=True)
            except Exception as error:
                print(f"Error al eliminar producto: {error}")
                mostrar_notificacion(pagina, "No fue posible eliminar el producto.", error=True)

        dialogo = confirmar_view(
            pagina,
            f"¿Eliminar el producto '{p.get('nombre', '')}' ({p.get('codigo', '')})? Esta acción no se puede deshacer.",
            al_confirmar,
        )
        pagina.overlay.append(dialogo)
        dialogo.open = True
        pagina.update()

    # ================== SECCIÓN: RESPALDO ==================

    async def generar_respaldo(e):
        """Pide dónde guardar y genera el respaldo .sql de la base de datos."""
        fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
        destino = await selector_archivos.save_file(
            dialog_title="Guardar respaldo de la base de datos",
            file_name=f"respaldo_{DB_NAME}_{fecha}.sql",
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["sql"],
        )
        if not destino:
            return  # El usuario canceló el diálogo de guardado

        try:
            adminController.generar_respaldo(destino)
            mostrar_notificacion(pagina, f"Respaldo guardado en: {destino}")
        except ValueError as error:
            mostrar_notificacion(pagina, str(error), error=True)
        except Exception as error:
            print(f"Error al generar respaldo: {error}")
            mostrar_notificacion(pagina, "No se pudo generar el respaldo.", error=True)

    # ================== NAVEGACIÓN ENTRE SECCIONES ==================

    def crear_boton_seccion(nombre, texto, icono):
        """Crea un botón de sección del panel (se resalta cuando está activo)."""
        return ft.Button(
            texto,
            icon=icono,
            width=260,
            height=44,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                text_style=ft.TextStyle(size=15, weight="bold"),
            ),
            on_click=lambda e: mostrar_seccion(nombre),
        )

    def resaltar_boton_activo():
        """Pinta de azul el botón de la sección activa y deja los demás neutros."""
        for nombre, boton in botones_secciones.items():
            activo = nombre == seccion_actual["valor"]
            boton.style = ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                text_style=ft.TextStyle(size=15, weight="bold"),
                bgcolor=ft.Colors.BLUE_700 if activo else None,
                color=ft.Colors.WHITE if activo else None,
            )

    def mostrar_seccion(nombre):
        """Muestra solo el contenedor de la sección elegida."""
        seccion_actual["valor"] = nombre
        contenedores = {
            "indicadores": contenedor_indicadores,
            "usuarios": contenedor_usuarios,
            "productos": contenedor_productos,
            "respaldo": contenedor_respaldo,
        }
        for clave, contenedor in contenedores.items():
            contenedor.visible = clave == nombre
        resaltar_boton_activo()
        pagina.update()

    def recargar_seccion_actual():
        """Recarga los datos de la sección que está visible (atajo F5)."""
        if seccion_actual["valor"] == "indicadores":
            cargar_indicadores()
        elif seccion_actual["valor"] == "usuarios":
            cargar_usuarios()
        elif seccion_actual["valor"] == "productos":
            cargar_productos()
        # Respaldo no tiene datos que recargar

    # ================== CONTENIDO DE CADA SECCIÓN ==================

    # -------- Indicadores --------
    contenedor_indicadores = ft.Container(
        expand=True,
        visible=True,
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Resumen del sistema", size=17, weight="bold"),
                        ft.Button(
                            "Recargar [F5]",
                            icon=ft.Icons.REFRESH,
                            on_click=lambda e: cargar_indicadores(),
                            width=180,
                            height=40,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Divider(),
                ft.Column(
                    [
                        fila_tarjetas,
                        ft.Text("Últimas ventas registradas", size=15, weight="bold"),
                        ft.Row(
                            [tabla_ventas],
                            scroll=ft.ScrollMode.ALWAYS,
                        ),
                    ],
                    expand=True,
                    scroll=ft.ScrollMode.ALWAYS,
                    spacing=15,
                ),
            ],
            expand=True,
            spacing=10,
        ),
    )

    # -------- Usuarios --------
    btn_nuevo_usuario = ft.Button(
        "➕ Nuevo usuario",
        icon=ft.Icons.PEOPLE_ALT,
        on_click=lambda e: dialogo_usuario(),
        width=200,
        height=40,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            text_style=ft.TextStyle(size=15, weight="bold"),
        ),
    )
    btn_recargar_usuarios = ft.Button(
        "Recargar [F5]",
        icon=ft.Icons.REFRESH,
        on_click=lambda e: cargar_usuarios(),
        width=180,
        height=40,
    )

    contenedor_usuarios = ft.Container(
        expand=True,
        visible=False,
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Gestión de usuarios", size=17, weight="bold"),
                        contador_usuarios,
                        ft.Row([btn_recargar_usuarios, btn_nuevo_usuario], spacing=5),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Divider(),
                ft.Container(
                    expand=True,
                    content=ft.Column(
                        [ft.Row([tabla_usuarios], scroll=ft.ScrollMode.ALWAYS)],
                        expand=True,
                        scroll=ft.ScrollMode.ALWAYS,
                    ),
                ),
            ],
            expand=True,
            spacing=10,
        ),
    )

    # -------- Productos --------
    btn_buscar_producto = ft.Button(
        "Buscar",
        icon=ft.Icons.SEARCH,
        on_click=lambda e: cargar_productos(),
        width=130,
        height=40,
    )
    btn_nuevo_producto = ft.Button(
        "➕ Nuevo producto",
        icon=ft.Icons.INVENTORY_2,
        on_click=lambda e: dialogo_producto(),
        width=220,
        height=40,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            text_style=ft.TextStyle(size=15, weight="bold"),
        ),
    )
    btn_recargar_productos = ft.Button(
        "Recargar [F5]",
        icon=ft.Icons.REFRESH,
        on_click=lambda e: cargar_productos(),
        width=180,
        height=40,
    )

    contenedor_productos = ft.Container(
        expand=True,
        visible=False,
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Gestión de productos", size=17, weight="bold"),
                        contador_productos,
                        campo_buscar,
                        ft.Row(
                            [btn_buscar_producto, btn_recargar_productos, btn_nuevo_producto],
                            spacing=5,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Divider(),
                ft.Container(
                    expand=True,
                    content=ft.Column(
                        [ft.Row([tabla_productos], scroll=ft.ScrollMode.ALWAYS)],
                        expand=True,
                        scroll=ft.ScrollMode.ALWAYS,
                    ),
                ),
            ],
            expand=True,
            spacing=10,
        ),
    )

    # -------- Respaldo --------
    btn_generar_respaldo = ft.Button(
        "💾 Generar respaldo (.sql)",
        icon=ft.Icons.SAVE_ALT,
        bgcolor=ft.Colors.GREEN,
        color=ft.Colors.WHITE,
        width=280,
        height=50,
        on_click=generar_respaldo,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            text_style=ft.TextStyle(size=16, weight="bold"),
        ),
    )

    contenedor_respaldo = ft.Container(
        expand=True,
        visible=False,
        content=ft.Column(
            [
                ft.Text("Respaldo de la base de datos", size=17, weight="bold"),
                ft.Divider(),
                ft.Container(
                    padding=30,
                    border_radius=15,
                    bgcolor=ft.Colors.WHITE,
                    shadow=ft.BoxShadow(
                        blur_radius=12,
                        spread_radius=2,
                        color=ft.Colors.BLACK_12
                    ),
                    content=ft.Column(
                        [
                            ft.Text("Base de datos del sistema", size=16, weight="bold"),
                            ft.Text(f"Base de datos: {DB_NAME}"),
                            ft.Text(f"Servidor: {DB_HOST}:{DB_PORT}"),
                            ft.Text(f"Usuario: {DB_USER}"),
                            ft.Divider(),
                            ft.Text(
                                "El respaldo guarda todas las tablas del sistema en un archivo "
                                ".sql que puedes restaurar con phpMyAdmin o la consola de MySQL.",
                                size=13,
                            ),
                            ft.Text(
                                "Requiere que 'mysqldump' esté disponible en el sistema "
                                "(viene instalado junto con MySQL, Laragon o XAMPP).",
                                size=13,
                                color=ft.Colors.BLACK54,
                            ),
                            btn_generar_respaldo,
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=15,
                    ),
                ),
            ],
            expand=True,
            spacing=10,
        ),
    )

    # ================== ESTRUCTURA DEL PANEL ==================

    botones_secciones = {
        "indicadores": crear_boton_seccion("indicadores", "📊 Indicadores", ft.Icons.DASHBOARD),
        "usuarios": crear_boton_seccion("usuarios", "👥 Usuarios", ft.Icons.PEOPLE_ALT),
        "productos": crear_boton_seccion("productos", "📦 Productos", ft.Icons.INVENTORY_2),
        "respaldo": crear_boton_seccion("respaldo", "💾 Respaldo", ft.Icons.SAVE_ALT),
    }

    def cerrar_sesion(e=None):
        """Vuelve a la pantalla de bienvenida (cierra la sesión de administración)."""
        ir_a_inicio()

    async def teclado(e: ft.KeyboardEvent):
        """Escape cierra la sesión; F5 recarga la sección actual."""
        if e.key == "Escape":
            cerrar_sesion()
        elif e.key == "F5":
            recargar_seccion_actual()

    pagina.on_keyboard_event = teclado

    # Barra superior: título, administrador autenticado y botón de cerrar sesión
    header = ft.Container(
        bgcolor=ft.Colors.WHITE,
        border=ft.Border.all(1, ft.Colors.BLACK),
        padding=ft.Padding.symmetric(horizontal=20, vertical=10),
        content=ft.Row(
            [
                ft.Row(
                    [
                        ft.Image(src="Logo_sena.png", width=50, height=50),
                        ft.Text("Panel de Administración", size=18, weight="bold"),
                        ft.Text(f"Administrador: {admin.get('nombre', '')}", size=15),
                    ],
                    spacing=15,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    expand=True,
                ),
                ft.Button(
                    "Cerrar sesión [Esc]",
                    icon=ft.Icons.LOGOUT,
                    bgcolor=ft.Colors.RED,
                    color=ft.Colors.WHITE,
                    on_click=cerrar_sesion,
                    width=230,
                    height=40,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

    pagina.add(
        ft.Column(
            [
                header,
                ft.Container(
                    bgcolor=ft.Colors.WHITE,
                    border=ft.Border.all(1, ft.Colors.BLACK),
                    padding=ft.Padding.symmetric(horizontal=20, vertical=10),
                    content=ft.Row(
                        list(botones_secciones.values()),
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=15,
                    ),
                ),
                ft.Container(
                    expand=True,
                    padding=20,
                    content=ft.Column(
                        [
                            contenedor_indicadores,
                            contenedor_usuarios,
                            contenedor_productos,
                            contenedor_respaldo,
                        ],
                        expand=True,
                        spacing=0,
                    ),
                ),
            ],
            expand=True,
            spacing=8,
        )
    )

    # Resalto el botón de la sección con la que arranca el panel
    resaltar_boton_activo()

    # Cargo los datos de la sección inicial
    cargar_indicadores()
