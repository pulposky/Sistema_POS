# Módulo central de navegación.
# Define las rutas y redirige entre las pantallas del sistema.
from views.inicio import inicio_view
from views.login import login_view
from views.menu import menu_view
from views.vender import vender
from views.remision import remision
from views.comprar import compras_view
from views.inventario import inventario
from views.consultarFacturas import consultarFacturas
from views.crearUsuario import nuevoUsuario
from views.entradas import entradas_view
from views.actualizarFacturas import actualizar_facturas_view

# Función encargada de centralizar las rutas de la aplicación
def configurar_rutas(pagina):
    # -------- INICIO --------
    def ir_a_inicio():
        inicio_view(
            pagina,
            ir_a_login
        )
    # -------- LOGIN --------
    def ir_a_login():
        login_view(
            pagina,
            ir_a_inicio,
            ir_a_menu
        )
    # -------- MENU --------
    def ir_a_menu(usuario):
        menu_view(
            pagina,
            ir_a_login,
            ir_a_vender,
            ir_a_remision,
            usuario,
            ir_a_compras,
            ir_a_inventario,
            ir_a_consultar_facturas,
            ir_a_nuevo_usuario,
            ir_a_entradas,
            ir_a_actualizar_facturas
        )

    # -------- VENDER --------
    def ir_a_vender(usuario):
        vender(
            pagina,
            ir_a_inicio,
            ir_a_menu,
            usuario
        )

    # -------- REMISION --------
    def ir_a_remision(usuario):
        remision(
            pagina,
            ir_a_inicio,
            ir_a_menu,
            usuario
        )

    def ir_a_compras(usuario):
        compras_view(
            pagina,
            ir_a_inicio,
            ir_a_menu,
            usuario
        )

    def ir_a_inventario(usuario):
        inventario(
            pagina,
            ir_a_inicio,
            ir_a_menu,
            usuario
        )

    def ir_a_entradas(usuario):
        entradas_view(pagina, ir_a_inicio, ir_a_menu, usuario)

    def ir_a_consultar_facturas(usuario):
        consultarFacturas(
            pagina,
            ir_a_inicio,
            ir_a_menu,
            usuario
        )

    def ir_a_actualizar_facturas(usuario):
        actualizar_facturas_view(pagina, ir_a_menu, usuario)

    def ir_a_nuevo_usuario(usuario):
        nuevoUsuario(
            pagina,
            ir_a_inicio,
            ir_a_menu,
            usuario
        )

    # Diccionario con las rutas principales para poder abrirlas desde otras partes del sistema
    rutas = {
        "inicio": ir_a_inicio,
        "login": ir_a_login,
        "menu": ir_a_menu,
        "vender": ir_a_vender,
        "remision": ir_a_remision,
        "compras": ir_a_compras,
        "inventario": ir_a_inventario,
        "entradas": ir_a_entradas,
        "consultar_facturas": ir_a_consultar_facturas,
        "actualizar_facturas": ir_a_actualizar_facturas,
        "nuevo_usuario": ir_a_nuevo_usuario,
    }

    return rutas, ir_a_inicio
