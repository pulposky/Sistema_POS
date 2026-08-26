"""
Vista para crear nuevos usuarios del sistema POS.

Muestra un formulario con campos de nombre, usuario, contraseña y rol.
La contraseña se deshabilita automáticamente cuando el rol es "Aprendiz" o
"Consultas", asignándole el valor por defecto "APRENDIZ". Solo los usuarios
con rol Admin o Administrador pueden acceder a esta vista (el acceso se
controla desde el menú principal).

El usuario creador se obtiene del parámetro 'usuario' que se pasa desde el menú.

Navegación:
    ir_a_menu(usuario) -> Vuelve al menú principal tras guardar o cancelar.
"""

import flet as ft
from controllers import usuarioController
from utils.notificaciones import mostrar_notificacion
# Vista para crear usuarios desde la interfaz del sistema.

def nuevoUsuario(pagina, ir_a_inicio, ir_a_menu, usuario):
    """
    Renderiza el formulario de creación de usuarios.

    Parámetros:
        pagina      -> Instancia de la página Flet.
        ir_a_inicio -> Callback para navegar a la pantalla de bienvenida (no usado aquí).
        ir_a_menu   -> Callback para volver al menú principal.
        usuario     -> Diccionario del usuario logueado actualmente.
    """
    # Limpio la pantalla
    pagina.clean()

    # ---------------- FUNCIONES ----------------

    def guardar(e):
        """
        Valida los campos y guarda el nuevo usuario en la base de datos.
        Si la validación falla o hay un error, muestra una notificación de error.
        Al guardar exitosamente, muestra confirmación y vuelve al menú.
        """
        # Verifico que ningún campo obligatorio esté vacío
        if not nombre.value.strip() or not usuario_field.value.strip() or not password.value.strip():
            mostrar_notificacion(pagina, "Completa todos los campos obligatorios.", error=True)
            return

        try:
            # Llamo al controller para persistir el usuario
            id_usuario = usuarioController.guardar_usuario(
                nombre.value.strip(), usuario_field.value.strip(), password.value, rol.value
            )
            mostrar_notificacion(pagina, f"Usuario #{id_usuario} creado correctamente.")
            # Vuelvo al menú principal pasando los datos del usuario logueado
            ir_a_menu(usuario)
        except Exception as error:
            print(f"Error al crear usuario: {error}")
            mostrar_notificacion(pagina, "No fue posible crear el usuario.", error=True)

    def cancelar(e):
        """Cancela la creación y vuelve al menú sin guardar cambios."""
        ir_a_menu(usuario)  # Regresar al menú sin guardar

    # ---------------- CAMPOS DE TEXTO ----------------

    # Campo de nombre completo del nuevo usuario
    nombre = ft.TextField(label="Nombre", width=300)

    # Campo de nombre de usuario (login)
    usuario_field = ft.TextField(label="Usuario", width=300)

    # Campo de contraseña: oculta el texto y permite revelarlo con el ícono de ojo
    password = ft.TextField(label="Contraseña", password=True, can_reveal_password=True, width=300)

    def seleccionar_rol(e):
        """
        Callback del dropdown de rol.
        Cuando se selecciona "Aprendiz" o "Consultas", se deshabilita el campo
        de contraseña y se asigna el valor por defecto "APRENDIZ".
        Para "Admin" se habilita el campo para que escriba la contraseña manualmente.
        """
        password.disabled = e.control.value in ["Aprendiz", "Consultas"]
        if password.disabled:
            password.value = "APRENDIZ"
        pagina.update()

    # Dropdown de selección de rol con tres opciones
    rol = ft.Dropdown(
        label="Rol",
        options=[
            ft.dropdown.Option("Admin"),         # Acceso total al sistema
            ft.dropdown.Option("Aprendiz"),       # Rol de aprendiz (sin permisos especiales)
            ft.dropdown.Option("Consultas"),      # Solo puede consultar facturas
        ],
        value="Admin",                           # Valor por defecto
        on_select=seleccionar_rol,               # Se dispara al cambiar la selección
        width=300
    )

    # Estado inicial del campo de contraseña según el rol por defecto
    password.disabled = rol.value in ["Aprendiz", "Consultas"]
    if password.disabled:
        password.value = "APRENDIZ"


    # ---------------- BOTONES ----------------

    # Botón de guardado: llama a la función guardar() al hacer clic
    boton_guardar = ft.ElevatedButton("Guardar ", on_click=guardar)

    # Botón de cancelar: vuelve al menú principal sin guardar
    boton_cancelar = ft.ElevatedButton("Cancelar ", on_click=cancelar)

    # ---------------- DISEÑO DE LA PANTALLA ----------------
    # Formulario vertical centrado con todos los campos y botones de acción
    # Los botones se colocan en una Row centrada para que aparezcan lado a lado
    pagina.add(
        ft.Column(
            [
                ft.Text("Crear Nuevo Usuario", style=ft.TextStyle(size=20, weight="bold")),
                nombre,                           # Campo nombre
                usuario_field,                    # Campo usuario
                password,                         # Campo contraseña (deshabilitado para Aprendiz/Consultas)
                rol,                              # Selector de rol
                ft.Row([boton_guardar, boton_cancelar], alignment=ft.MainAxisAlignment.CENTER),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
        )
    )
