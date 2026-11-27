# Prueba de la entrega de pedidos web (F9) con una base falsa (no toca la real).
# Ejecutar: .venv\Scripts\python tests\test_entrega_pedido.py
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'App'))
from models import ventasModel as vm


def linea(id_apartado, estado, cantidad, precio, pres=None, factor=None):
    return {'id_apartado': id_apartado, 'estado': estado, 'cantidad': str(cantidad),
            'precio_aplicado': precio, 'presentacion_nombre': pres, 'presentacion_factor': factor,
            'id_producto': id_apartado, 'nombre': f'P{id_apartado}', 'unidad': 'UND',
            'codigo': f'C{id_apartado}', 'lugar': 'Tienda'}


def pedido(lineas, descuento=0, envio=0, id_cliente=7, metodo='nequi'):
    return {'id_pedido': 31, 'id_cliente': id_cliente, 'nombre_cliente': 'Ana Pérez', 'metodo_pago': metodo,
            'descuento': descuento, 'costo_envio': envio, 'codigo_cupon': 'HOLA', 'lineas': lineas}


# --- resumen_pedido: las mismas cuentas que la tienda ---
r = vm.resumen_pedido(pedido([linea(1, 'confirmado', 20, 1400, 'Caja x10', 10), linea(2, 'confirmado', 3, 2000)],
                             descuento=3500, envio=6000))
assert r['subtotal'] == 34000 and r['descuento'] == 3500 and r['envio'] == 6000 and r['total'] == 36500
assert r['lineas'][0]['texto_cantidad'] == '2 Caja x10' and r['lineas'][0]['precio_presentacion'] == 14000
assert r['lineas'][1]['texto_cantidad'] == '3 UND'

# Línea cancelada: no cuenta.
r = vm.resumen_pedido(pedido([linea(1, 'confirmado', 2, 1000), linea(2, 'cancelado', 5, 1000)]))
assert r['total'] == 2000 and len(r['lineas']) == 1

# Cupón mayor que el subtotal: el descuento se limita al subtotal.
r = vm.resumen_pedido(pedido([linea(1, 'confirmado', 1, 1000)], descuento=5000, envio=0))
assert r['descuento'] == 1000 and r['total'] == 0

# Ya entregado en parte: no se vuelven a cobrar ni el envío ni el cupón.
r = vm.resumen_pedido(pedido([linea(1, 'entregado', 1, 1000), linea(2, 'confirmado', 1, 1000)],
                             descuento=500, envio=6000))
assert r['total'] == 1000 and r['envio'] == 0 and r['descuento'] == 0

# Factor 0 o nulo con nombre: se trata como unidades.
r = vm.resumen_pedido(pedido([linea(1, 'confirmado', 4, 100, 'Caja', 0)]))
assert r['lineas'][0]['texto_cantidad'] == '4 UND' and r['total'] == 400


# --- entregar_pedido con base falsa ---
class Cursor:
    def __init__(self, bd):
        self.bd, self._res, self.lastrowid = bd, None, 99

    def execute(self, sql, params=()):
        s = ' '.join(sql.split())
        self.bd.sqls.append(s)
        if s.startswith('SELECT * FROM pedidos'):
            p = dict(self.bd.pedido); p.pop('lineas')
            self._res = [p]
        elif 'FROM apartados a' in s:
            self._res = [dict(l) for l in self.bd.pedido['lineas']]
        elif 'FROM clientes' in s:
            self._res = [{'id_cliente': params[0]}] if self.bd.cliente_existe else []
        elif s.startswith('INSERT INTO venta'):
            self.bd.venta = params
        elif s.startswith('INSERT INTO detalle_venta'):
            self.bd.detalles.append(params)
        elif s.startswith('UPDATE apartados'):
            for l in self.bd.pedido['lineas']:
                if l['estado'] == 'confirmado':
                    l['estado'] = 'entregado'
        elif s.startswith('UPDATE producto'):
            raise AssertionError('No debe tocar el stock')

    def fetchone(self):
        return self._res[0] if self._res else None

    def fetchall(self):
        return self._res or []

    def close(self):
        pass


class BD:
    def __init__(self, ped, cliente_existe=True):
        self.pedido, self.cliente_existe = ped, cliente_existe
        self.sqls, self.detalles, self.venta, self.confirmada = [], [], None, False

    def cursor(self, **_):
        return Cursor(self)

    def commit(self):
        self.confirmada = True

    def rollback(self):
        pass

    def close(self):
        pass


def entregar(bd):
    vm.conectar = lambda: bd
    return vm.entregar_pedido(31, id_usuario=2)


# Pedido normal: venta con el total de la tienda, sin stock, líneas entregadas, todo bloqueado.
bd = BD(pedido([linea(1, 'confirmado', 20, 1400, 'Caja x10', 10), linea(2, 'confirmado', 3, 2000)],
               descuento=3500, envio=6000))
res = entregar(bd)
assert res['id_venta'] == 99 and bd.confirmada
assert sum('FOR UPDATE' in s for s in bd.sqls) == 2
fecha, total, metodo, estado, id_cliente, id_usuario, recibido, cambio, nota, id_apartado = bd.venta
assert total == 36500 and metodo == 'Transferencia' and recibido == 36500 and cambio == 0
assert id_cliente == 7 and id_usuario == 2 and id_apartado == 1 and nota == 'Pedido web #31'
assert [(d[2], d[3]) for d in bd.detalles] == [(20, 1400), (3, 2000)]
assert all(l['estado'] == 'entregado' for l in bd.pedido['lineas'])

# Línea pendiente (alguien cambió el pedido en la web): se rechaza sin guardar.
bd = BD(pedido([linea(1, 'confirmado', 1, 1000), linea(2, 'pendiente', 1, 1000)]))
try:
    entregar(bd); raise SystemExit('debió rechazar')
except ValueError as e:
    assert 'sin pagar' in str(e)
assert not bd.confirmada and bd.venta is None

# Ya entregado o cancelado por completo: se rechaza.
bd = BD(pedido([linea(1, 'entregado', 1, 1000)]))
try:
    entregar(bd); raise SystemExit('debió rechazar')
except ValueError as e:
    assert 'ya no está por entregar' in str(e)

# Cliente que no existe en clientes: cliente genérico y el nombre en la nota; efectivo -> Efectivo.
bd = BD(pedido([linea(1, 'confirmado', 1, 1000)], id_cliente=555, metodo='efectivo'), cliente_existe=False)
entregar(bd)
assert bd.venta[4] == 1 and bd.venta[8] == 'Pedido web #31 - Ana Pérez' and bd.venta[2] == 'Efectivo'

# --- Revisión final ---
# El pedido cambió en la tienda (una línea cancelada) mientras el cajero lo veía: se rechaza.
bd = BD(pedido([linea(1, 'confirmado', 1, 1000), linea(2, 'cancelado', 1, 1000)]))
vm.conectar = lambda: bd
try:
    vm.entregar_pedido(31, id_usuario=2, lineas_vistas=[1, 2]); raise SystemExit('debió rechazar')
except ValueError as e:
    assert 'cambió' in str(e)
assert bd.venta is None and not bd.confirmada
# Si coincide con lo que vio, se entrega.
bd = BD(pedido([linea(1, 'confirmado', 1, 1000), linea(2, 'cancelado', 1, 1000)]))
vm.conectar = lambda: bd
assert vm.entregar_pedido(31, id_usuario=2, lineas_vistas=[1])['id_venta'] == 99

from controllers import ventasController as vc
# Si el PDF falla (devuelve None), se avisa que no se imprimió; la venta ya está guardada.
vc.entregar_pedido = lambda id_pedido, id_usuario, lineas_vistas=None: {
    'id_venta': 5, 'id_cliente': 1, 'pedido': {'nombre_cliente': 'Ana', 'metodo_pago': 'nequi'},
    'resumen': {'lineas': [], 'total': 0, 'envio': 0, 'descuento': 0}}
vc.generar_factura_pdf = lambda **k: None
assert vc.entregar_pedido_web(31, {'id_usuario': 1})['impreso'] is False
vc.generar_factura_pdf = lambda **k: 'ruta.pdf'
assert vc.entregar_pedido_web(31, {'id_usuario': 1})['impreso'] is True

# Reimpresión: envío y cupón del pedido si cuadran con el total guardado.
assert vc.ajustes_venta_web({'total': 36500, 'pedido_envio': 6000, 'pedido_descuento': 3500}, 34000) == (6000, 3500)
# Si no cuadran (entrega en partes), se muestra solo la diferencia.
assert vc.ajustes_venta_web({'total': 1000, 'pedido_envio': 6000, 'pedido_descuento': 500}, 1000) == (0, 0)
assert vc.ajustes_venta_web({'total': 2500, 'pedido_envio': 6000, 'pedido_descuento': 3500}, 2000) == (500, 0)
assert vc.ajustes_venta_web({'total': 1500, 'pedido_envio': None, 'pedido_descuento': None}, 2000) == (0, 500)
print('OK: 17 casos')
