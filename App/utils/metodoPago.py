

import flet as ft
import traceback


# ============================================================================
# MÓDULO DE MÉTODO DE PAGO
# ============================================================================
# Diálogo modal que permite al usuario elegir y configurar el método de
# pago de una venta: Transferencia, Efectivo, Mixto o Crédito.
#
# Características:
#   - Calcula en tiempo real el faltante y el cambio según los montos ingresados.
#   - Para Transferencia pura, el monto total se registra automáticamente.
#   - Para Crédito, no se requiere ningún monto (la deuda queda pendiente).
#   - Para Mixto, permite dividir entre efectivo y transferencia.
#   - Muestra un campo de notas por cada empresa con productos en la venta
#     (SenaEmpresa, Campesena, etc.).
#
# Flujo:
#   1. El usuario elige un método de pago con los radio buttons.
#   2. Ingresa los montos correspondientes.
#   3. Presiona Confirmar (o Enter) para enviar el resultado al callback.
#   4. El callback recibe un diccionario con todos los datos del pago.
# ============================================================================


def metodo_pago_view(pagina: ft.Page, total, callback, productos=None):
    """
    Crea el diálogo de selección de método de pago.

    Parámetros:
        pagina (ft.Page): Página de Flet donde se mostrará el diálogo.
        total (float): Monto total de la venta a pagar.
        callback (callable): Función que recibe un diccionario con la
            información del pago al confirmar. El diccionario contiene:
            - metodo_pago (str): "Transferencia", "Efectivo", "Mixto" o "Credito".
            - dinero_recibido (float): Suma de efectivo + transferencia.
            - efectivo (float): Monto en efectivo.
            - transferencia (float): Monto por transferencia.
            - cambio (float): Cambio a devolver (positivo si se dio de más).
            - notas (str): Notas adicionales (banco, comprobante, etc.).
            - notas_empresa (dict): Notas separadas por empresa {"SenaEmpresa": "...", "Campesena": "..."}.
        productos (list[dict], optional): Lista de productos de la venta.
            Se usa para detectar las empresas (campo 'lugar') y mostrar
            un campo de nota por cada empresa presente.

    Retorna:
        ft.AlertDialog: Componente de diálogo listo para mostrarse.
    """
    # Guardo el handler de teclado anterior para restaurarlo al cerrar
    teclado_anterior = pagina.on_keyboard_event
    dialogo_cerrado = False
    metodo_actual = "Transferencia" # Selecciono transferencia por defecto porque es lo más común en ventas grandes

    # ---------------- CAMPOS DE ENTRADA ----------------

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

    # Textos informativos que se actualizan en tiempo real
    texto_total    = ft.Text(f"Total a pagar: ${total:,.0f}", size=14, weight="bold")
    texto_faltante = ft.Text(f"Faltante: ${total:,.0f}",     size=14, color=ft.Colors.RED)
    texto_cambio   = ft.Text("Cambio: $0",                   size=14, color=ft.Colors.GREEN)

    # Fila de efectivo, oculto por defecto (solo se muestra si se elige Efectivo o Mixto)
    fila_efectivo = ft.Column(
        [ft.Text("Efectivo:", weight="bold"), campo_efectivo],
        spacing=5,
        visible=False
    )

    # Fila de transferencia, visible por defecto (transferencia es el método más común)
    fila_transferencia = ft.Column(
        [ft.Text("Transferencia:", weight="bold"), campo_transferencia],
        spacing=5,
        visible=True
    )

    # Contenedor principal que agrupa los campos de pago, faltante y cambio
    campos_pago = ft.Column(
        [
            fila_transferencia,
            fila_efectivo,
            ft.Divider(),
            texto_faltante,
            texto_cambio
        ],
        spacing=10,
        visible=False
    )

    # Mensaje informativo para el pago a crédito
    texto_credito = ft.Text(
        "✓ La deuda quedará pendiente en el sistema",
        size=13,
        color=ft.Colors.ORANGE,
        visible=False
    )

    # -------------------------------------------------------
    # CAMPOS DE NOTAS DINÁMICOS POR EMPRESA
    # -------------------------------------------------------
    # Se detectan las empresas (campo 'lugar') de los productos
    # y se crea un campo de nota por cada una.
    empresas_detectadas = []
    if productos:
        empresas_detectadas = sorted(set(
            str(p.get("lugar", "SenaEmpresa")).strip()
            for p in productos
            if p.get("lugar")
        ))

    # Si no se detectaron empresas, usar "General" como fallback
    if not empresas_detectadas:
        empresas_detectadas = ["General"]

    # Diccionario de campos de nota: {empresa: TextField}
    campos_nota_empresa = {}

    # Lista de controles visuales para los campos de nota
    controles_notas = []
    for empresa in empresas_detectadas:
        campo = ft.TextField(
            label=f"Nota {empresa}",
            hint_text=f"Nota para {empresa} (banco, comprobante, ref.)",
            width=320,
            multiline=True,
            min_lines=1,
            max_lines=3,
            visible=True,
        )
        campos_nota_empresa[empresa] = campo
        controles_notas.append(campo)

    # Mensaje informativo para transferencia pura
    texto_transferencia = ft.Text(
        "✓ Pago por transferencia por el total",
        size=13,
        color=ft.Colors.BLUE,
        visible=True
    )

    # ---------------- FUNCIONES ----------------

    def calcular(e=None):
        """
        Calcula el faltante y el cambio en tiempo real cuando el usuario
        modifica los montos de efectivo o transferencia.
        Se ejecuta cada vez que cambia el contenido de cualquiera de los
        dos campos de monto.
        """
        try:
            efectivo      = float(campo_efectivo.value      or 0)
            transferencia = float(campo_transferencia.value or 0)
            suma          = efectivo + transferencia
            faltante      = total - suma
            cambio        = suma - total

            if faltante > 0:
                # Aún no se cubre el total: muestro el faltante en rojo
                texto_faltante.value = f"Faltante: ${faltante:,.0f}"
                texto_faltante.color = ft.Colors.RED
                texto_cambio.value   = "Cambio: $0"
            else:
                # El pago cubre o supera el total: muestro "Cubierto" en verde
                texto_faltante.value = "✓ Cubierto"
                texto_faltante.color = ft.Colors.GREEN
                texto_cambio.value   = f"Cambio: ${cambio:,.0f}"
        except:
            pass

        pagina.update()

    def seleccionar_metodo(e):
        """
        Maneja el cambio de selección del método de pago.
        Muestra u oculta los campos según el método elegido.

        Parámetros:
            e: Evento del RadioGroup con el valor seleccionado en e.control.value.
        """
        nonlocal metodo_actual
        metodo_actual = e.control.value

        # Oculto todo primero para luego mostrar solo lo necesario
        campos_pago.visible          = False
        texto_credito.visible        = False
        texto_transferencia.visible  = False
        fila_efectivo.visible        = False
        fila_transferencia.visible   = False
        # El campo de notas siempre está visible (se registra la referencia
        # en cualquier método de pago).

        if metodo_actual == "Efectivo":
            # Solo campo de efectivo, reseteo transferencia a 0
            campos_pago.visible      = True
            fila_efectivo.visible    = True
            campo_transferencia.value = "0"

        elif metodo_actual == "Transferencia":
            # Transferencia pura: el monto es el total automáticamente
            texto_transferencia.visible = True
            # En transferencias se registra el banco o comprobante.

        elif metodo_actual == "Mixto":
            # Muestro ambos campos (efectivo y transferencia) y campo de notas
            campos_pago.visible          = True
            fila_efectivo.visible        = True
            fila_transferencia.visible   = True
            # En pago mixto se puede aclarar la referencia de transferencia.

        elif metodo_actual == "Credito":
            # No hay campos de monto, solo muestro el mensaje de crédito
            texto_credito.visible = True

        calcular()
        pagina.update()

    def confirmar(e=None):
        """
        Confirma el pago y ejecuta el callback con los datos.
        Valida que el monto cubra el total (excepto para crédito).
        Cierra el diálogo antes de ejecutar el callback para evitar
        problemas de UI si el callback tarda.
        """
        # Recopilar notas por empresa en un diccionario
        notas_empresa = {}
        for empresa, campo in campos_nota_empresa.items():
            valor = (campo.value or "").strip()
            if valor:
                notas_empresa[empresa] = valor

        # Nota general combinada (para compatibilidad)
        nota_general = " | ".join(
            f"{emp}: {txt}" for emp, txt in notas_empresa.items()
        ) if notas_empresa else ""

        # 1. Crédito: no requiere validar montos
        if metodo_actual == "Credito":
            cerrar_dialogo()
            try:
                callback({
                    "metodo_pago":     "Credito",
                    "dinero_recibido": 0,
                    "efectivo":        0,
                    "transferencia":   0,
                    "cambio":          0,
                    "notas":           nota_general,
                    "notas_empresa":   notas_empresa,
                })
            except Exception as err:
                print(f"[metodo_pago] Error en callback Credito: {err}")
                traceback.print_exc()
            return

        # 2. Transferencia pura: el total se paga completo por transferencia
        if metodo_actual == "Transferencia":
            cerrar_dialogo()
            try:
                callback({
                    "metodo_pago":     "Transferencia",
                    "dinero_recibido": total,
                    "efectivo":        0,
                    "transferencia":   total,
                    "cambio":          0,
                    "notas":           nota_general,
                    "notas_empresa":   notas_empresa,
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
                "cambio":          cambio,
                "notas":           nota_general,
                "notas_empresa":   notas_empresa,
            })
        except Exception as err:
            print(f"[metodo_pago] Error en callback de pago: {err}")
            traceback.print_exc()

    def cerrar_dialogo():
        """Cierra el diálogo y restaura el handler de teclado anterior."""
        nonlocal dialogo_cerrado
        if dialogo_cerrado:
            return
        dialogo_cerrado = True
        dialog.open = False
        if pagina.on_keyboard_event == teclado_pagina:
            pagina.on_keyboard_event = teclado_anterior
        pagina.update()

    def cancelar(e=None):
        """Cancela el pago y cierra el diálogo."""
        cerrar_dialogo()

    # Asigno los callbacks de cambio de texto para calcular en tiempo real
    campo_efectivo.on_change      = calcular
    campo_transferencia.on_change = calcular

    # ---------------- TECLADO ----------------

    async def teclado(e: ft.KeyboardEvent):
        """Maneja las teclas del diálogo: Escape cancela, Enter confirma."""
        if e.key == "Escape":
            cancelar()
        elif e.key == "Enter":
            confirmar()

    async def teclado_pagina(e: ft.KeyboardEvent):
        """Wrapper del handler de teclado para la página."""
        await teclado(e)

    # ---------------- DIALOG ----------------

    # Construyo el diálogo con los radio buttons de método de pago,
    # los campos de monto y los botones de acción
    # Incremento la altura según cuántas empresas tengan campo de nota
    altura_dialogo = 560 + 70 * max(0, len(empresas_detectadas) - 1)
    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Método de pago", weight="bold"),
        content=ft.Container(
            width=380,
            height=altura_dialogo,
            content=ft.Column(
                [
                    texto_total,
                    ft.Divider(),
                    # Radio buttons para elegir el método de pago
                    ft.RadioGroup(
                        value="Transferencia",
                        on_change=seleccionar_metodo,
                        content=ft.Column(
                            [
                                ft.Radio(value="Transferencia", label="🏦 Transferencia"),
                                ft.Radio(value="Efectivo",      label="💵 Efectivo"),
                                ft.Radio(value="Mixto",         label="💵🏦 Mixto"),
                                ft.Radio(value="Credito",       label="📄 Crédito"),
                            ],
                            spacing=5
                        )
                    ),
                    campos_pago,
                    texto_credito,
                    *controles_notas,
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

    # Reemplazo el teclado de la vista actual para manejar Escape/Enter
    pagina.on_keyboard_event = teclado_pagina
    return dialog
