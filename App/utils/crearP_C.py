import flet as ft
from models.ventasModel import (
    crear_cliente, crear_producto, existe_codigo_producto
)
from models.comprasModel import crear_proveedor
from utils.notificaciones import mostrar_notificacion


# ============================================================================
# MÓDULO DE CREACIÓN DE PRODUCTOS, CLIENTES Y PROVEEDORES
# ============================================================================
# Diálogo modal multiuso que permite crear nuevos registros de三种 tipos:
#   - Producto: código, nombre, unidad, empresa, precio, stock, descripción, categoría.
#   - Cliente (Usuario): nombre, documento, dirección, teléfono, rol.
#   - Proveedor: solo nombre.
#
# Flujo del diálogo:
#   1. "elegir"         → El usuario elige entre "Producto" o "Cliente/Proveedor"
#                         usando radio buttons.
#   2. "crear_producto" → Si eligió Producto, se muestra el formulario completo.
#   3. "crear_usuario"  → Si eligió Cliente o Proveedor, se muestra el formulario
#                         correspondiente.
#
# El tipo de tercero (cliente o proveedor) se determina por el parámetro
# tipo_tercero, que viene de la vista que llama a este diálogo.
#
# Dependencias:
#   - models.ventasModel: crear_cliente(), crear_producto(), existe_codigo_producto().
#   - models.comprasModel: crear_proveedor().
#   - utils.notificaciones: mostrar_notificacion().
# ============================================================================


# =========================================================
# VISTA PARA CREAR CLIENTES O PRODUCTOS
# =========================================================


def Crear(pagina: ft.Page, callback, tipo_tercero="cliente"):
    """
    Crea el diálogo de creación de productos, clientes o proveedores.

    Parámetros:
        pagina (ft.Page): Página de Flet donde se mostrará el diálogo.
        callback (callable): Función que recibe un diccionario con los datos
            del registro creado (producto, cliente o proveedor). Se ejecuta
            después de guardar exitosamente en la base de datos.
        tipo_tercero (str): Tipo de tercero a crear. Puede ser "cliente"
            o "proveedor". Determina si se muestra el formulario de cliente
            o el de proveedor al elegir la segunda opción del radio.

    Retorna:
        ft.AlertDialog: Componente de diálogo listo para mostrarse.
    """
    # Guardo el teclado de la vista anterior para restaurarlo al cerrar
    teclado_anterior = pagina.on_keyboard_event

    # Opcion seleccionada por defecto (Producto)
    opcion_seleccionada = "CrearP"

    # Evita que el dialogo se cierre mas de una vez
    dialogo_cerrado = False

    # Fase actual del dialogo: elegir opcion o llenar formulario
    fase = "elegir"

    # -------- CAMPOS FORMULARIO CLIENTE/USUARIO --------

    campo_nombre    = ft.TextField(label="Nombre",    width=300)
    campo_documento = ft.TextField(label="Documento", width=300)
    campo_direccion = ft.TextField(label="Dirección", width=300)
    campo_telefono  = ft.TextField(label="Teléfono",  width=300)
    campo_rol       = ft.TextField(label="Rol/Cargo", width=300)

    # Mensaje de error o validacion
    mensaje_usuario = ft.Text("", color=ft.Colors.RED, size=12)

    # Formulario oculto al inicio, solo se muestra si elige "Crear Usuario"
    form_usuario = ft.Column(
        [
            campo_nombre,
            campo_documento,
            campo_direccion,
            campo_telefono,
            campo_rol,
            mensaje_usuario
        ],
        spacing=10,
        visible=False  # oculto hasta que el usuario elija "👤 Usuario"
    )

    # -------- CAMPOS FORMULARIO PROVEEDOR --------

    campo_nombre_proveedor = ft.TextField(label="Nombre", width=300)
    mensaje_proveedor = ft.Text("", color=ft.Colors.RED, size=12)

    # El formulario de proveedor solo tiene nombre (es más simple)
    form_proveedor = ft.Column(
        [
            campo_nombre_proveedor,
            mensaje_proveedor
        ],
        spacing=10,
        visible=False
    )


    # -------- CAMPOS FORMULARIO PRODUCTO --------

    campo_codigo_producto = ft.TextField(label="Código", width=300)
    campo_nombre_producto = ft.TextField(label="Nombre", width=300)
    # Dropdown de unidad de medida del producto
    campo_unidad = ft.Dropdown(
        label="Unidad",
        width=300,
        value="UND",
        options=[
            ft.dropdown.Option("UND"),
            ft.dropdown.Option("Kg"),
            ft.dropdown.Option("Gr"),
            ft.dropdown.Option("Lt"),
        ]
    )
    # Dropdown de empresa/proveedor del producto
    campo_empresa = ft.Dropdown(
        label="¿De donde viene?",
        width=300,
        value="SenaEmpresa",
        options=[
            ft.dropdown.Option("SenaEmpresa"),
            ft.dropdown.Option("Campesena"),
        ]
    )
    campo_precio = ft.TextField(label="Precio", width=300)
    campo_stock  = ft.TextField(label="Stock",  width=300)
    campo_descripcion = ft.TextField(
        label="Descripción",
        width=300,
        multiline=True,
        min_lines=2,
        max_lines=4,
        keyboard_type=ft.KeyboardType.TEXT
    )
    # Lista de categorías de productos disponibles
    categoria_opciones = [
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
    campo_categoria = ft.Dropdown(
        label="Categoría",
        width=300,
        value="Abonos y Sustratos",
        options=[ft.dropdown.Option(item) for item in categoria_opciones],
    )

    # Mensaje de error o validacion del producto
    mensaje_producto = ft.Text("", color=ft.Colors.RED, size=12)

    # Formulario oculto al inicio, solo se muestra si elige "Crear Producto"
    form_producto = ft.Column(
        [
            campo_codigo_producto,
            campo_nombre_producto,
            campo_unidad,
            campo_empresa,
            campo_precio,
            campo_stock,
            campo_descripcion,
            campo_categoria,
            mensaje_producto
        ],
        spacing=10,
        visible=False  # oculto hasta que el usuario elija "📦 Producto"
    )
    # -------- RADIO GROUP --------
    # Determino la etiqueta e icono según el tipo de tercero
    etiqueta_tercero = "Proveedor" if tipo_tercero == "proveedor" else "Usuario"
    icono_tercero = "🏢" if tipo_tercero == "proveedor" else "👤"

    # Radio buttons para elegir entre Producto y Cliente/Proveedor
    radio_group = ft.RadioGroup(
        value="CrearP",  # opcion por defecto
        on_change=lambda e: on_cambio(e),
        content=ft.Column(
            [
                ft.Radio(value="CrearP", label="📦 Producto"),
                ft.Radio(value="CrearU", label=f"{icono_tercero} {etiqueta_tercero}")
            ],
            spacing=10
        )
    )

    # Contenido del dialogo: primero el radio, luego los formularios
    # Todos los formularios empiezan ocultos
    contenido = ft.Column(
        [radio_group, form_usuario, form_proveedor, form_producto],
        spacing=10
    )

    # -------- FUNCIONES --------

    def on_cambio(e):
        """Actualiza la opción seleccionada cuando el usuario cambia el radio."""
        nonlocal opcion_seleccionada
        opcion_seleccionada = e.control.value

    def cerrar_dialogo():
        """Cierra el diálogo y restaura el teclado anterior."""
        nonlocal dialogo_cerrado
        if dialogo_cerrado:
            return
        dialogo_cerrado = True
        dialog.open = False

        # Solo restauro si el teclado sigue siendo el de este dialogo
        if pagina.on_keyboard_event == teclado_pagina:
            pagina.on_keyboard_event = teclado_anterior

        pagina.update()

    def cancelar(e=None):
        """Cancela la creación y cierra el diálogo."""
        cerrar_dialogo()

    def mostrar_form_usuario():
        """
        Cambia el diálogo a la fase de creación de cliente o proveedor.
        Oculta los radio buttons y muestra el formulario correspondiente
        según tipo_tercero.
        """
        nonlocal fase
        fase = "crear_usuario"

        # Cambio el titulo del dialogo
        if tipo_tercero == "proveedor":
            dialog.title = ft.Text("Crear Proveedor", weight="bold")
        else:
            dialog.title = ft.Text("Crear Cliente 👤 ", weight="bold")

        # Oculto las opciones y muestro el formulario correspondiente
        radio_group.visible = False
        form_usuario.visible = tipo_tercero != "proveedor"
        form_proveedor.visible = tipo_tercero == "proveedor"

        pagina.update()

        # Enfoco el primer campo del formulario
        if tipo_tercero == "proveedor":
            pagina.run_task(enfocar, campo_nombre_proveedor)
        else:
            pagina.run_task(enfocar, campo_nombre)

    def mostrar_form_productos():
        """
        Cambia el diálogo a la fase de creación de producto.
        Oculta los radio buttons y muestra el formulario de producto.
        """
        nonlocal fase
        fase = "crear_producto"

        # Cambio el titulo del dialogo
        dialog.title = ft.Text("Crear Producto 📦 ", weight="bold")

        # Oculto las opciones y muestro el formulario
        radio_group.visible = False
        form_producto.visible = True

        pagina.update()

        # Enfoco el primer campo del formulario
        pagina.run_task(enfocar, campo_codigo_producto)

    async def enfocar(campo):
        """
        Coloca el foco en un campo de texto con un pequeño delay
        para asegurar que el campo esté listo para recibir foco.
        """
        import asyncio
        await asyncio.sleep(0.05)
        await campo.focus()

    def guardar_usuario(e=None):
        """
        Valida y guarda un nuevo cliente o proveedor en la base de datos.
        Si tipo_tercero es "proveedor", delega a guardar_proveedor().
        """
        if tipo_tercero == "proveedor":
            guardar_proveedor()
            return

        # Valido que el nombre no este vacio
        if not campo_nombre.value.strip():
            mensaje_usuario.value = "El nombre es obligatorio"
            pagina.update()
            return

        # Armo el diccionario con los datos del formulario
        datos = {
            'nombre':    campo_nombre.value.strip(),
            'documento': campo_documento.value.strip(),
            'direccion': campo_direccion.value.strip(),
            'telefono':  campo_telefono.value.strip(),
            'rol':       campo_rol.value.strip() or "Cliente"  # si no escribe rol uso "Cliente"
        }

        # Llamo al modelo para insertar en la base de datos
        id_nuevo = crear_cliente(datos)

        if id_nuevo:
            # Agrego el id al diccionario para que seleccionar_cliente lo reciba completo
            datos['id_cliente'] = id_nuevo

            # Llamo el callback con el cliente creado
            # Esto actualiza el campo de cliente en vender.py
            callback(datos)
            cerrar_dialogo()
            mostrar_notificacion(pagina, f"Cliente '{datos['nombre']}' creado correctamente.")
        else:
            mensaje_usuario.value = "Error al guardar el cliente"
            pagina.update()

    def guardar_proveedor(e=None):
        """
        Valida y guarda un nuevo proveedor en la base de datos.
        Solo requiere el nombre como campo obligatorio.
        """
        if not campo_nombre_proveedor.value.strip():
            mensaje_proveedor.value = "El nombre es obligatorio"
            pagina.update()
            return

        datos = {
            "nombre": campo_nombre_proveedor.value.strip()
        }

        id_nuevo = crear_proveedor(datos)

        if id_nuevo:
            datos["id_proveedor"] = id_nuevo
            callback(datos)
            cerrar_dialogo()
            mostrar_notificacion(pagina, f"Proveedor '{datos['nombre']}' creado correctamente.")
        else:
            mensaje_proveedor.value = "Error al guardar el proveedor"
            pagina.update()


    def guardar_producto(e=None):
        """
        Valida y guarda un nuevo producto en la base de datos.
        Realiza validaciones exhaustivas: código único, campos obligatorios,
        y que precio y stock sean numéricos.
        """
        codigo = campo_codigo_producto.value.strip()

        # Validar campos vacíos
        if not codigo:
            mensaje_producto.value = "El código es obligatorio"
            pagina.update()
            return

        # Verifico que el código no esté repetido
        if existe_codigo_producto(codigo):
            mensaje_producto.value = f"El código '{codigo}' ya existe"
            pagina.update()
            return

        if not campo_nombre_producto.value.strip():
            mensaje_producto.value = "El nombre es obligatorio"
            pagina.update()
            return

        if not campo_unidad.value.strip():
            mensaje_producto.value = "La unidad es obligatoria"
            pagina.update()
            return

        if not campo_precio.value.strip():
            mensaje_producto.value = "El precio es obligatorio"
            pagina.update()
            return

        if not campo_stock.value.strip():
            mensaje_producto.value = "El stock es obligatorio"
            pagina.update()
            return

        if not campo_empresa.value.strip():
            mensaje_producto.value = "El lugar es obligatorio"

        # Validar que precio y stock sean numéricos
        try:
            precio = float(campo_precio.value)
        except:
            mensaje_producto.value = "El precio debe ser numérico"
            pagina.update()
            return

        try:
            stock = int(campo_stock.value)
        except:
            mensaje_producto.value = "El stock debe ser un número entero"
            pagina.update()
            return

        # Creo el diccionario con todos los datos del producto
        datos = {
            'codigo': codigo,
            'nombre': campo_nombre_producto.value.strip(),
            'unidad': campo_unidad.value.strip(),
            'lugar': campo_empresa.value.strip(),
            'precio': precio,
            'stock': stock,
            'descripcion': campo_descripcion.value.strip(),
            'categoria': campo_categoria.value.strip() if campo_categoria.value else 'Abonos y Sustratos',
        }
        # Llamo al modelo para insertar en la base de datos
        id_nuevo = crear_producto(datos)

        if id_nuevo:
            datos['id_producto'] = id_nuevo

            callback(datos)
            cerrar_dialogo()
            mostrar_notificacion(pagina, f"Producto '{datos['nombre']}' creado correctamente.")
        else:
            mensaje_producto.value = "Error al guardar el Producto"
            pagina.update()

    def confirmar(e=None):
        """
        Maneja la acción del botón "Confirmar".
        Su comportamiento cambia según la fase actual:
        - "elegir": muestra el formulario correspondiente.
        - "crear_usuario": guarda el cliente/proveedor.
        - "crear_producto": guarda el producto.
        """
        # Fase 1: el usuario esta eligiendo entre Producto o Usuario
        if fase == "elegir":
            if opcion_seleccionada == "CrearU":
                # Si eligio Usuario muestro el formulario
                mostrar_form_usuario()
            elif opcion_seleccionada =="CrearP":
                    mostrar_form_productos()
            else:
                # Si eligio Producto cierro y aviso a vender.py
                cerrar_dialogo()
                callback(opcion_seleccionada)

        # Fase 2: el usuario esta llenando el formulario de cliente
        elif fase == "crear_usuario":
            guardar_usuario()
        elif fase == "crear_producto":
            guardar_producto()

    # -------- TECLADO --------

    async def teclado(e: ft.KeyboardEvent):
        """
        Handler de teclado del diálogo.

        - Escape: cierra el diálogo.
        - Enter: confirma la acción actual.
        """
        if e.key == "Escape":
            cancelar()
        elif e.key == "Enter":
            confirmar()

    # Reemplazo temporalmente el teclado de vender.py
    async def teclado_pagina(e: ft.KeyboardEvent):
        await teclado(e)

    # -------- DIALOG --------

    # Construyo el diálogo modal con los radio buttons, formularios y botones
    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("¿Que deseas crear?", weight="bold"),
        content=ft.Container(
            width=320,
            content=contenido
        ),
        actions=[
            ft.TextButton("Cancelar", on_click=cancelar),
            ft.Button(
                "Confirmar",
                bgcolor=ft.Colors.GREEN,
                color=ft.Colors.WHITE,
                on_click=confirmar
            )
        ],
        actions_alignment=ft.MainAxisAlignment.END
    )

    # Activo el teclado de este dialogo
    pagina.on_keyboard_event = teclado_pagina

    return dialog
