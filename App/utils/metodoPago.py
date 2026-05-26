

import flet as ft
import traceback


# =========================================================
# PARA RECIBIR METODOS DE PAGOS DIFERENTES
# =========================================================

def metodo_pago_view(pagina: ft.Page, total, callback):

    teclado_anterior = pagina.on_keyboard_event
    dialogo_cerrado = False
    metodo_actual = "Efectivo"

    # ---------------- CAMPOS ----------------

    campo_efectivo = ft.TextField(
        label="Dinero en efectivo",
        width=320,
        value="0"
    )

    campo_transferencia = ft.TextField(
        label="Dinero por transferencia",
        width=320,
        value="0"
    )

    texto_total    = ft.Text(f"Total a pagar: ${total:,.0f}", size=14, weight="bold")
    texto_faltante = ft.Text(f"Faltante: ${total:,.0f}",     size=14, color=ft.Colors.RED)
    texto_cambio   = ft.Text("Cambio: $0",                   size=14, color=ft.Colors.GREEN)

    # Fila de efectivo, visible por defecto
    fila_efectivo = ft.Column(
        [ft.Text("Efectivo:", weight="bold"), campo_efectivo],
        spacing=5,
        visible=True
    )

    # Fila de transferencia, oculta por defecto
    fila_transferencia = ft.Column(
        [ft.Text("Transferencia:", weight="bold"), campo_transferencia],
        spacing=5,
        visible=False
    )

    # Contenedor principal de campos
    campos_pago = ft.Column(
        [
            fila_efectivo,
            fila_transferencia,
            ft.Divider(),
            texto_faltante,
            texto_cambio
        ],
        spacing=10,
        visible=True
    )

    # Mensaje para credito
    texto_credito = ft.Text(
        "✓ La deuda quedará pendiente en el sistema",
        size=13,
        color=ft.Colors.ORANGE,
        visible=False
    )

    # Mensaje para transferencia pura
    texto_transferencia = ft.Text(
        "✓ Pago por transferencia por el total",
        size=13,
        color=ft.Colors.BLUE,
        visible=False
    )

    # ---------------- FUNCIONES ----------------

    def calcular(e=None):
        try:
            efectivo      = float(campo_efectivo.value      or 0)
            transferencia = float(campo_transferencia.value or 0)
            suma          = efectivo + transferencia
            faltante      = total - suma
            cambio        = suma - total

            if faltante > 0:
                texto_faltante.value = f"Faltante: ${faltante:,.0f}"
                texto_faltante.color = ft.Colors.RED
                texto_cambio.value   = "Cambio: $0"
            else:
                texto_faltante.value = "✓ Cubierto"
                texto_faltante.color = ft.Colors.GREEN
                texto_cambio.value   = f"Cambio: ${cambio:,.0f}"
        except:
            pass

        pagina.update()

    def seleccionar_metodo(e):
        nonlocal metodo_actual
        metodo_actual = e.control.value

        # Oculto todo primero
        campos_pago.visible          = False
        texto_credito.visible        = False
        texto_transferencia.visible  = False
        fila_efectivo.visible        = False
        fila_transferencia.visible   = False

        if metodo_actual == "Efectivo":
            campos_pago.visible      = True
            fila_efectivo.visible    = True
            campo_transferencia.value = "0"

        elif metodo_actual == "Transferencia":
            texto_transferencia.visible = True

        elif metodo_actual == "Mixto":
            campos_pago.visible          = True
            fila_efectivo.visible        = True
            fila_transferencia.visible   = True

        elif metodo_actual == "Credito":
            texto_credito.visible = True

        calcular()
        pagina.update()

    def confirmar(e=None):
        # 1. Crédito: no requiere validar montos
        if metodo_actual == "Credito":
            cerrar_dialogo()
            try:
                callback({
                    "metodo_pago":     "Credito",
                    "dinero_recibido": 0,
                    "efectivo":        0,
                    "transferencia":   0,
                    "cambio":          0
                })
            except Exception as err:
                print(f"[metodo_pago] Error en callback Credito: {err}")
                traceback.print_exc()
            return

        # 2. Transferencia pura
        if metodo_actual == "Transferencia":
            cerrar_dialogo()
            try:
                callback({
                    "metodo_pago":     "Transferencia",
                    "dinero_recibido": total,
                    "efectivo":        0,
                    "transferencia":   total,
                    "cambio":          0
                })
            except Exception as err:
                print(f"[metodo_pago] Error en callback Transferencia: {err}")
                traceback.print_exc()
            return

        # 3. Efectivo o Mixto: convierto los montos (aquí sí puede fallar el float)
        try:
            efectivo      = float(campo_efectivo.value      or 0)
            transferencia = float(campo_transferencia.value or 0)
        except ValueError:
            texto_faltante.value = "Valor inválido"
            texto_faltante.color = ft.Colors.RED
            pagina.update()
            return

        suma = efectivo + transferencia

        # 4. Valido que el dinero cubra el total
        if suma < total:
            texto_faltante.value = f"Faltante: ${total - suma:,.0f}"
            texto_faltante.color = ft.Colors.RED
            pagina.update()
            return

        cambio = suma - total

        # 5. Cierro primero el diálogo y luego ejecuto el callback
        # El callback ya NO está dentro del try, así que sus errores
        # se ven en consola en vez de mostrar "Valor inválido"
        cerrar_dialogo()

        try:
            callback({
                "metodo_pago":     "Mixto" if metodo_actual == "Mixto" else "Efectivo",
                "dinero_recibido": suma,
                "efectivo":        efectivo,
                "transferencia":   transferencia,
                "cambio":          cambio
            })
        except Exception as err:
            print(f"[metodo_pago] Error en callback de pago: {err}")
            traceback.print_exc()

    def cerrar_dialogo():
        nonlocal dialogo_cerrado
        if dialogo_cerrado:
            return
        dialogo_cerrado = True
        dialog.open = False
        if pagina.on_keyboard_event == teclado_pagina:
            pagina.on_keyboard_event = teclado_anterior
        pagina.update()

    def cancelar(e=None):
        cerrar_dialogo()

    campo_efectivo.on_change      = calcular
    campo_transferencia.on_change = calcular

    # ---------------- TECLADO ----------------

    async def teclado(e: ft.KeyboardEvent):
        if e.key == "Escape":
            cancelar()
        elif e.key == "Enter":
            confirmar()

    async def teclado_pagina(e: ft.KeyboardEvent):
        await teclado(e)

    # ---------------- DIALOG ----------------

    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Método de pago", weight="bold"),
        content=ft.Container(
            width=380,
            height=560,
            content=ft.Column(
                [
                    texto_total,
                    ft.Divider(),
                    ft.RadioGroup(
                        value="Efectivo",
                        on_change=seleccionar_metodo,
                        content=ft.Column(
                            [
                                ft.Radio(value="Efectivo",      label="💵 Efectivo"),
                                ft.Radio(value="Transferencia", label="🏦 Transferencia"),
                                ft.Radio(value="Mixto",         label="💵🏦 Mixto"),
                                ft.Radio(value="Credito",       label="📄 Crédito"),
                            ],
                            spacing=5
                        )
                    ),
                    campos_pago,
                    texto_credito,
                    texto_transferencia,
                ],
                spacing=10,
                scroll=ft.ScrollMode.AUTO
            )
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

    pagina.on_keyboard_event = teclado_pagina
    return dialog