"""
Módulo de informes de inventario del sistema POS.
Este archivo genera un informe consolidado del inventario calculando
el stock final de cada producto a partir de sus movimientos (entradas,
compras, ventas y remisiones), en lugar de depender del campo
almacenado 'producto.stock'.

La fórmula de stock es:
  stock_final = entradas + compras - ventas - remisiones

Solo se incluyen productos que tengan al menos una entrada activa,
ya que un producto sin entradas no tiene historial de inventario.
"""

# Importa la función de conexión a la base de datos MySQL
from database.bd import conectar

# Modelo para construir el informe de inventario desde los movimientos.


def obtener_informe_inventario():
    """Retorna un diccionario por producto con sus entradas y salidas.

    El stock se calcula en SQL para que el informe no dependa del valor
    almacenado en ``producto.stock``.

    Esta función ejecuta una consulta SQL compleja que:
    1. Parte de todos los productos (tabla 'producto')
    2. Hace LEFT JOIN con subconsultas que suman las cantidades de:
       - Entradas de inventario (solo entradas con estado 'ACTIVA')
       - Compras (solo compras con estado 'ACTIVA')
       - Ventas (solo ventas con estado 'ACTIVA')
       - Remisiones (solo remisiones con estado 'ACTIVA')
    3. Calcula el stock final con la fórmula: entradas + compras - ventas - remisiones
    4. Filtra solo productos con al menos una entrada activa
    5. Ordena por código de producto

    Retorna:
        list[dict]: Lista de diccionarios, uno por producto, con los campos:
            - id_producto: ID único del producto
            - codigo: Código del producto (ej: LAC001, FRU002)
            - nombre: Nombre descriptivo del producto
            - unidad: Unidad de medida (kg, litro, unidad, etc.)
            - entradas: Cantidad total recibida por entradas de inventario
            - compras: Cantidad total recibida por compras a proveedores
            - ventas: Cantidad total despachada por ventas
            - remisiones: Cantidad total despachada por remisiones
            - stock_final: Stock calculado (entradas + compras - ventas - remisiones)
        Retorna lista vacía si la conexión a la base de datos falla.
    """

    # Conecta a la base de datos
    conexion = conectar()

    # Si la conexión falla, retorna lista vacía
    if not conexion:
        return []

    # Cursor diccionario para acceder a columnas por nombre
    cursor = conexion.cursor(dictionary=True)

    # Bloque try/finally para garantizar cierre de recursos
    try:
        # Consulta SQL compleja con 4 LEFT JOINs y subconsultas
        # Cada LEFT JOIN suma las cantidades de un tipo de movimiento
        # agrupadas por producto. Se usa LEFT JOIN (no INNER) para que
        # los productos sin movimientos en alguna categoría muestren 0
        # gracias a COALESCE (que convierte NULL en 0)
        sql = """
            SELECT
                p.id_producto,
                p.codigo,
                p.nombre,
                p.unidad,
                COALESCE(e.entradas, 0) AS entradas,
                COALESCE(c.compras, 0) AS compras,
                COALESCE(v.ventas, 0) AS ventas,
                COALESCE(r.remisiones, 0) AS remisiones,
                COALESCE(e.entradas, 0) + COALESCE(c.compras, 0)
                    - COALESCE(v.ventas, 0) - COALESCE(r.remisiones, 0)
                    AS stock_final
            FROM producto p
            LEFT JOIN (
                SELECT de.id_producto, SUM(de.cantidad) AS entradas
                FROM detalle_entradas de
                INNER JOIN entradas e ON e.id_entrada = de.id_entrada
                WHERE e.estado = 'ACTIVA'
                GROUP BY de.id_producto
            ) e ON e.id_producto = p.id_producto
            LEFT JOIN (
                SELECT dc.id_producto, SUM(dc.cantidad) AS compras
                FROM detalle_compras dc
                INNER JOIN compras c ON c.id_compra = dc.id_compra
                WHERE c.estado = 'ACTIVA'
                GROUP BY dc.id_producto
            ) c ON c.id_producto = p.id_producto
            LEFT JOIN (
                SELECT dv.id_producto, SUM(dv.cantidad) AS ventas
                FROM detalle_venta dv
                INNER JOIN venta v ON v.id_venta = dv.id_venta
                WHERE v.estado = 'ACTIVA'
                GROUP BY dv.id_producto
            ) v ON v.id_producto = p.id_producto
            LEFT JOIN (
                SELECT dr.id_producto, SUM(dr.cantidad) AS remisiones
                FROM detalle_remision dr
                INNER JOIN remision r ON r.id_remision = dr.id_remision
                WHERE r.estado = 'ACTIVA'
                GROUP BY dr.id_producto
            ) r ON r.id_producto = p.id_producto
            -- Solo se incluyen productos que tengan por lo menos una entrada activa.
            WHERE COALESCE(e.entradas, 0) > 0
            -- Ordenar por código agrupa prefijos como LAC, FRU, ABN, etc.
            ORDER BY p.codigo ASC
        """
        # Ejecuta la consulta (sin parámetros porque no hay filtros dinámicos)
        cursor.execute(sql)

        # Retorna todos los resultados como lista de diccionarios
        return cursor.fetchall()
    finally:
        # Bloque finally: se ejecuta SIEMPRE para liberar recursos
        # Independientemente de si hubo error o no
        cursor.close()
        conexion.close()
