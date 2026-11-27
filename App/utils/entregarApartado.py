import flet as ft
from controllers import ventasController as ventas_controller


# ============================================================================
# ENTREGA DE PEDIDOS WEB EN EL POS (F9)
# ============================================================================
# Ventana con los pedidos web ya pagados (izquierda) y el detalle del pedido
# elegido (derecha). "Entregar e imprimir" guarda la venta con el total de la
# tienda (envío y cupón incluidos), SIN descontar stock (la tienda ya lo hizo),
# marca el pedido como entregado e imprime el ticket.
#
# Dependencias:
#   - controllers.ventasController.obtener_pedidos_por_entrega()
#   - controllers.ventasController.resumen_pedido()
#   - controllers.ventasController.entregar_pedido_web()
# ============================================================================

_NOMBRE_PAGO = {'efectivo': 'Efectivo', 'nequi': 'Nequi'}


def _dinero(valor):
    return f"${float(valor):,.0f}".replace(",", ".")


def entregar_pedido_view(pagina: ft.Page, usuario, al_entregar):
    """
    Crea la ventana de entrega de pedidos web.

    Parámetros:
        pagina (ft.Page): Página de Flet donde se mostrará.
        usuario (dict): Usuario logueado (cajero que entrega).
        al_entregar (callable): Recibe el texto de confirmación cuando un
            pedido se entrega, para notificarlo en vender.py.

    Retorna:
        ft.AlertDialog listo para abrirse.
    """

    pedidos = []
    seleccionado = None
    dialogo_cerrado = False

    # ---------------- CONTROLES ----------------
    campo_buscar = ft.TextField(
        label="Buscar por número o cliente", width=300, dense=True, autofocus=True,
        on_change=lambda e: pintar_lista(),
    )
    lista = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=4, expand=True)
    detalle = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=6, expand=True)
    mensaje = ft.Text("", size=12, color=ft.Colors.RED)
    boton_entregar = ft.Button(
        "Entregar e imprimir", icon=ft.Icons.CHECK, disabled=True,
        bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE,
        on_click=lambda e: entregar(),
    )

    # ---------------- FUNCIONES ----------------
    def cargar():
        pedidos.clear()
        pedidos.extend(ventas_controller.obtener_pedidos_por_entrega())
        pintar_lista()
        pintar_detalle()

    def coincide(p, texto):
        texto = texto.strip().lower().lstrip('#')
        return not texto or texto in str(p['id_pedido']) or texto in str(p.get('nombre_cliente') or '').lower()

    def pintar_lista():
        lista.controls.clear()
        visibles = [p for p in pedidos if coincide(p, campo_buscar.value or "")]
        if not pedidos:
            lista.controls.append(ft.Text("No hay pedidos web pagados por entregar."))
        elif not visibles:
            lista.controls.append(ft.Text("Ningún pedido coincide con la búsqueda."))
        for p in visibles:
            total = ventas_controller.resumen_pedido(p)['total']
            es_actual = seleccionado is not None and seleccionado['id_pedido'] == p['id_pedido']
            lista.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Text(f"#{p['id_pedido']}", weight="bold", width=50),
                        ft.Text(p.get('nombre_cliente') or 'Cliente', expand=True, no_wrap=True),
                        ft.Text(_dinero(total), weight="bold"),
                    ]),
                    padding=8,
                    border_radius=5,
                    bgcolor=ft.Colors.BLUE_100 if es_actual else ft.Colors.WHITE,
                    border=ft.Border.all(1, ft.Colors.BLACK_12),
                    on_click=lambda e, p=p: elegir(p),
                )
            )
        pagina.update()

    def elegir(p):
        nonlocal seleccionado
        seleccionado = p
        mensaje.value = ""
        pintar_lista()
        pintar_detalle()

    def fila(izquierda, derecha, negrita=False):
        peso = "bold" if negrita else None
        return ft.Row([ft.Text(izquierda, expand=True, weight=peso), ft.Text(derecha, weight=peso)])

    def pintar_detalle():
        detalle.controls.clear()
        boton_entregar.disabled = seleccionado is None
        if seleccionado is None:
            detalle.controls.append(ft.Text("Elige un pedido de la lista.", color=ft.Colors.GREY))
            pagina.update()
            return

        p = seleccionado
        r = ventas_controller.resumen_pedido(p)
        primera = p['lineas'][0] if p['lineas'] else {}
        entrega = 'Domicilio' if (p.get('entrega') or primera.get('entrega')) == 'domicilio' else 'Recoge en tienda'
        if entrega == 'Domicilio' and primera.get('direccion_entrega'):
            entrega += f" - {primera['direccion_entrega']}"
            if primera.get('telefono_entrega'):
                entrega += f" - Tel. {primera['telefono_entrega']}"
        pago = _NOMBRE_PAGO.get(str(p.get('metodo_pago') or '').lower(), p.get('metodo_pago') or '-')

        detalle.controls.extend([
            ft.Text(f"Pedido #{p['id_pedido']} - {p.get('nombre_cliente') or 'Cliente'}", size=16, weight="bold"),
            ft.Text(entrega, size=12),
            ft.Text(f"Pagado con: {pago}", size=12),
            ft.Divider(),
        ])
        for l in r['lineas']:
            detalle.controls.append(fila(f"{l['texto_cantidad']}  {l['nombre']}", _dinero(l['subtotal'])))
        detalle.controls.append(ft.Divider())
        if r['envio']:
            detalle.controls.append(fila("Envío", f"+{_dinero(r['envio'])}"))
        if r['descuento']:
            detalle.controls.append(fila(f"Cupón {p.get('codigo_cupon') or ''}".strip(), f"-{_dinero(r['descuento'])}"))
        detalle.controls.append(fila("TOTAL", _dinero(r['total']), negrita=True))
        pagina.update()

    def entregar():
        nonlocal seleccionado
        if seleccionado is None:
            return
        boton_entregar.disabled = True
        pagina.update()
        id_pedido = seleccionado['id_pedido']
        try:
            vistas = [l['id_apartado'] for l in seleccionado['lineas'] if l['estado'] == 'confirmado']
            resultado = ventas_controller.entregar_pedido_web(id_pedido, usuario, vistas)
        except ValueError as err:
            # Alguien cambió el pedido en la web: se muestra el motivo y se recarga.
            mensaje.value = str(err)
            seleccionado = None
            cargar()
            return
        except Exception as err:
            mensaje.value = f"No se pudo entregar el pedido: {err}"
            boton_entregar.disabled = False
            pagina.update()
            return

        texto = f"Pedido web #{id_pedido} entregado (venta #{resultado['id_venta']})."
        if not resultado['impreso']:
            texto += " No se pudo imprimir: reimprímelo desde Consultar (F6/F7)."
        cerrar_dialogo()
        al_entregar(texto)

    def cerrar_dialogo(e=None):
        nonlocal dialogo_cerrado
        if dialogo_cerrado:
            return
        dialogo_cerrado = True
        dialog.open = False
        # Devuelvo el teclado a la vista que estaba antes
        if pagina.on_keyboard_event == teclado:
            pagina.on_keyboard_event = teclado_anterior
        pagina.update()

    async def teclado(e: ft.KeyboardEvent):
        if e.key == "Escape":
            cerrar_dialogo()

    teclado_anterior = pagina.on_keyboard_event

    # ---------------- DIALOG ----------------
    dialog = ft.AlertDialog(
        title=ft.Text("Pedidos web por entregar (F9)"),
        content=ft.Row(
            [
                ft.Column([campo_buscar, lista], width=330),
                ft.VerticalDivider(),
                ft.Column([detalle, mensaje, ft.Row([boton_entregar], alignment=ft.MainAxisAlignment.END)],
                          width=420),
            ],
            width=780,
            height=480,
            vertical_alignment=ft.CrossAxisAlignment.START,
        ),
        actions=[ft.TextButton("Cerrar", on_click=cerrar_dialogo)],
        on_dismiss=cerrar_dialogo,
    )

    pagina.on_keyboard_event = teclado
    cargar()
    return dialog
