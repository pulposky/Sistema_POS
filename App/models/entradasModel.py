"""
Módulo de entradas de inventario del sistema POS.
Las entradas representan incorporación de mercancía al inventario que
NO proviene de una compra (ej: devoluciones, ajustes de inventario,
donaciones, mercancía de prueba, etc.).

A diferencia de las compras (que también suman stock), las entradas
no están vinculadas a un proveedor ni generan un registro contable
de compra. Solo modifican el stock de los productos.

Este módulo maneja:
  - Guardado de entradas con sus detalles y actualización de stock
"""

# Importa la función de conexión a la base de datos MySQL
from database.bd import conectar


def guardar_entrada(entrada_datos, detalles):
    """Guarda la entrada, su detalle y aumenta el stock en una transacción.

    Realiza tres operaciones en una sola transacción atómica:
    1. Inserta la cabecera de la entrada en la tabla 'entradas'
    2. Inserta cada producto entrante en 'detalle_entradas'
    3. Aumenta el stock de cada producto (suma la cantidad)

    Si cualquier operación falla, se revierten todas las anteriores
    mediante rollback para mantener la integridad del inventario.

    Parámetros:
        entrada_datos (dict): Datos de la cabecera de la entrada.
            Claves requeridas: fecha.
            Claves opcionales: observacion (str), id_usuario (int, default 1).
        detalles (list[dict]): Lista de productos que ingresan.
            Cada dict debe tener: id (o id_producto), cantidad.

    Retorna:
        int o None: El ID de la entrada creada, o None si ocurrió un error
        o si la conexión a la base de datos falló.
    """

    # Conecta a la base de datos
    conexion = conectar()

    # Si la conexión falla, retorna None inmediatamente
    if not conexion:
        return None

    # Crea cursor estándar para operaciones de escritura
    cursor = conexion.cursor()

    # Bloque try/except/finally para manejo seguro de errores y recursos
    try:
        # Consulta SQL para insertar la cabecera de la entrada
        # El estado se establece como 'ACTIVA' directamente en la consulta
        # Campo 'observacion' es opcional, default cadena vacía
        # Campo 'id_usuario' default es 1 (administrador del sistema)
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

        # Obtiene el ID auto-generado de la entrada recién insertada
        id_entrada = cursor.lastrowid

        # Itera sobre cada producto que ingresa al inventario
        for detalle in detalles:
            # Obtiene el ID del producto, aceptando ambas claves posibles
            id_producto = detalle.get("id") or detalle.get("id_producto")

            # Convierte la cantidad a float para manejar unidades fraccionarias
            cantidad = float(detalle.get("cantidad", 0))

            # Una entrada siempre debe sumar una cantidad positiva.
            # Valida que haya un producto válido y que la cantidad sea mayor a cero.
            # Si no se cumple, lanza una excepción que será capturada por el except
            if not id_producto or cantidad <= 0:
                raise ValueError("Cada producto debe tener una cantidad mayor que cero.")

            # Consulta SQL para insertar el detalle de la entrada
            # Solo almacena: entrada padre, producto y cantidad
            # A diferencia de ventas/compras, no se almacena precio
            cursor.execute(
                """
                INSERT INTO detalle_entradas (id_entrada, id_producto, cantidad)
                VALUES (%s, %s, %s)
                """,
                (id_entrada, id_producto, cantidad),
            )

            # Solo se modifica stock: precio y costo quedan intactos.
            # La entrada suma stock porque representa incorporación de mercancía
            # No se modifica el precio porque la entrada no tiene costo asociado
            cursor.execute(
                "UPDATE producto SET stock = stock + %s WHERE id_producto = %s",
                (cantidad, id_producto),
            )

        # Confirma TODA la transacción: entrada + detalles + actualización de stock
        conexion.commit()

        # Retorna el ID de la entrada creada
        return id_entrada
    except Exception as error:
        # Si ocurre cualquier error, revierte TODA la transacción
        conexion.rollback()

        # Imprime el error para depuración
        print(f"Error al guardar entrada: {error}")

        # Retorna None indicando fallo
        return None
    finally:
        # Bloque finally: se ejecuta SIEMPRE, con o sin excepción
        # Garantiza que cursor y conexión se cierren para liberar recursos
        cursor.close()
        conexion.close()
