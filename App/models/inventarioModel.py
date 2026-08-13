from database.bd import conectar

# Modelo para construir el informe de inventario desde los movimientos.


def obtener_informe_inventario():
    """Retorna un diccionario por producto con sus entradas y salidas.

    El stock se calcula en SQL para que el informe no dependa del valor
    almacenado en ``producto.stock``.
    """
    conexion = conectar()
    if not conexion:
        return []

    cursor = conexion.cursor(dictionary=True)
    try:
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
        cursor.execute(sql)
        return cursor.fetchall()
    finally:
        cursor.close()
        conexion.close()
