import flet as ft

# ============================================================================
# MÓDULO DE RENDERIZADO DE TABLA DE DOCUMENTOS
# ============================================================================
# Contiene la función para pintar las filas de una DataTable con
# documentos (facturas, compras, remisiones) en la vista de consultas
# del sistema POS.
#
# La DataTable debe tener las columnas definidas previamente en la vista
# que la contiene (tipo, número, fecha, tercero, usuario, total, productos).
# ============================================================================


def pintar_documentos(tabla_documentos, cantidad_documentos, documentos):
    """
    Pinta los documentos en la tabla de consulta de la vista.

    Limpia todas las filas existentes y las rellena con los documentos
    proporcionados. También actualiza el contador de documentos encontrados.

    Parámetros:
        tabla_documentos (ft.DataTable): Componente DataTable de Flet donde
            se renderizarán las filas.
        cantidad_documentos (ft.Text): Componente de texto que muestra la
            cantidad de documentos encontrados.
        documentos (list[dict]): Lista de documentos a mostrar. Cada
            documento es un diccionario con las claves:
            - tipo (str): Tipo de documento (Factura, Compra, Remisión).
            - numero (int): Número/ID del documento.
            - fecha (datetime): Fecha del documento.
            - tercero (str): Nombre del cliente o proveedor.
            - usuario (str): Nombre del usuario que creó el documento.
            - total (float): Monto total del documento.
            - productos (str, optional): Productos incluidos.
    """
    # Limpio las filas anteriores
    tabla_documentos.rows.clear()

    # Actualizo el contador de documentos
    cantidad_documentos.value = f"Documentos encontrados: {len(documentos)}"

    # Creo una fila por cada documento
    for doc in documentos:
        tabla_documentos.rows.append(
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(doc["tipo"])),
                    ft.DataCell(ft.Text(str(doc["numero"]))),
                    ft.DataCell(
                        ft.Text(
                            doc["fecha"].strftime("%d/%m/%Y %H:%M")
                        )
                    ),
                    ft.DataCell(ft.Text(str(doc["tercero"] or "-"))),
                    ft.DataCell(ft.Text(str(doc["usuario"] or "-"))),
                    ft.DataCell(ft.Text(f"${float(doc['total']):,.0f}")),
                    ft.DataCell(ft.Text(str(doc.get("productos", "-")))),
                    ft.DataCell(ft.Text(str(doc.get("notas", "-")))),
                ]
            )
        )
