"""Pantalla para modificar facturas de venta, compra y remisión."""
from datetime import datetime
import flet as ft

from controllers.actualizarDocumentosController import cargar_documento, actualizar_documento
from utils.buscarProducto import buscar_producto_view
from utils.buscarCliente import buscar_cliente_view
from utils.buscarProveedor import buscar_proveedor_view
from utils.notificaciones import mostrar_notificacion


def actualizar_facturas_view(pagina: ft.Page, ir_a_menu, usuario):
    pagina.clean()
    pagina.window.width = 1280
    pagina.window.height = 780

    productos = []
    tercero_actual = None
    tipo_actual = None

    tipo = ft.Dropdown(
        label="Tipo de documento", width=190, value="VENTA",
        options=[ft.dropdown.Option("VENTA"), ft.dropdown.Option("COMPRA"), ft.dropdown.Option("REMISION")],
    )
    numero = ft.TextField(label="Número", width=120)
    fecha = ft.TextField(label="Fecha (DD/MM/AAAA HH:MM)", width=220)
    tercero = ft.TextField(label="Cliente / proveedor", width=260, read_only=True)
    metodo_pago = ft.TextField(label="Método de pago", width=180)
    dinero_recibido = ft.TextField(label="Dinero recibido", width=150)
    cambio = ft.TextField(label="Cambio", width=120)
    tipo_remision = ft.TextField(label="Tipo de remisión", width=260)
    notas = ft.TextField(label="Notas", width=400, multiline=True, min_lines=1, max_lines=2)
    total = ft.Text("Total: $0", size=16, weight="bold")
    estado = ft.Text("Seleccione el tipo y número, luego cargue el documento.")

    tabla = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID")), ft.DataColumn(ft.Text("Producto")),
            ft.DataColumn(ft.Text("Cantidad")), ft.DataColumn(ft.Text("Precio unitario")),
            ft.DataColumn(ft.Text("Subtotal")), ft.DataColumn(ft.Text("Acción")),
        ], rows=[], border_radius=10,
    )

    def numero_decimal(valor, nombre):
        try:
            return float(str(valor).replace(",", "."))
        except (TypeError, ValueError):
            raise ValueError(f"{nombre} inválido.")

    def formatear(valor):
        valor = float(valor or 0)
        return str(int(valor)) if valor.is_integer() else f"{valor:.3f}".rstrip("0").rstrip(".")

    def recalcular():
        valor = sum(float(p.get("cantidad", 0)) * float(p.get("precio", 0) or 0) for p in productos)
        total.value = "Remisión sin valor comercial" if tipo.value == "REMISION" else f"Total: ${valor:,.2f}"

    def pintar_tabla():
        tabla.rows.clear()
        for indice, producto in enumerate(productos):
            cantidad = ft.TextField(value=formatear(producto.get("cantidad", 0)), width=100, dense=True)
            precio = ft.TextField(value=f"{float(producto.get('precio', 0) or 0):.2f}", width=120, dense=True,
                                  visible=tipo.value != "REMISION")

            def guardar_linea(_, i=indice, campo_cantidad=cantidad, campo_precio=precio):
                try:
                    productos[i]["cantidad"] = numero_decimal(campo_cantidad.value, "Cantidad")
                    productos[i]["precio"] = 0 if tipo.value == "REMISION" else numero_decimal(campo_precio.value, "Precio")
                    if productos[i]["cantidad"] <= 0 or productos[i]["precio"] < 0:
                        raise ValueError("La cantidad debe ser mayor que cero.")
                    productos[i]["subtotal"] = productos[i]["cantidad"] * productos[i]["precio"]
                    pintar_tabla()
                    pagina.update()
                except ValueError as error:
                    mostrar_notificacion(pagina, str(error), error=True)

            def borrar_linea(_, i=indice):
                productos.pop(i)
                pintar_tabla()
                pagina.update()

            tabla.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(str(producto.get("id", "-")))),
                ft.DataCell(ft.Text(producto.get("nombre", "Sin nombre"))),
                ft.DataCell(cantidad), ft.DataCell(precio),
                ft.DataCell(ft.Text(f"${float(producto.get('subtotal', 0) or 0):,.2f}")),
                ft.DataCell(ft.Row([
                    ft.IconButton(icon=ft.Icons.SAVE, tooltip="Aplicar línea", on_click=guardar_linea),
                    ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, tooltip="Quitar línea", on_click=borrar_linea),
                ], tight=True)),
            ]))
        recalcular()

    def actualizar_campos_tipo():
        es_venta = tipo.value == "VENTA"
        es_remision = tipo.value == "REMISION"
        metodo_pago.visible = es_venta
        dinero_recibido.visible = es_venta
        cambio.visible = es_venta
        tipo_remision.visible = es_remision
        pagina.update()

    def seleccionar_tercero(seleccionado):
        nonlocal tercero_actual
        tercero_actual = seleccionado
        tercero.value = seleccionado.get("nombre", "Sin nombre")
        pagina.update()

    def buscar_tercero(_=None):
        if tipo.value == "COMPRA":
            dialogo = buscar_proveedor_view(pagina, seleccionar_tercero)
        else:
            dialogo = buscar_cliente_view(pagina, seleccionar_tercero)
        pagina.overlay.append(dialogo)
        dialogo.open = True
        pagina.update()

    def agregar_producto(seleccionado):
        producto = dict(seleccionado)
        producto["id"] = producto.get("id") or producto.get("id_producto")
        producto["cantidad"] = float(producto.get("cantidad", 1) or 1)
        producto["precio"] = 0 if tipo.value == "REMISION" else float(producto.get("precio", 0) or 0)
        producto["subtotal"] = producto["cantidad"] * producto["precio"]
        productos.append(producto)
        pintar_tabla()
        pagina.update()

    def buscar_producto(_=None):
        dialogo = buscar_producto_view(pagina, agregar_producto, mostrar_precio=tipo.value != "REMISION")
        pagina.overlay.append(dialogo)
        dialogo.open = True
        pagina.update()

    def cargar(_=None):
        nonlocal productos, tercero_actual, tipo_actual
        try:
            datos = cargar_documento(tipo.value, int(numero.value))
        except ValueError:
            datos = None
        if not datos:
            mostrar_notificacion(pagina, "No se encontró el documento solicitado.", error=True)
            return
        cabecera = datos["cabecera"]
        if cabecera.get("estado") != "ACTIVA":
            mostrar_notificacion(pagina, "No puede editar un documento anulado.", error=True)
            return
        tipo_actual = tipo.value
        tercero_actual = datos.get("tercero")
        tercero.value = (tercero_actual or {}).get("nombre", "")
        fecha_valor = cabecera.get("fecha")
        fecha.value = fecha_valor.strftime("%d/%m/%Y %H:%M") if hasattr(fecha_valor, "strftime") else str(fecha_valor)
        metodo_pago.value = cabecera.get("metodo_pago", "")
        dinero_recibido.value = str(cabecera.get("dinero_recibido", 0) or 0)
        cambio.value = str(cabecera.get("cambio", 0) or 0)
        tipo_remision.value = cabecera.get("tipo_remision", "")
        notas.value = cabecera.get("notas", "") or ""
        productos = [dict(p) for p in datos["productos"]]
        for producto in productos:
            producto["precio"] = 0 if tipo.value == "REMISION" else float(producto.get("precio", 0) or 0)
            producto["subtotal"] = float(producto.get("cantidad", 0)) * producto["precio"]
        actualizar_campos_tipo()
        pintar_tabla()
        estado.value = f"Editando {tipo.value.lower()} #{numero.value}. Modifique las líneas y guarde."
        pagina.update()

    def guardar(_=None):
        if not tipo_actual or tipo_actual != tipo.value:
            mostrar_notificacion(pagina, "Cargue primero el documento del tipo seleccionado.", error=True)
            return
        if not tercero_actual:
            mostrar_notificacion(pagina, "Seleccione un cliente o proveedor.", error=True)
            return
        try:
            fecha_db = datetime.strptime(fecha.value.strip(), "%d/%m/%Y %H:%M").strftime("%Y-%m-%d %H:%M:%S")
            id_tercero = tercero_actual.get("id_proveedor") if tipo.value == "COMPRA" else tercero_actual.get("id_cliente")
            cabecera = {"fecha": fecha_db, "id_tercero": id_tercero, "notas": notas.value or ""}
            if tipo.value == "VENTA":
                cabecera.update({"metodo_pago": metodo_pago.value.strip(),
                                 "dinero_recibido": numero_decimal(dinero_recibido.value, "Dinero recibido"),
                                 "cambio": numero_decimal(cambio.value, "Cambio")})
            elif tipo.value == "REMISION":
                cabecera["tipo_remision"] = tipo_remision.value.strip()
            if not id_tercero:
                raise ValueError("El tercero seleccionado no es válido.")
        except ValueError as error:
            mostrar_notificacion(pagina, str(error), error=True)
            return
        correcto, mensaje = actualizar_documento(tipo.value, numero.value, cabecera, productos)
        mostrar_notificacion(pagina, mensaje, error=not correcto)
        if correcto:
            cargar()

    actualizar_campos_tipo()
    pagina.add(ft.Column([
        ft.Row([ft.Text("Actualizar documentos", size=22, weight="bold"),
                ft.Text(f"Usuario: {usuario.get('usuario', '')}"),
                ft.Button("Volver", on_click=lambda _: ir_a_menu(usuario))],
               alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Divider(),
        ft.Row([tipo, numero, ft.Button("Cargar documento", icon=ft.Icons.SEARCH, on_click=cargar), estado], wrap=True),
        ft.Row([fecha, tercero, ft.Button("Buscar cliente/proveedor", on_click=buscar_tercero)], wrap=True),
        ft.Row([metodo_pago, dinero_recibido, cambio, tipo_remision], wrap=True),
        notas,
        ft.Row([ft.Button("Agregar producto", icon=ft.Icons.ADD, on_click=buscar_producto),
                ft.Button("Guardar actualización", icon=ft.Icons.SAVE, on_click=guardar), total]),
        ft.Container(content=ft.Column([ft.Row([tabla], scroll=ft.ScrollMode.AUTO)], scroll=ft.ScrollMode.AUTO), expand=True),
    ], expand=True, scroll=ft.ScrollMode.AUTO, spacing=12))
    tipo.on_change = lambda _: actualizar_campos_tipo()
    pagina.on_keyboard_event = lambda e: ir_a_menu(usuario) if e.key == "Escape" else None
    pagina.update()
