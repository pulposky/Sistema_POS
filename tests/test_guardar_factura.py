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

print('OK: 5 casos')
