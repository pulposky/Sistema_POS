"""
Persistencia transaccional para la edición de documentos comerciales.
Este módulo permite actualizar documentos existentes (ventas, compras
y remisiones) manteniendo la consistencia del inventario.

El proceso de actualización sigue estos pasos:
1. Valida que el documento exista y esté activo
2. Revierte el movimiento de stock anterior (deshace el stock previo)
3. Elimina los detalles antiguos
4. Inserta los nuevos detalles
5. Aplica el nuevo movimiento de stock
6. Actualiza la cabecera del documento

Todo se ejecuta en una transacción atómica: si cualquier paso falla,
se revierten todos los cambios anteriores.
"""

# Importa la función de conexión a la base de datos MySQL
from database.bd import conectar


# Diccionario de configuración que define los parámetros de cada tipo
# de documento. Permite reutilizar la misma lógica para ventas, compras
# y remisiones simplemente cambiando los nombres de tablas y columnas.
#
# Cada entrada contiene:
#   cabecera:      Nombre de la tabla de cabecera del documento
#   id:            Nombre de la columna ID en la tabla de cabecera
#   detalle:       Nombre de la tabla de detalles del documento
#   detalle_id:    Nombre de la columna ID en la tabla de detalles
#   columna_doc:   Nombre de la columna que vincula el detalle con la cabecera
#   movimiento:    Factor de stock: -1 para salidas (ventas, remisiones)
#                  y +1 para entradas (compras). Se usa para calcular
#                  el ajuste de stock al reverter y aplicar movimientos
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
    """Reemplaza cabecera y detalle, conservando el inventario consistente.

    Esta función implementa la edición completa de un documento comercial.
    El proceso es:
      1. Validar el tipo de documento y los datos de entrada
      2. Obtener el documento actual con bloqueo FOR UPDATE (prevenir ediciones concurrentes)
      3. Revertir el stock anterior (deshacer el movimiento previo)
      4. Verificar stock suficiente para documentos de salida
      5. Actualizar la cabecera del documento
      6. Eliminar los detalles antiguos
      7. Insertar los nuevos detalles
      8. Aplicar el nuevo movimiento de stock
      9. Confirmar la transacción

    Parámetros:
        tipo (str): Tipo de documento: 'VENTA', 'COMPRA' o 'REMISION'.
        numero (int): ID del documento a actualizar.
        cabecera (dict): Datos nuevos de la cabecera del documento.
            Claves según tipo:
            - VENTA: fecha, metodo_pago, id_tercero, dinero_recibido, cambio, notas
            - COMPRA: fecha, id_tercero
            - REMISION: fecha, tipo_remision, id_tercero, notas
        detalles (list[dict]): Lista de productos nuevos.
            Cada dict debe tener: id (producto), cantidad, precio.

    Retorna:
        tuple (bool, str): Tupla con:
            - True/False indicando éxito o fallo
            - Mensaje descriptivo del resultado o error
    """

    # Normaliza el tipo a mayúsculas para aceptar variantes como 'venta'
    tipo = (tipo or "").upper()

    # Busca la configuración del tipo de documento en el diccionario
    # Si el tipo no es válido (no existe en CONFIGURACION), retorna error
    config = CONFIGURACION.get(tipo)
    if not config:
        return False, "Tipo de documento no válido."

    # Valida que se proporcionen al menos un producto en los detalles
    if not detalles:
        return False, "Agregue al menos un producto."

    try:
        # Convierte el número de documento a entero
        numero = int(numero)

        # Lista para almacenar los detalles normalizados con valores validados
        detalles_normalizados = []

        # Itera sobre cada detalle para validar y normalizar sus datos
        for detalle in detalles:
            # Extrae y valida el ID del producto
            producto = int(detalle["id"])

            # Extrae y valida la cantidad
            cantidad = float(detalle["cantidad"])

            # Extrae el precio, default 0 si es None o no existe
            precio = float(detalle.get("precio", 0) or 0)

            # Valida que la cantidad sea positiva y el precio no sea negativo
            if cantidad <= 0 or precio < 0:
                return False, "Las cantidades deben ser mayores que cero y los precios no pueden ser negativos."

            # Agrega el detalle normalizado con subtotal calculado
            detalles_normalizados.append({
                "id": producto, "cantidad": cantidad, "precio": precio,
                "subtotal": cantidad * precio,
            })
    except (KeyError, TypeError, ValueError):
        # Captura errores de acceso a claves, tipos inválidos o conversión
        return False, "Hay datos de producto, cantidad o precio inválidos."

    # Conecta a la base de datos
    conexion = conectar()

    # Si la conexión falla, retorna error
    if conexion is None:
        return False, "No fue posible conectar con la base de datos."

    # Cursor diccionario para acceder a columnas por nombre
    cursor = conexion.cursor(dictionary=True)

    try:
        # PASO 1: Verificar que el documento exista y esté activo
        # Se usa FOR UPDATE para bloquear la fila y prevenir ediciones
        # concurrentes (que otro usuario edite el mismo documento a la vez)
        cursor.execute(
            f"SELECT estado FROM {config['cabecera']} WHERE {config['id']} = %s FOR UPDATE",
            (numero,),
        )

        # Obtiene el documento o None si no existe
        documento = cursor.fetchone()

        # Si el documento no existe, lanza excepción
        if not documento:
            raise ValueError("El documento no existe.")

        # Si el documento no está activo (está anulado), no se puede editar
        if documento.get("estado") != "ACTIVA":
            raise ValueError("Solo se pueden actualizar documentos activos.")

        # PASO 2: Obtener los detalles actuales del documento
        # Se necesitan para revertir el movimiento de stock anterior
        cursor.execute(
            f"SELECT id_producto, cantidad FROM {config['detalle']} "
            f"WHERE {config['columna_doc']} = %s",
            (numero,),
        )

        # Lista de detalles anteriores
        anteriores = cursor.fetchall()

        # PASO 3: Revertir el movimiento previo antes de comprobar y aplicar el nuevo.
        # Para salidas (ventas, remisiones, movimiento=-1) se SUMA stock
        # Para entradas (compras, movimiento=1) se RESTA stock
        # Se usa -config["movimiento"] para invertir el signo del movimiento original
        for detalle in anteriores:
            # Calcula el ajuste: invierte el signo del movimiento y multiplica por cantidad
            ajuste = -config["movimiento"] * float(detalle["cantidad"])

            # Aplica el ajuste de stock (revertir el movimiento anterior)
            cursor.execute(
                "UPDATE producto SET stock = stock + %s WHERE id_producto = %s",
                (ajuste, detalle["id_producto"]),
            )

        # PASO 4: Agrupar cantidades nuevas por producto
        # Si un producto aparece varias veces en los detalles, suma sus cantidades
        cantidades_nuevas = {}
        for detalle in detalles_normalizados:
            cantidades_nuevas[detalle["id"]] = cantidades_nuevas.get(detalle["id"], 0) + detalle["cantidad"]

        # PASO 5: Verificar stock suficiente para documentos de salida
        # Solo se verifica para ventas (-1) y remisiones (-1), no para compras (+1)
        if config["movimiento"] < 0:
            for id_producto, cantidad in cantidades_nuevas.items():
                # Bloquea la fila del producto con FOR UPDATE para lectura segura
                cursor.execute(
                    "SELECT stock FROM producto WHERE id_producto = %s FOR UPDATE",
                    (id_producto,),
                )
                producto = cursor.fetchone()

                # Si el producto ya no existe, lanza error
                if not producto:
                    raise ValueError(f"El producto con ID {id_producto} ya no existe.")

                # Verifica que haya stock suficiente para cubrir la cantidad solicitada
                if float(producto["stock"] or 0) < cantidad:
                    raise ValueError(f"Stock insuficiente para el producto ID {id_producto}.")

        # PASO 6: Calcular el nuevo total sumando los subtotales de todos los detalles
        total = sum(d["subtotal"] for d in detalles_normalizados)

        # PASO 7: Actualizar la cabecera del documento según su tipo
        # Cada tipo tiene diferentes campos en su cabecera
        if tipo == "VENTA":
            # Actualiza todos los campos de la venta: fecha, total, método de pago,
            # cliente, dinero recibido, cambio y notas
            cursor.execute(
                "UPDATE venta SET fecha=%s, total=%s, metodo_pago=%s, id_cliente=%s, "
                "dinero_recibido=%s, cambio=%s, notas=%s WHERE id_venta=%s",
                (cabecera["fecha"], total, cabecera["metodo_pago"], cabecera["id_tercero"],
                 cabecera.get("dinero_recibido", 0), cabecera.get("cambio", 0),
                 cabecera.get("notas", ""), numero),
            )
        elif tipo == "COMPRA":
            # Actualiza los campos de la compra: fecha, total y proveedor
            cursor.execute(
                "UPDATE compras SET fecha=%s, total=%s, id_proveedor=%s WHERE id_compra=%s",
                (cabecera["fecha"], total, cabecera["id_tercero"], numero),
            )
        else:
            # Actualiza los campos de la remisión: fecha, tipo, cliente y notas
            cursor.execute(
                "UPDATE remision SET fecha=%s, tipo_remision=%s, id_cliente=%s, notas=%s "
                "WHERE id_remision=%s",
                (cabecera["fecha"], cabecera["tipo_remision"], cabecera["id_tercero"],
                 cabecera.get("notas", ""), numero),
            )

        # PASO 8: Eliminar todos los detalles antiguos del documento
        # Se eliminan porque se van a reinsertar con los nuevos datos
        cursor.execute(
            f"DELETE FROM {config['detalle']} WHERE {config['columna_doc']} = %s", (numero,)
        )

        # PASO 9: Insertar los nuevos detalles
        for detalle in detalles_normalizados:
            if tipo == "REMISION":
                # Las remisiones solo tienen: remisión, producto y cantidad
                # No tienen precio unitario ni subtotal
                cursor.execute(
                    "INSERT INTO detalle_remision (id_remision, id_producto, cantidad) VALUES (%s, %s, %s)",
                    (numero, detalle["id"], detalle["cantidad"]),
                )
            else:
                # Ventas y compras tienen: documento, producto, cantidad, precio y subtotal
                cursor.execute(
                    f"INSERT INTO {config['detalle']} ({config['columna_doc']}, id_producto, cantidad, "
                    "precio_unitario, subtotal) VALUES (%s, %s, %s, %s, %s)",
                    (numero, detalle["id"], detalle["cantidad"], detalle["precio"], detalle["subtotal"]),
                )

        # PASO 10: Aplicar el nuevo movimiento de stock
        # Para cada producto, ajusta el stock según la cantidad nueva
        # El factor config["movimiento"] determina si suma (+1) o resta (-1)
        for id_producto, cantidad in cantidades_nuevas.items():
            cursor.execute(
                "UPDATE producto SET stock = stock + %s WHERE id_producto = %s",
                (config["movimiento"] * cantidad, id_producto),
            )

        # Confirma TODA la transacción: verificación + reversión + actualización
        # + eliminación + inserción + ajuste de stock
        conexion.commit()
        return True, "Documento actualizado correctamente."
    except Exception as error:
        # Si ocurre cualquier error, revierte TODA la transacción
        # para mantener la integridad del inventario
        conexion.rollback()
        return False, str(error)
    finally:
        # Bloque finally: se ejecuta SIEMPRE para liberar recursos
        cursor.close()
        conexion.close()
