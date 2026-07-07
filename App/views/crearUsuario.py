import flet as ft
from controllers import usuarioController

def nuevoUsuario(pagina, ir_a_inicio, ir_a_menu, usuario):
    # Limpio la pantalla
    pagina.clean()

    # ---------------- FUNCIONES ----------------
    def guardar(e):
        # Aquí puedes agregar la lógica para guardar el usuario en la base de datos o realizar cualquier acción necesaria.
        print("Usuario guardado:", nombre.value, usuario_field.value, password.value, rol.value)
        usuarioController.guardar_usuario(nombre.value, usuario_field.value, password.value, rol.value)
        ir_a_menu(usuario)  # Regresar al menú después de guardar

    def cancelar(e):
        ir_a_menu(usuario)  # Regresar al menú sin guardar

    # ---------------- CAMPOS DE TEXTO ----------------
    nombre = ft.TextField(label="Nombre", width=300)
    usuario_field = ft.TextField(label="Usuario", width=300)
    password = ft.TextField(label="Contraseña", password=True, can_reveal_password=True, width=300)

    def seleccionar_rol(e):
        password.disabled = e.control.value in ["Aprendiz", "Consultas"]
        if password.disabled:
            password.value = ""
        pagina.update()

    rol = ft.Dropdown(
        label="Rol",
        options=[
            ft.dropdown.Option("Admin"),
            ft.dropdown.Option("Aprendiz"),
            ft.dropdown.Option("Consultas"),
        ],
        value="Admin",
        on_select=seleccionar_rol,
        width=300
    )
    password.disabled = rol.value in ["Aprendiz", "Consultas"]
    if password.disabled:
        password.value = ""


    # ---------------- BOTONES ----------------
    boton_guardar = ft.ElevatedButton("Guardar ", on_click=guardar)
    boton_cancelar = ft.ElevatedButton("Cancelar ", on_click=cancelar)

    # ---------------- DISEÑO DE LA PANTALLA ----------------
    pagina.add(
        ft.Column(
            [
                ft.Text("Crear Nuevo Usuario", style=ft.TextStyle(size=20, weight="bold")),
                nombre,
                usuario_field,
                password,
                rol,
                ft.Row([boton_guardar, boton_cancelar], alignment=ft.MainAxisAlignment.CENTER),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
        )
    )