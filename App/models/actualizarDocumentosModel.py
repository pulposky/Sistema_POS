"""Persistencia transaccional para la edición de documentos comerciales."""
from database.bd import conectar


CONFIGURACION = {
    "VENTA": {
        "cabecera": "venta", "id": "id_venta", "detalle": "detalle_venta",
        "detalle_id": "id_detalle", "columna_doc": "id_venta", "movimiento": -1,
    },
    "COMPRA": {
        "cabecera": "compras", "id": "id_compra", "detalle": "detalle_compras",
        "detalle_id": "id_detalle", "columna_doc": "id_compra", "movimiento": 1,
    },
    "REMISION": {
        "cabecera": "remision", "id": "id_remision", "detalle": "detalle_remision",
        "detalle_id": "id_detalle_remision", "columna_doc": "id_remision", "movimiento": -1,
    },
}


def actualizar_documento(tipo, numero, cabecera, detalles):
    """Reemplaza cabecera y detalle, conservando el inventario consistente."""
    tipo = (tipo or "").upper()
    config = CONFIGURACION.get(tipo)
    if not config:
        return False, "Tipo de documento no válido."
    if not detalles:
        return False, "Agregue al menos un producto."

    try:
        numero = int(numero)
        detalles_normalizados = []
        for detalle in detalles:
            producto = int(detalle["id"])
            cantidad = float(detalle["cantidad"])
            precio = float(detalle.get("precio", 0) or 0)
            if cantidad <= 0 or precio < 0:
                return False, "Las cantidades deben ser mayores que cero y los precios no pueden ser negativos."
            detalles_normalizados.append({
                "id": producto, "cantidad": cantidad, "precio": precio,
                "subtotal": cantidad * precio,
            })
    except (KeyError, TypeError, ValueError):
        return False, "Hay datos de producto, cantidad o precio inválidos."

    conexion = conectar()
    if conexion is None:
        return False, "No fue posible conectar con la base de datos."
    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute(
            f"SELECT estado FROM {config['cabecera']} WHERE {config['id']} = %s FOR UPDATE",
            (numero,),
        )
        documento = cursor.fetchone()
        if not documento:
            raise ValueError("El documento no existe.")
        if documento.get("estado") != "ACTIVA":
            raise ValueError("Solo se pueden actualizar documentos activos.")

        cursor.execute(
            f"SELECT id_producto, cantidad FROM {config['detalle']} "
            f"WHERE {config['columna_doc']} = %s",
            (numero,),
        )
        anteriores = cursor.fetchall()

        # Se revierte el movimiento previo antes de comprobar y aplicar el nuevo.
        for detalle in anteriores:
            ajuste = -config["movimiento"] * float(detalle["cantidad"])
            cursor.execute(
                "UPDATE producto SET stock = stock + %s WHERE id_producto = %s",
                (ajuste, detalle["id_producto"]),
            )

        cantidades_nuevas = {}
        for detalle in detalles_normalizados:
            cantidades_nuevas[detalle["id"]] = cantidades_nuevas.get(detalle["id"], 0) + detalle["cantidad"]

        if config["movimiento"] < 0:
            for id_producto, cantidad in cantidades_nuevas.items():
                cursor.execute(
                    "SELECT stock FROM producto WHERE id_producto = %s FOR UPDATE",
                    (id_producto,),
                )
                producto = cursor.fetchone()
                if not producto:
                    raise ValueError(f"El producto con ID {id_producto} ya no existe.")
                if float(producto["stock"] or 0) < cantidad:
                    raise ValueError(f"Stock insuficiente para el producto ID {id_producto}.")

        total = sum(d["subtotal"] for d in detalles_normalizados)
        if tipo == "VENTA":
            cursor.execute(
                "UPDATE venta SET fecha=%s, total=%s, metodo_pago=%s, id_cliente=%s, "
                "dinero_recibido=%s, cambio=%s, notas=%s WHERE id_venta=%s",
                (cabecera["fecha"], total, cabecera["metodo_pago"], cabecera["id_tercero"],
                 cabecera.get("dinero_recibido", 0), cabecera.get("cambio", 0),
                 cabecera.get("notas", ""), numero),
            )
        elif tipo == "COMPRA":
            cursor.execute(
                "UPDATE compras SET fecha=%s, total=%s, id_proveedor=%s WHERE id_compra=%s",
                (cabecera["fecha"], total, cabecera["id_tercero"], numero),
            )
        else:
            cursor.execute(
                "UPDATE remision SET fecha=%s, tipo_remision=%s, id_cliente=%s, notas=%s "
                "WHERE id_remision=%s",
                (cabecera["fecha"], cabecera["tipo_remision"], cabecera["id_tercero"],
                 cabecera.get("notas", ""), numero),
            )

        cursor.execute(
            f"DELETE FROM {config['detalle']} WHERE {config['columna_doc']} = %s", (numero,)
        )
        for detalle in detalles_normalizados:
            if tipo == "REMISION":
                cursor.execute(
                    "INSERT INTO detalle_remision (id_remision, id_producto, cantidad) VALUES (%s, %s, %s)",
                    (numero, detalle["id"], detalle["cantidad"]),
                )
            else:
                cursor.execute(
                    f"INSERT INTO {config['detalle']} ({config['columna_doc']}, id_producto, cantidad, "
                    "precio_unitario, subtotal) VALUES (%s, %s, %s, %s, %s)",
                    (numero, detalle["id"], detalle["cantidad"], detalle["precio"], detalle["subtotal"]),
                )

        for id_producto, cantidad in cantidades_nuevas.items():
            cursor.execute(
                "UPDATE producto SET stock = stock + %s WHERE id_producto = %s",
                (config["movimiento"] * cantidad, id_producto),
            )

        conexion.commit()
        return True, "Documento actualizado correctamente."
    except Exception as error:
        conexion.rollback()
        return False, str(error)
    finally:
        cursor.close()
        conexion.close()
