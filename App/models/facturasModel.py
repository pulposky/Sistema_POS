from database.bd import conectar


def obtener_documentos():
    """
    Versión optimizada con menos consultas
    """
    documentos = []
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    # Obtener todos los clientes de una vez
    cursor.execute("SELECT id_cliente, nombre FROM clientes")
    clientes = {c['id_cliente']: c['nombre'] for c in cursor.fetchall()}

    # Obtener todos los proveedores de una vez
    cursor.execute("SELECT id_proveedor, nombre FROM proveedores")
    proveedores = {p['id_proveedor']: p['nombre'] for p in cursor.fetchall()}

    # Obtener todos los usuarios de una vez
    cursor.execute("SELECT id_usuario, nombre FROM usuarios")
    usuarios = {u['id_usuario']: u['nombre'] for u in cursor.fetchall()}

    # ========== VENTAS ==========
    cursor.execute("SELECT id_venta, fecha, total, id_cliente, id_usuario FROM venta")
    ventas = cursor.fetchall()   
    

    for venta in ventas:
        # Obtener productos
        cursor.execute("""
            SELECT p.nombre 
            FROM detalle_venta dv
            JOIN producto p ON p.id_producto = dv.id_producto
            WHERE dv.id_venta = %s
        """, (venta['id_venta'],))
        productos = [p['nombre'] for p in cursor.fetchall()]

        documentos.append({
            'tipo': 'VENTA',
            'numero': venta['id_venta'],
            'fecha': venta['fecha'],
            'tercero': clientes.get(venta['id_cliente'], '-'),
            'usuario': usuarios.get(venta['id_usuario'], '-'),
            'total': venta['total'],
            'productos': ', '.join(productos) if productos else '-'
        })

    # ========== COMPRAS ==========
    cursor.execute("SELECT id_compra, fecha, total, id_proveedor, id_usuario FROM compras")
    compras = cursor.fetchall()

    for compra in compras:
        # Obtener productos
        cursor.execute("""
            SELECT p.nombre 
            FROM detalle_compras dc
            JOIN producto p ON p.id_producto = dc.id_producto
            WHERE dc.id_compra = %s
        """, (compra['id_compra'],))
        productos = [p['nombre'] for p in cursor.fetchall()]

        documentos.append({
            'tipo': 'COMPRA',
            'numero': compra['id_compra'],
            'fecha': compra['fecha'],
            'tercero': proveedores.get(compra['id_proveedor'], '-'),
            'usuario': usuarios.get(compra['id_usuario'], '-'),
            'total': compra['total'],
            'productos': ', '.join(productos) if productos else '-'
        })

    # ========== REMISIONES ==========
    cursor.execute("SELECT id_remision, fecha, id_cliente, id_usuario FROM remision")
    remisiones = cursor.fetchall()

    for remision in remisiones:
        # Obtener productos
        cursor.execute("""
            SELECT p.nombre 
            FROM detalle_remision dr
            JOIN producto p ON p.id_producto = dr.id_producto
            WHERE dr.id_remision = %s
        """, (remision['id_remision'],))
        productos = [p['nombre'] for p in cursor.fetchall()]

        documentos.append({
            'tipo': 'REMISION',
            'numero': remision['id_remision'],
            'fecha': remision['fecha'],
            'tercero': clientes.get(remision['id_cliente'], '-'),
            'usuario': usuarios.get(remision['id_usuario'], '-'),
            'total': 0,
            'productos': ', '.join(productos) if productos else '-'
        })

    cursor.close()
    conexion.close()

    # Ordenar por fecha
    documentos.sort(key=lambda x: x['fecha'], reverse=True)

    return documentos