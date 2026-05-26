import flet as ft
from models.ventasModel import (
    crear_cliente, crear_producto
)


# =========================================================
# VISTA PARA CREAR CLIENTES O PRODUCTOS
# =========================================================


def Crear(pagina: ft.Page, callback):

    # Guardo el teclado de la vista anterior para restaurarlo al cerrar
    teclado_anterior = pagina.on_keyboard_event

    # Opcion seleccionada por defecto
    opcion_seleccionada = "CrearP"

    # Evita que el dialogo se cierre mas de una vez
    dialogo_cerrado = False

    # Fase actual del dialogo: elegir opcion o llenar formulario
    fase = "elegir"

    # -------- CAMPOS FORMULARIO USUARIO --------

    campo_nombre    = ft.TextField(label="Nombre",    width=300)
    campo_documento = ft.TextField(label="Documento", width=300)
    campo_direccion = ft.TextField(label="Dirección", width=300)
    campo_telefono  = ft.TextField(label="Teléfono",  width=300)
    campo_rol       = ft.TextField(label="Rol/Cargo", width=300)

    # Mensaje de error o validacion
    mensaje = ft.Text("", color=ft.Colors.RED, size=12)

    # Formulario oculto al inicio, solo se muestra si elige "Crear Usuario"
    form_usuario = ft.Column(
        [
            campo_nombre,
            campo_documento,
            campo_direccion,
            campo_telefono,
            campo_rol,
            mensaje
        ],
        spacing=10,
        visible=False  # oculto hasta que el usuario elija "👤 Usuario"
    )


    # -------- CAMPOS FORMULARIO PRODUCTO --------

    campo_nombre_producto = ft.TextField(label="Nombre", width=300)
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

    # Mensaje de error o validacion
    mensaje = ft.Text("", color=ft.Colors.RED, size=12)

    # Formulario oculto al inicio, solo se muestra si elige "Crear Producto"
    form_producto = ft.Column(
        [
            campo_nombre_producto,
            campo_unidad,
            campo_empresa,
            campo_precio,
            campo_stock,
            mensaje
        ],
        spacing=10,
        visible=False  # oculto hasta que el usuario elija "👤 Usuario"
    )
    # -------- RADIO GROUP --------

    # Opciones que el usuario puede elegir
    radio_group = ft.RadioGroup(
        value="CrearP",  # opcion por defecto
        on_change=lambda e: on_cambio(e),
        content=ft.Column(
            [
                ft.Radio(value="CrearP", label="📦 Producto"),
                ft.Radio(value="CrearU", label="👤 Usuario")
            ],
            spacing=10
        )
    )

    # Contenido del dialogo: primero el radio, luego el formulario
    # El formulario empieza oculto
    contenido = ft.Column(
        [radio_group, form_usuario, form_producto],
        spacing=10
    )

    # -------- FUNCIONES --------

    # Actualizo la opcion seleccionada cuando el usuario cambia el radio
    def on_cambio(e):
        nonlocal opcion_seleccionada
        opcion_seleccionada = e.control.value

    # Cierro el dialogo y restauro el teclado anterior
    def cerrar_dialogo():
        nonlocal dialogo_cerrado
        if dialogo_cerrado:
            return
        dialogo_cerrado = True
        dialog.open = False

        # Solo restauro si el teclado sigue siendo el de este dialogo
        if pagina.on_keyboard_event == teclado_pagina:
            pagina.on_keyboard_event = teclado_anterior

        pagina.update()

    # Cancelo sin hacer nada
    def cancelar(e=None):
        cerrar_dialogo()

    # Cambio el dialogo a la fase de crear usuario
    # Oculto el radio y muestro el formulario
    def mostrar_form_usuario():
        nonlocal fase
        fase = "crear_usuario"

        # Cambio el titulo del dialogo
        dialog.title = ft.Text("Crear Cliente 👤 ", weight="bold")

        # Oculto las opciones y muestro el formulario
        radio_group.visible = False
        form_usuario.visible = True

        pagina.update()

        # Enfoco el primer campo del formulario
        pagina.run_task(enfocar, campo_nombre)
    
    def mostrar_form_productos():
        nonlocal fase
        fase = "crear_producto"
        
        # Cambio el titulo del dialogo
        dialog.title = ft.Text("Crear Producto 📦 ", weight="bold")

        # Oculto las opciones y muestro el formulario
        radio_group.visible = False
        form_producto.visible = True

        pagina.update()

        # Enfoco el primer campo del formulario
        pagina.run_task(enfocar, campo_nombre)

    # Enfoco un campo de forma segura con un pequeño delay
    async def enfocar(campo):
        import asyncio
        await asyncio.sleep(0.05)
        await campo.focus()

    # Guardo el cliente en la base de datos
    def guardar_usuario(e=None):

        # Valido que el nombre no este vacio
        if not campo_nombre.value.strip():
            mensaje.value = "El nombre es obligatorio"
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
        else:
            mensaje.value = "Error al guardar el cliente"
            pagina.update()
        
        
    def guardar_producto(e=None):

        # Validar campos vacíos
        if not campo_nombre_producto.value.strip():
            mensaje.value = "El nombre es obligatorio"
            pagina.update()
            return

        if not campo_unidad.value.strip():
            mensaje.value = "La unidad es obligatoria"
            pagina.update()
            return

        if not campo_precio.value.strip():
            mensaje.value = "El precio es obligatorio"
            pagina.update()
            return

        if not campo_stock.value.strip():
            mensaje.value = "El stock es obligatorio"
            pagina.update()
            return
        
        if not campo_empresa.value.strip():
            mensaje.value = "El lugar es obligatorio"

        # Validar números
        try:
            precio = float(campo_precio.value)
        except:
            mensaje.value = "El precio debe ser numérico"
            pagina.update()
            return

        try:
            stock = int(campo_stock.value)
        except:
            mensaje.value = "El stock debe ser un número entero"
            pagina.update()
            return

        # Crear diccionario
        datos = {
            'nombre': campo_nombre_producto.value.strip(),
            'unidad': campo_unidad.value.strip(),
            'lugar': campo_empresa.value.strip(),
            'precio': precio,
            'stock': stock,
        }
        # Llamo al modelo para insertar en la base de datos
        id_nuevo = crear_producto(datos)

        if id_nuevo:
            datos['id_producto'] = id_nuevo

            callback(datos)
            cerrar_dialogo()
        else:
            mensaje.value = "Error al guardar el Producto"
            pagina.update()

    # Boton confirmar: su comportamiento cambia segun la fase
    def confirmar(e=None):

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
        if e.key == "Escape":
            cancelar()
        elif e.key == "Enter":
            confirmar()

    # Reemplazo temporalmente el teclado de vender.py
    async def teclado_pagina(e: ft.KeyboardEvent):
        await teclado(e)

    # -------- DIALOG --------

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