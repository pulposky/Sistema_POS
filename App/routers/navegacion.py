"""
Módulo central de navegación del sistema POS.

Define todas las rutas (pantallas) disponibles en la aplicación y
las funciones de redirección entre ellas. Cada función `ir_a_*`
es un wrapper que llama a la vista correspondiente pasándole los
callbacks necesarios para que cada pantalla pueda navegar a las
demás (volver al inicio, ir al menú, etc.).

Este patrón evita acoplamiento directo entre vistas: ninguna vista
importa a otra, simplemente recibe funciones de navegación como
parámetros. Esto facilita mantener y reorganizar el flujo de la app.

La función principal `configurar_rutas` retorna:
  - Un diccionario `rutas` con las funciones de navegación indexadas
    por nombre, para poder invocarlas desde cualquier parte del sistema
    (por ejemplo, desde main.py al abrir ventanas secundarias).
  - La función `ir_a_inicio` como ruta por defecto.
"""

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
    """
    Crea y retorna todas las rutas de navegación de la aplicación.

    Cada función interna (`ir_a_*`) actúa como un intermediario
    que recibe los callbacks de navegación que la vista necesita y se
    los pasa. Así, cada vista sabe a dónde puede ir pero no conoce
    las demás vistas directamente.

    Parámetros:
        pagina (ft.Page): La ventana principal de Flet. Se pasa a cada
                          vista para que pueda manipular el contenido
                          de la página.

    Retorna:
        tuple: Una tupla con:
            - dict: Diccionario `{nombre_ruta: función}` que mapea
                    nombres de ruta a funciones de navegación.
            - callable: La función `ir_a_inicio` como ruta por defecto.
    """

    # -------- INICIO --------
    def ir_a_inicio():
        """
        Navega a la pantalla de inicio (splash / bienvenida).
        No requiere datos de usuario ya que es la primera pantalla
        que se muestra al abrir la aplicación.
        """
        inicio_view(
            pagina,
            ir_a_login  # Desde inicio solo se puede ir al login
        )

    # -------- LOGIN --------
    def ir_a_login():
        """
        Navega a la pantalla de login.
        Recibe callbacks para volver al inicio (si el usuario cancela)
        o ir al menú principal (cuando el login es exitoso).
        """
        login_view(
            pagina,
            ir_a_inicio,  # Volver al inicio (botón atrás / cerrar sesión)
            ir_a_menu     # Ir al menú tras autenticarse correctamente
        )

    # -------- MENU --------
    def ir_a_menu(usuario):
        """
        Navega al menú principal del sistema.
        Es la pantalla central desde donde el usuario accede a todas
        las funcionalidades del POS.

        Parámetros:
            usuario (dict): Objeto con los datos del usuario logueado
                            (id, nombre, rol, etc.). Se usa para
                            personalizar el menú según permisos y
                            para pasar a las vistas que lo necesiten.
        """
        menu_view(
            pagina,
            ir_a_login,              # Cerrar sesión
            ir_a_vender,             # Ir a módulo de ventas
            ir_a_remision,           # Ir a módulo de remisiones
            usuario,                 # Datos del usuario logueado
            ir_a_compras,            # Ir a módulo de compras
            ir_a_inventario,         # Ir a módulo de inventario
            ir_a_consultar_facturas, # Ir a consulta de facturas
            ir_a_nuevo_usuario,      # Ir a creación de usuarios
            ir_a_entradas,           # Ir a módulo de entradas
            ir_a_actualizar_facturas # Ir a actualización de facturas
        )

    # -------- VENDER --------
    def ir_a_vender(usuario):
        """
        Navega a la pantalla de ventas (facturación).
        Permite al usuario registrar nuevas ventas y generar facturas.

        Parámetros:
            usuario (dict): Datos del usuario que está realizando la venta.
        """
        vender(
            pagina,
            ir_a_inicio,  # Volver al inicio
            ir_a_menu,    # Volver al menú principal
            usuario       # Usuario logueado
        )

    # -------- REMISION --------
    def ir_a_remision(usuario):
        """
        Navega a la pantalla de remisiones.
        Las remisiones son documentos que acompañan la entrega
        de mercancía sin implicar una transacción de venta directa.

        Parámetros:
            usuario (dict): Datos del usuario que genera la remisión.
        """
        remision(
            pagina,
            ir_a_inicio,  # Volver al inicio
            ir_a_menu,    # Volver al menú principal
            usuario       # Usuario logueado
        )

    def ir_a_compras(usuario):
        """
        Navega a la pantalla de compras.
        Permite registrar las compras de mercancía al proveedor,
        actualizando el inventario y generando los registros
        correspondientes.

        Parámetros:
            usuario (dict): Datos del usuario que registra la compra.
        """
        compras_view(
            pagina,
            ir_a_inicio,  # Volver al inicio
            ir_a_menu,    # Volver al menú principal
            usuario       # Usuario logueado
        )

    def ir_a_inventario(usuario):
        """
        Navega a la pantalla de inventario.
        Muestra el estado actual del stock de productos, permite
        consultar existencias y realizar ajustes.

        Parámetros:
            usuario (dict): Datos del usuario que consulta el inventario.
        """
        inventario(
            pagina,
            ir_a_inicio,  # Volver al inicio
            ir_a_menu,    # Volver al menú principal
            usuario       # Usuario logueado
        )

    def ir_a_entradas(usuario):
        """
        Navega a la pantalla de entradas.
        Registra las entradas de mercancía al almacén, ya sea por
        compras, devoluciones u otros movimientos.

        Parámetros:
            usuario (dict): Datos del usuario que registra la entrada.
        """
        entradas_view(pagina, ir_a_inicio, ir_a_menu, usuario)

    def ir_a_consultar_facturas(usuario):
        """
        Navega a la pantalla de consulta de facturas.
        Permite buscar, filtrar y revisar facturas emitidas
        anteriormente en el sistema.

        Parámetros:
            usuario (dict): Datos del usuario que realiza la consulta.
        """
        consultarFacturas(
            pagina,
            ir_a_inicio,  # Volver al inicio
            ir_a_menu,    # Volver al menú principal
            usuario       # Usuario logueado
        )

    def ir_a_actualizar_facturas(usuario):
        """
        Navega a la pantalla de actualización de facturas.
        Permite modificar facturas existentes (corregir errores,
        agregar ítems, anular, etc.).

        Parámetros:
            usuario (dict): Datos del usuario que realiza la actualización.

        Nota: Esta vista solo recibe ir_a_menu como ruta de retorno,
        no ir_a_inicio, ya que se espera que el usuario siempre
        regrese al menú después de actualizar.
        """
        actualizar_facturas_view(pagina, ir_a_menu, usuario)

    def ir_a_nuevo_usuario(usuario):
        """
        Navega a la pantalla de creación de usuarios.
        Permite registrar nuevos usuarios en el sistema con su
        nombre, contraseña y rol/permisos.

        Parámetros:
            usuario (dict): Datos del usuario administrador que está
                            creando el nuevo usuario.
        """
        nuevoUsuario(
            pagina,
            ir_a_inicio,  # Volver al inicio
            ir_a_menu,    # Volver al menú principal
            usuario       # Usuario administrador logueado
        )

    # Diccionario con las rutas principales para poder abrirlas desde otras partes del sistema
    # Este diccionario se usa principalmente desde main.py cuando se abre
    # una ventana secundaria con una vista específica (POS_VIEW).
    # Las claves deben coincidir con los valores que maneja main.py.
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
