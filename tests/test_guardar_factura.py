# Prueba de guardar_factura con una conexión falsa (no toca la base real).
# Ejecutar: .venv\Scripts\python tests\test_guardar_factura.py
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'App'))
from models import ventasModel


class CursorFalso:
    def __init__(self, bd):
        self.bd, self.rowcount, self.lastrowid, self._fila = bd, 0, 1, None

    def execute(self, sql, params=()):
        self.bd.sqls.append(sql)
        if 'INSERT INTO detalle_venta' in sql:
            self.bd.detalles.append(params)
        if 'FOR UPDATE' in sql:
            self._fila = (self.bd.estado_apartado,)
        elif sql.lstrip().startswith('UPDATE producto SET stock'):
            cant, idp, _ = params
            ok = self.bd.stock[idp] >= cant
            if ok:
                self.bd.stock[idp] -= cant
            self.rowcount = int(ok)
        elif 'UPDATE apartados' in sql:
            self.bd.estado_apartado = 'entregado'

    def fetchone(self):
        return self._fila

    def close(self):
        pass


class BDFalsa:
    def __init__(self, stock, estado_apartado='confirmado'):
        self.stock, self.estado_apartado, self.sqls, self.detalles = stock, estado_apartado, [], []
        self.confirmada = False

    def cursor(self, **_):
        return CursorFalso(self)

    def commit(self):
        self.confirmada = True

    def rollback(self):
        pass

    def close(self):
        pass


def correr(bd, factura, detalles):
    ventasModel.conectar = lambda: bd
    return ventasModel.guardar_factura(factura, detalles)


linea = lambda idp, cant, apartado=False: {'id_producto': idp, 'cantidad': cant, 'nombre': 'x', 'unidad': 'und', 'precio': 1, 'subtotal': cant, 'es_apartado': apartado}

# Venta directa con stock suficiente: descuenta.
bd = BDFalsa({1: 10})
assert correr(bd, {}, [linea(1, 3)]) == 1 and bd.stock[1] == 7 and bd.confirmada

# Sin stock suficiente: no guarda nada y el stock no queda negativo.
bd = BDFalsa({1: 2})
assert correr(bd, {}, [linea(1, 3)]) is None and bd.stock[1] == 2 and not bd.confirmada

# Entrega de pedido web pagado: no descuenta stock y lo marca entregado.
bd = BDFalsa({1: 10})
assert correr(bd, {'id_apartado': 5}, [linea(1, 4, apartado=True)]) == 1
assert bd.stock[1] == 10 and bd.estado_apartado == 'entregado'

# Pedido web sin pagar o cancelado: se rechaza.
bd = BDFalsa({1: 10}, estado_apartado='pendiente')
assert correr(bd, {'id_apartado': 5}, [linea(1, 4, apartado=True)]) is None and not bd.confirmada

# limite_venta ya no se toca.
assert not any('limite_venta' in s for s in bd.sqls)

# --- Presentaciones ---
from controllers import ventasController as vc

# 2 cajas x10 con stock 25: descuenta 20 y el detalle va en unidad mínima.
caja = dict(linea(1, 2), factor=10, precio=45000, subtotal=90000)
bd = BDFalsa({1: 25})
assert correr(bd, {}, [caja]) == 1 and bd.stock[1] == 5
_, _, cant_det, precio_det, sub_det = bd.detalles[0]
assert cant_det == 20 and precio_det == 4500 and sub_det == 90000

# 3 cajas x10 con stock 25: no alcanza, nada cambia.
bd = BDFalsa({1: 25})
assert correr(bd, {}, [dict(caja, cantidad=3)]) is None and bd.stock[1] == 25

# Aviso de stock en pantalla cuenta el factor.
assert vc.obtener_stock_restante({'stock': 25, 'cantidad': 3, 'factor': 10}) == -5

# Cambiar a Caja x10 con descuento manual del 10 %.
fila = {'precio': 4500, 'precio_unidad': 4500, 'precio_original': 4500, 'precio_original_unidad': 4500,
        'cantidad': 2, 'descuento': 10, 'unidad': 'UND', 'factor': 1,
        'presentaciones': [{'nombre': 'UND', 'factor': 1}, {'nombre': 'Caja x10', 'factor': 10}]}
vc.cambiar_presentacion(fila, 10)
assert fila['precio'] == 45000 and fila['subtotal'] == 81000 and fila['unidad'] == 'Caja x10'
vc.cambiar_presentacion(fila, 1)
assert fila['precio'] == 4500 and fila['unidad'] == 'UND'

# Opciones: la unidad mínima va primero si no hay presentación de factor 1.
assert vc.armar_presentaciones('UND', [{'nombre': 'Caja x100', 'factor': 100}]) == [
    {'nombre': 'UND', 'factor': 1}, {'nombre': 'Caja x100', 'factor': 100}]
assert vc.armar_presentaciones('UND', [{'nombre': 'Unidad', 'factor': 1}, {'nombre': 'Par', 'factor': 2}])[0]['nombre'] == 'Unidad'
print('OK: 12 casos')
