from database.bd import conectar


def guardar_entrada(entrada_datos, detalles):
    """Guarda la entrada, su detalle y aumenta el stock en una transacción."""
    conexion = conectar()
    if not conexion:
        return None

    cursor = conexion.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO entradas (fecha, observacion, id_usuario, estado)
            VALUES (%s, %s, %s, 'ACTIVA')
            """,
            (
                entrada_datos["fecha"],
                entrada_datos.get("observacion", ""),
                entrada_datos.get("id_usuario", 1),
            ),
        )
        id_entrada = cursor.lastrowid

        for detalle in detalles:
            id_producto = detalle.get("id") or detalle.get("id_producto")
            cantidad = float(detalle.get("cantidad", 0))

            # Una entrada siempre debe sumar una cantidad positiva.
            if not id_producto or cantidad <= 0:
                raise ValueError("Cada producto debe tener una cantidad mayor que cero.")

            cursor.execute(
                """
                INSERT INTO detalle_entradas (id_entrada, id_producto, cantidad)
                VALUES (%s, %s, %s)
                """,
                (id_entrada, id_producto, cantidad),
            )

            # Solo se modifica stock: precio y costo quedan intactos.
            cursor.execute(
                "UPDATE producto SET stock = stock + %s WHERE id_producto = %s",
                (cantidad, id_producto),
            )

        conexion.commit()
        return id_entrada
    except Exception as error:
        conexion.rollback()
        print(f"Error al guardar entrada: {error}")
        return None
    finally:
        cursor.close()
        conexion.close()
