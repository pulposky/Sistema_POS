from views.inicio import inicio_view
from views.login import login_view
from views.menu import menu_view
from views.vender import vender
from views.remision import remision
from views.comprar import compras_view
from views.inventario import inventario
from views.consultarFacturas import consultarFacturas
from views.crearUsuario import nuevoUsuario

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
            ir_a_nuevo_usuario
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

    def ir_a_consultar_facturas(usuario):
        consultarFacturas(
            pagina,
            ir_a_inicio,
            ir_a_menu,
            usuario
        )

    def ir_a_nuevo_usuario(usuario):
        nuevoUsuario(
            pagina,
            ir_a_inicio,
            ir_a_menu,
            usuario
        )
    # Primera vista
    return ir_a_inicio
