# Entrega de pedidos web (F9): plan de implementación

> **Para agentes:** superpowers:executing-plans. Las tareas A y B son independientes, cada una con sus propios archivos.

**Objetivo:** F9 entrega un pedido web completo y pagado en una sola factura, con el mismo total que la tienda y sin descontar stock.
**Arquitectura:** el modelo hace todo el trabajo de base de datos en una transacción. Una ventana nueva en `utils/` muestra la lista y el detalle.
El ticket y el PDF aceptan envío y descuento. La edición de facturas web queda bloqueada y el panel las separa.
**Tecnología:** Python, Flet 0.85 y mysql-connector. Pruebas: scripts con asserts en `tests/`.
**Diseño:** `docs/superpowers/specs/2026-11-26-entrega-pedidos-web-design.md`

## Restricciones generales
- No se cambia el esquema de ninguna tabla. Las tablas de la web solo se leen, salvo `apartados.estado`.
- Se bloquea con `SELECT ... FOR UPDATE` dentro de la transacción. Se imprime después del commit.

## Revisión: casos a vigilar
1. Un pedido con una línea cancelada: el total no la incluye.
2. El cupón es mayor que la suma de las líneas vivas: el descuento se limita a esa suma.
3. Mientras la ventana está abierta, alguien confirma o cancela en la web: la entrega lee de nuevo y se rechaza si ya no es válida.
4. Un pedido sin cliente válido: se usa el cliente 1 y el nombre del pedido va en la nota.
5. La impresora falla: la venta y la entrega quedan guardadas.

---

### Tarea A (yo): modelo, controlador y ventana F9
**Archivos:** `App/models/ventasModel.py`, `App/controllers/ventasController.py`, `App/utils/entregarApartado.py` (se reescribe), `App/views/vender.py` (solo `seleccionar_apartado` y `entregar_apartado`) y `tests/test_entrega_pedido.py` (nuevo).
**Interfaces:**
- `ventasModel.obtener_pedidos_por_entrega() -> list[dict]`. Cabecera del pedido: `id_pedido, nombre_cliente, fecha, entrega, metodo_pago, subtotal, descuento, costo_envio, codigo_cupon, direccion_entrega, telefono_entrega` y `lineas` (lista de `id_apartado, estado, cantidad, precio_aplicado, presentacion_nombre, presentacion_factor, id_producto, nombre, unidad, codigo, lugar`). Incluye solo los pedidos con alguna línea confirmada y ninguna pendiente.
- `ventasController.resumen_pedido(pedido: dict) -> dict`. Función pura que devuelve `{'lineas': [...confirmadas, con texto_cantidad, precio_presentacion, subtotal], 'subtotal', 'descuento', 'envio', 'total'}`. Aplica la regla del cupón y el envío: solo si ninguna línea está `entregado`.
- `ventasModel.entregar_pedido(id_pedido: int, id_usuario: int) -> dict`. Devuelve `{'id_venta', 'resumen', 'pedido'}` o lanza `ValueError` con el mensaje para el cajero.
- `ventasController.entregar_pedido_web(id_pedido, usuario) -> dict`. Llama al modelo y luego a `generar_factura_pdf(..., envio=, descuento=)`. Un fallo al imprimir no anula la venta.
- Prueba: base falsa (como en `tests/test_guardar_factura.py`) para `entregar_pedido`, y asserts directos para `resumen_pedido`. Casos: pedido normal, línea cancelada, cupón mayor que el subtotal, ya entregado en parte (sin envío ni cupón), línea pendiente (rechazo) y cliente inexistente (cliente 1).

### Tarea B (subagente Sonnet): ticket, edición y panel
**Archivos:** solo `App/utils/generarFactura.py`, `App/models/actualizarDocumentosModel.py` (y su controlador si muestra el error), `App/models/adminModel.py` y `App/views/adminPanel.py`, más `tests/test_ticket_y_panel.py` (nuevo).
- `generar_factura_pdf`, `imprimir_factura_datos` y `_crear_texto_ticket` ganan `envio=0, descuento=0`. "Descuento:" muestra `descuento`. Si `envio > 0`, se agrega la línea "Envío:". El subtotal sigue siendo la suma de las líneas. Los demás llamadores no cambian.
- `actualizar_documento`: si la venta tiene `id_apartado` no nulo, lanza o devuelve el mismo tipo de error que ya usa la función, con el mensaje "Las facturas de pedidos web no se pueden editar." y antes de tocar el stock.
- `obtener_estadisticas`: `ventas_hoy` agrega `AND id_apartado IS NULL`. Nuevos `pedidos_web_hoy` (cantidad) y `pedidos_web_total_hoy` (suma de `total`). `adminPanel` los muestra en una tarjeta igual a las demás.
- Prueba: `_crear_texto_ticket` con `envio=6000, descuento=3500` contiene las dos líneas, y sin esos datos el ticket se ve igual que antes.
