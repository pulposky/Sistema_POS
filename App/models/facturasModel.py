from database.bd import conectar

# Modelo para consultar documentos y movimientos del sistema.

def obtener_documentos():
    documentos = []
    conexion = None
    cursor = None

    try:
        conexion = conectar()
        if conexion is None:
            print("[ERROR] conectar() devolvió None")
            return documentos

        cursor = conexion.cursor(dictionary=True)

        # Obtener clientes, proveedores y usuarios
        cursor.execute("SELECT id_cliente, nombre FROM clientes")
        clientes = {c['id_cliente']: c['nombre'] for c in cursor.fetchall()}

        cursor.execute("SELECT id_proveedor, nombre FROM proveedores")
        proveedores = {p['id_proveedor']: p['nombre'] for p in cursor.fetchall()}

        cursor.execute("SELECT id_usuario, nombre FROM usuarios")
        usuarios = {u['id_usuario']: u['nombre'] for u in cursor.fetchall()}

        # ========== VENTAS ==========
        cursor.execute("SELECT id_venta, fecha, total, id_cliente, id_usuario FROM venta")
        ventas = cursor.fetchall()

        for venta in ventas:
            cursor.execute("""
                SELECT p.nombre
                FROM detalle_venta dv
                JOIN producto p ON p.id_producto = dv.id_producto
                WHERE dv.id_venta = %s
            """, (venta['id_venta'],))
            productos = [p['nombre'] for p in cursor.fetchall()]

            documentos.append({
                'tipo':      'VENTA',
                'numero':    venta['id_venta'],
                'fecha':     venta['fecha'],
                'tercero':   clientes.get(venta['id_cliente'], '-'),
                'usuario':   usuarios.get(venta['id_usuario'], '-'),
                'total':     venta['total'],
                'productos': ', '.join(productos) if productos else '-'
            })

        # ========== COMPRAS ==========
        cursor.execute("SELECT id_compra, fecha, total, id_proveedor, id_usuario FROM compras")
        compras = cursor.fetchall()

        for compra in compras:
            cursor.execute("""
                SELECT p.nombre
                FROM detalle_compras dc
                JOIN producto p ON p.id_producto = dc.id_producto
                WHERE dc.id_compra = %s
            """, (compra['id_compra'],))
            productos = [p['nombre'] for p in cursor.fetchall()]

            documentos.append({
                'tipo':      'COMPRA',
                'numero':    compra['id_compra'],
                'fecha':     compra['fecha'],
                'tercero':   proveedores.get(compra['id_proveedor'], '-'),
                'usuario':   usuarios.get(compra['id_usuario'], '-'),
                'total':     compra['total'],
                'productos': ', '.join(productos) if productos else '-'
            })

        # ========== REMISIONES ==========
        cursor.execute("SELECT id_remision, fecha, id_cliente, id_usuario FROM remision")
        remisiones = cursor.fetchall()

        for remision in remisiones:
            cursor.execute("""
                SELECT p.nombre
                FROM detalle_remision dr
                JOIN producto p ON p.id_producto = dr.id_producto
                WHERE dr.id_remision = %s
            """, (remision['id_remision'],))
            productos = [p['nombre'] for p in cursor.fetchall()]

            documentos.append({
                'tipo':      'REMISION',
                'numero':    remision['id_remision'],
                'fecha':     remision['fecha'],
                'tercero':   clientes.get(remision['id_cliente'], '-'),
                'usuario':   usuarios.get(remision['id_usuario'], '-'),
                'total':     0,
                'productos': ', '.join(productos) if productos else '-'
            })

        documentos.sort(key=lambda x: x['fecha'], reverse=True)

    except Exception as err:
        import traceback
        traceback.print_exc()
        print(f"[ERROR obtener_documentos] {err}")

    finally:
        try:
            if cursor:
                cursor.close()
            if conexion:
                conexion.close()
        except Exception:
            pass

    # SIEMPRE retorna lista (nunca None)
    return documentos



def obtener_ventas_detalladas():
    documentos = []
    conexion = None
    cursor = None

    try:
        conexion = conectar()
        if conexion is None:
            print("[ERROR] conectar() devolvió None")
            return documentos

        cursor = conexion.cursor(dictionary=True)

        cursor.execute("SELECT id_cliente, nombre FROM clientes")
        clientes = {c['id_cliente']: c['nombre'] for c in cursor.fetchall()}

        cursor.execute("SELECT id_usuario, nombre FROM usuarios")
        usuarios = {u['id_usuario']: u['nombre'] for u in cursor.fetchall()}

        cursor.execute("""
            SELECT
                v.id_venta,
                v.fecha,
                v.id_cliente,
                v.id_usuario,
                p.nombre           AS producto,
                dv.cantidad        AS cantidad,
                dv.precio_unitario AS precio_unitario,
                dv.subtotal        AS subtotal
            FROM venta v
            JOIN detalle_venta dv ON dv.id_venta = v.id_venta
            JOIN producto p       ON p.id_producto = dv.id_producto
            ORDER BY v.fecha DESC, v.id_venta DESC, p.nombre ASC
        """)

        for r in cursor.fetchall():
            documentos.append({
                'tipo':            'VENTA DETALLADA',
                'numero':          r['id_venta'],
                'fecha':           r['fecha'],
                'tercero':         clientes.get(r['id_cliente'], '-'),
                'usuario':         usuarios.get(r['id_usuario'], '-'),
                'producto':        r['producto'],
                'cantidad':        r['cantidad'],
                'precio_unitario': r['precio_unitario'],
                'subtotal':        r['subtotal'],
            })

    except Exception as err:
        import traceback
        traceback.print_exc()
        print(f"[ERROR obtener_ventas_detalladas] {err}")

    finally:
        try:
            if cursor:
                cursor.close()
            if conexion:
                conexion.close()
        except Exception:
            pass

    return documentos