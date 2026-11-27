# Prueba del ticket con envío/descuento. Ejecutar: .venv\Scripts\python tests\test_ticket_y_panel.py
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'App'))
from utils.generarFactura import _crear_texto_ticket

base = dict(
    id_factura=1, fecha_actual="01/01/2026 10:00 AM", etiqueta_documento="Factura",
    titulo_documento="FACTURA DE VENTA", nombre_cliente="Ana", doc_cliente="123",
    nombre_usuario="Caja", metodo_pago_txt="Efectivo",
    productos=[{"nombre": "Resma", "cantidad": 1, "unidad": "UND", "precio": 10000,
                "subtotal": 10000, "lugar": "SenaEmpresa", "id": 7}],
    total=12500, dinero_recibido=12500, cambio=0, mostrar_precios=True, es_mixto=False,
)

con = _crear_texto_ticket(**base, envio=6000, descuento=3500)
assert "Descuento:" in con and "$3,500" in con.split("Descuento:")[1].split("\n")[0]
assert "Envío:" in con and "$6,000" in con.split("Envío:")[1].split("\n")[0]

sin = _crear_texto_ticket(**base)
assert "Envío" not in sin
assert sin == _crear_texto_ticket(**base, envio=0, descuento=0)
print("OK")
