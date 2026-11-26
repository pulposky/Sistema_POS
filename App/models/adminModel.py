"""
Módulo de datos del Panel de Administración del sistema POS.

Centraliza todas las consultas SQL que usa el módulo de administración:
  - Indicadores del panel de control (ventas, compras, productos, etc.).
  - Gestión de usuarios (listar, actualizar, cambiar contraseña, eliminar).
  - Gestión del catálogo de productos (listar, crear/editar, eliminar).
  - Generación del respaldo de la base de datos con mysqldump.

Las contraseñas se almacenan siempre hasheadas con bcrypt, igual que el
resto del sistema (ver models/usuariosModel.py y models/loginModel.py).
"""

import glob
import os
import shutil
import subprocess

import bcrypt
import mysql.connector

# Configuración de conexión (la misma que usa todo el sistema)
from database.bd import conectar, DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT

# Cantidad mínima a partir de la cual un producto se considera con stock bajo.
UMBRAL_STOCK_BAJO = 5


# =========================================================
# INDICADORES (PANEL DE CONTROL)
# =========================================================

def obtener_estadisticas():
    """
    Recopila los indicadores que se muestran en la pestaña del panel de control.

    Retorna:
        dict: Diccionario con los indicadores del sistema. Si la conexión a la
        base de datos falla retorna un diccionario vacío.
    """
    conexion = conectar()
    if not conexion:
        return {}

    stats = {}
    try:
        cursor = conexion.cursor(dictionary=True)

        # -------- Ventas de hoy (documentos activos de la fecha actual) --------
        cursor.execute("""
            SELECT COUNT(*) AS documentos
            FROM venta
            WHERE estado = 'ACTIVA' AND DATE(fecha) = CURDATE()
        """)
        fila = cursor.fetchone() or {}
        stats["ventas_hoy"] = int(fila.get("documentos", 0))

        # -------- Compras de hoy --------
        cursor.execute("""
            SELECT COUNT(*) AS documentos, COALESCE(SUM(total), 0) AS total
            FROM compras
            WHERE estado = 'ACTIVA' AND DATE(fecha) = CURDATE()
        """)
        fila = cursor.fetchone() or {}
        stats["compras_hoy"] = int(fila.get("documentos", 0))
        stats["compras_total_hoy"] = float(fila.get("total", 0) or 0)

        # -------- Remisiones de hoy --------
        cursor.execute("""
            SELECT COUNT(*) AS documentos
            FROM remision
            WHERE estado = 'ACTIVA' AND DATE(fecha) = CURDATE()
        """)
        fila = cursor.fetchone() or {}
        stats["remisiones_hoy"] = int(fila.get("documentos", 0))

        # -------- Productos: totales, activos y stock bajo --------
        cursor.execute("""
            SELECT
                COUNT(*) AS total,
                COALESCE(SUM(CASE WHEN LOWER(estado) = 'activo' THEN 1 ELSE 0 END), 0) AS activos,
                COALESCE(SUM(CASE WHEN stock <= %s THEN 1 ELSE 0 END), 0) AS stock_bajo
            FROM producto
        """, (UMBRAL_STOCK_BAJO,))
        fila = cursor.fetchone() or {}
        stats["productos_total"] = int(fila.get("total", 0))
        stats["productos_activos"] = int(fila.get("activos", 0))
        stats["productos_stock_bajo"] = int(fila.get("stock_bajo", 0))

        # -------- Clientes y proveedores registrados --------
        stats["clientes"] = _contar(conexion, "SELECT COUNT(*) FROM clientes")
        stats["proveedores"] = _contar(conexion, "SELECT COUNT(*) FROM proveedores")

        # -------- Usuarios por rol --------
        cursor.execute("""
            SELECT
                COUNT(*) AS total,
                COALESCE(SUM(CASE WHEN rol IN ('Admin', 'Administrador') THEN 1 ELSE 0 END), 0) AS admins,
                COALESCE(SUM(CASE WHEN rol = 'Facturador' THEN 1 ELSE 0 END), 0) AS facturadores
            FROM usuarios
        """)
        fila = cursor.fetchone() or {}
        stats["usuarios_total"] = int(fila.get("total", 0))
        stats["usuarios_admin"] = int(fila.get("admins", 0))
        stats["usuarios_facturador"] = int(fila.get("facturadores", 0))

        # -------- Últimas ventas registradas --------
        cursor.execute("""
            SELECT
                v.id_venta,
                v.fecha,
                v.total,
                v.metodo_pago,
                v.estado,
                COALESCE(c.nombre, '-') AS cliente,
                COALESCE(u.nombre, '-') AS usuario
            FROM venta v
            LEFT JOIN clientes c ON c.id_cliente = v.id_cliente
            LEFT JOIN usuarios u ON u.id_usuario = v.id_usuario
            ORDER BY v.id_venta DESC
            LIMIT 8
        """)
        stats["ultimas_ventas"] = cursor.fetchall()

        return stats
    except Exception as error:
        print(f"Error al calcular indicadores: {error}")
        return stats
    finally:
        conexion.close()


def _contar(conexion, sql, valores=None):
    """Ejecuta un COUNT y retorna el valor; 0 si la consulta falla."""
    try:
        cursor = conexion.cursor()
        cursor.execute(sql, valores or ())
        fila = cursor.fetchone()
        cursor.close()
        return int(fila[0] or 0) if fila else 0
    except Exception as error:
        print(f"Consulta de conteo omitida: {error}")
        return 0


# =========================================================
# USUARIOS
# =========================================================

def listar_usuarios():
    """Retorna todos los usuarios del sistema ordenados por nombre."""
    conexion = conectar()
    if not conexion:
        return []
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT id_usuario, nombre, usuario, rol FROM usuarios ORDER BY nombre ASC"
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conexion.close()


def obtener_usuario(id_usuario):
    """Retorna los datos de un usuario por su ID, o None si no existe."""
    conexion = conectar()
    if not conexion:
        return None
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT id_usuario, nombre, usuario, rol FROM usuarios WHERE id_usuario = %s",
            (id_usuario,)
        )
        return cursor.fetchone()
    finally:
        cursor.close()
        conexion.close()


def existe_usuario(usuario):
    """Indica si ya existe un usuario con ese nombre de login."""
    conexion = conectar()
    if not conexion:
        return False
    try:
        cursor = conexion.cursor()
        cursor.execute("SELECT id_usuario FROM usuarios WHERE usuario = %s", (usuario,))
        return cursor.fetchone() is not None
    finally:
        cursor.close()
        conexion.close()


def contar_administradores(excluyendo_id=None):
    """
    Cuenta los usuarios con rol de administrador.

    Parámetro:
        excluyendo_id (int|None): ID que se excluye del conteo. Se usa para
        verificar que siempre quede al menos un administrador en el sistema.
    """
    conexion = conectar()
    if not conexion:
        return 0
    try:
        cursor = conexion.cursor()
        if excluyendo_id is not None:
            cursor.execute(
                "SELECT COUNT(*) FROM usuarios "
                "WHERE rol IN ('Admin', 'Administrador') AND id_usuario <> %s",
                (excluyendo_id,)
            )
        else:
            cursor.execute(
                "SELECT COUNT(*) FROM usuarios WHERE rol IN ('Admin', 'Administrador')"
            )
        fila = cursor.fetchone()
        return int(fila[0] or 0) if fila else 0
    finally:
        cursor.close()
        conexion.close()


def actualizar_usuario(id_usuario, nombre, usuario, rol):
    """
    Actualiza nombre, login y rol de un usuario existente.

    Lanza ValueError si el login ya pertenece a otro usuario.
    """
    conexion = conectar()
    if not conexion:
        raise ValueError("Sin conexión a la base de datos.")
    try:
        cursor = conexion.cursor()

        # Verifico que el login no esté tomado por otro usuario
        cursor.execute(
            "SELECT id_usuario FROM usuarios WHERE usuario = %s AND id_usuario <> %s",
            (usuario, id_usuario)
        )
        if cursor.fetchone():
            raise ValueError(f"Ya existe otro usuario con el login '{usuario}'.")

        cursor.execute(
            "UPDATE usuarios SET nombre = %s, usuario = %s, rol = %s WHERE id_usuario = %s",
            (nombre, usuario, rol, id_usuario)
        )
        conexion.commit()
    except mysql.connector.Error as error:
        raise ValueError(f"No fue posible actualizar el usuario: {error}")
    finally:
        cursor.close()
        conexion.close()


def cambiar_password(id_usuario, password):
    """Actualiza la contraseña del usuario (se guarda hasheada con bcrypt)."""
    conexion = conectar()
    if not conexion:
        raise ValueError("Sin conexión a la base de datos.")
    try:
        cursor = conexion.cursor()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        cursor.execute(
            "UPDATE usuarios SET password = %s WHERE id_usuario = %s",
            (password_hash, id_usuario)
        )
        conexion.commit()
    except mysql.connector.Error as error:
        raise ValueError(f"No fue posible cambiar la contraseña: {error}")
    finally:
        cursor.close()
        conexion.close()


def eliminar_usuario(id_usuario):
    """
    Elimina un usuario del sistema.

    Lanza ValueError si el usuario tiene documentos asociados (ventas,
    compras, entradas o remisiones), ya que esos documentos conservan
    la trazabilidad del usuario que los registró.
    """
    conexion = conectar()
    if not conexion:
        raise ValueError("Sin conexión a la base de datos.")
    try:
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM usuarios WHERE id_usuario = %s", (id_usuario,))
        conexion.commit()
        if cursor.rowcount == 0:
            raise ValueError("El usuario ya no existe.")
    except mysql.connector.IntegrityError:
        raise ValueError(
            "No se puede eliminar: el usuario tiene documentos asociados "
            "(ventas, compras, entradas o remisiones). "
            "Como alternativa, edítelo y cámbielo a Facturador."
        )
    finally:
        cursor.close()
        conexion.close()


# =========================================================
# PRODUCTOS
# =========================================================

def listar_productos(filtro=None):
    """
    Retorna el catálogo completo de productos.

    Parámetro:
        filtro (str|None): Texto de búsqueda que se compara contra código,
        nombre y categoría (búsqueda parcial, sin distinguir mayúsculas).
    """
    conexion = conectar()
    if not conexion:
        return []
    try:
        cursor = conexion.cursor(dictionary=True)
        sql = """
            SELECT id_producto, codigo, nombre, unidad, lugar, precio,
                   categoria, stock, estado, descripcion
            FROM producto
        """
        valores = ()
        if filtro and filtro.strip():
            sql += " WHERE codigo LIKE %s OR nombre LIKE %s OR categoria LIKE %s"
            patron = f"%{filtro.strip()}%"
            valores = (patron, patron, patron)
        sql += " ORDER BY codigo ASC"
        cursor.execute(sql, valores)
        return cursor.fetchall()
    finally:
        cursor.close()
        conexion.close()


def guardar_producto(datos, id_producto=None):
    """
    Crea un producto nuevo o actualiza uno existente.

    Parámetros:
        datos (dict): Campos del producto (codigo, nombre, unidad, lugar,
            precio, categoria, stock, estado, descripcion).
        id_producto (int|None): Si se indica, se actualiza ese producto;
            si es None se crea uno nuevo.

    Retorna:
        int: ID del producto creado o actualizado.

    Lanza ValueError si el código ya pertenece a otro producto.
    """
    conexion = conectar()
    if not conexion:
        raise ValueError("Sin conexión a la base de datos.")
    try:
        cursor = conexion.cursor()

        # Verifico que el código no esté tomado por otro producto
        if id_producto is not None:
            cursor.execute(
                "SELECT id_producto FROM producto WHERE codigo = %s AND id_producto <> %s",
                (datos["codigo"], id_producto)
            )
        else:
            cursor.execute(
                "SELECT id_producto FROM producto WHERE codigo = %s",
                (datos["codigo"],)
            )
        if cursor.fetchone():
            raise ValueError(f"Ya existe otro producto con el código '{datos['codigo']}'.")

        valores = (
            datos["codigo"],
            datos["nombre"],
            datos["unidad"],
            datos["lugar"],
            datos["precio"],
            datos["categoria"],
            datos["stock"],
            datos["estado"],
            datos["descripcion"],
        )

        if id_producto is not None:
            cursor.execute("""
                UPDATE producto
                SET codigo = %s, nombre = %s, unidad = %s, lugar = %s, precio = %s,
                    categoria = %s, stock = %s, estado = %s,
                    descripcion = %s
                WHERE id_producto = %s
            """, valores + (id_producto,))
            conexion.commit()
            return id_producto

        cursor.execute("""
            INSERT INTO producto
                (codigo, nombre, unidad, lugar, precio, categoria, stock,
                 estado, descripcion)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, valores)
        conexion.commit()
        return cursor.lastrowid
    except mysql.connector.Error as error:
        raise ValueError(f"No fue posible guardar el producto: {error}")
    finally:
        cursor.close()
        conexion.close()


def eliminar_producto(id_producto):
    """
    Elimina un producto del catálogo.

    Lanza ValueError si el producto tiene movimientos asociados (ventas,
    compras, entradas o remisiones); en ese caso debe quedar inactivo.
    """
    conexion = conectar()
    if not conexion:
        raise ValueError("Sin conexión a la base de datos.")
    try:
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM producto WHERE id_producto = %s", (id_producto,))
        conexion.commit()
        if cursor.rowcount == 0:
            raise ValueError("El producto ya no existe.")
    except mysql.connector.IntegrityError:
        raise ValueError(
            "No se puede eliminar: el producto tiene movimientos asociados "
            "(ventas, compras, entradas o remisiones). "
            "Como alternativa, edítelo y márquelo como inactivo."
        )
    finally:
        cursor.close()
        conexion.close()


# =========================================================
# RESPALDO DE LA BASE DE DATOS
# =========================================================

def _buscar_mysqldump():
    """
    Lista los ejecutables de mysqldump candidatos, en orden de prioridad.

    El orden importa: en equipos con varias instalaciones de MySQL (por
    ejemplo Laragon + XAMPP) el mysqldump del PATH puede ser de otra versión
    y fallar contra el servidor real. Por eso se prueban en orden:
      1. Variable de entorno MYSQLDUMP_PATH (ruta personalizada).
      2. El mysqldump del PATH del sistema.
      3. Las versiones de Laragon (de la más reciente a la más antigua).
      4. El mysqldump de XAMPP.
    """
    candidatos = []

    # Ruta personalizada por el usuario (opcional)
    personalizado = os.getenv("MYSQLDUMP_PATH")
    if personalizado:
        candidatos.append(personalizado)

    # mysqldump disponible en el PATH del sistema
    desde_path = shutil.which("mysqldump")
    if desde_path:
        candidatos.append(desde_path)

    # Laragon: todas las versiones instaladas, de la más nueva a la más vieja
    candidatos.extend(sorted(
        glob.glob(r"C:\laragon\bin\mysql\*\bin\mysqldump.exe"),
        reverse=True,
    ))

    # XAMPP
    candidatos.append(r"C:\xampp\mysql\bin\mysqldump.exe")

    # Quito duplicados preservando el orden
    vistos = set()
    return [c for c in candidatos if c and not (c in vistos or vistos.add(c))]


def generar_respaldo(ruta_destino):
    """
    Genera un respaldo .sql de la base de datos usando mysqldump.

    Se prueban varios candidatos de mysqldump (ver _buscar_mysqldump) hasta
    encontrar uno compatible con el servidor MySQL en ejecución.

    Parámetro:
        ruta_destino (str): Ruta completa del archivo .sql a crear.

    Retorna:
        str: La ruta donde quedó guardado el respaldo.

    Lanza ValueError si no hay ningún mysqldump disponible o si el
    respaldo falla con todos los candidatos.
    """
    candidatos = _buscar_mysqldump()
    if not candidatos:
        raise ValueError(
            "No se encontró 'mysqldump'. Verifica que MySQL esté instalado y que "
            "su carpeta bin (ej: C:\\laragon\\bin\\mysql\\<version>\\bin) esté en "
            "el PATH del sistema."
        )

    # mysqldump viene instalado junto con MySQL (Laragon, XAMPP, MySQL Server).
    # La contraseña se pasa por variable de entorno para que no aparezca en
    # la lista de procesos del sistema operativo.
    entorno = dict(os.environ)
    if DB_PASSWORD:
        entorno["MYSQL_PWD"] = DB_PASSWORD

    ultimo_error = ""
    for ejecutable in candidatos:
        comando = [
            ejecutable,
            f"--host={DB_HOST}",
            f"--port={DB_PORT}",
            f"--user={DB_USER}",
            "--single-transaction",
            "--routines",
            "--triggers",
            DB_NAME,
        ]
        try:
            # 'wb' trunca el archivo en cada intento, por lo que un intento
            # fallido no deja basura antes de probar el siguiente candidato
            with open(ruta_destino, "wb") as archivo:
                resultado = subprocess.run(
                    comando,
                    stdout=archivo,
                    stderr=subprocess.PIPE,
                    env=entorno,
                )
        except OSError as error:
            # El ejecutable no se pudo ejecutar (ruta inválida, permisos, etc.)
            ultimo_error = str(error)
            continue

        if resultado.returncode == 0:
            break

        ultimo_error = resultado.stderr.decode("utf-8", errors="ignore").strip()
    else:
        # Ningún candidato funcionó
        raise ValueError(
            f"El respaldo falló: {ultimo_error or 'error desconocido de mysqldump'} "
            "(si tienes varias versiones de MySQL instaladas, indica la correcta "
            "en la variable de entorno MYSQLDUMP_PATH)."
        )

    # Verifico que el archivo tenga contenido (mysqldump pudo fallar en silencio)
    if os.path.getsize(ruta_destino) == 0:
        raise ValueError("El respaldo se generó vacío. Verifica las credenciales de MySQL.")

    return ruta_destino
