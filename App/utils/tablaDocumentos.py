import flet as ft

# Utilidad para pintar tablas de documentos en la vista de consultas.

def pintar_documentos(tabla_documentos, cantidad_documentos, documentos):
    """Pinta los documentos en la tabla de consulta."""
    tabla_documentos.rows.clear()
    cantidad_documentos.value = f"Documentos encontrados: {len(documentos)}"

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
                    ft.DataCell(ft.Text(str(doc.get("productos", "-"))))
                ]
            )
        )
