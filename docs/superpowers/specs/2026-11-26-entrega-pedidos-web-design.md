# Entrega de pedidos web completos en el POS (F9), diseño corto

**Para qué:** el POS trabaja conectado a la tienda. El cajero entrega en un solo paso un
pedido web **ya pagado**, con todas sus líneas, y la factura del POS da el mismo total que cobró la tienda.

**Fuera de alcance:** cobrar dinero en F9 (el pedido ya está pagado), confirmar pagos o cancelar
pedidos (eso se hace en la tienda), y agregar productos de pasillo a la misma factura (se hace una venta aparte).

## Enfoques considerados
- **Ventana propia de entrega** (elegido por el usuario): lista de pedidos a la izquierda, detalle a la
  derecha y botón "Entregar e imprimir". No toca la tabla de venta.
- Cargar el pedido en la tabla de venta bloqueada: se parece a lo que el cajero ya conoce, pero cambia mucho `vender.py`.
- Lista simple con confirmación: es la más rápida, pero el cajero no ve los productos antes de entregar.

## Qué pedidos aparecen
- Los que tienen al menos una línea `confirmado` y **ninguna** `pendiente`. Las líneas canceladas se muestran tachadas o se omiten.
- Orden: los más antiguos primero. Un campo busca por número de pedido o por nombre del cliente.

## Detalle y total (las mismas cuentas que la tienda)
- Por línea: cantidad = `cantidad / presentacion_factor` + `presentacion_nombre` (si no tiene presentación, unidades),
  y precio c/u = `precio_aplicado × factor`.
- Total = suma de las líneas vivas (`precio_aplicado × cantidad`) − mín(esa suma, `pedidos.descuento`) + `pedidos.costo_envio`.
- Se muestran: cliente, entrega (recoger o domicilio con dirección y teléfono), forma de pago, cupón y envío.

## Al entregar (una sola transacción)
1. Se bloquean la fila de `pedidos` y sus `apartados` (`FOR UPDATE`) y **se vuelve a calcular todo desde la base**,
   no con lo que muestra la pantalla. Si hay alguna línea `pendiente` o ninguna `confirmado` (alguien la cambió
   en la web), se cancela todo con un mensaje claro.
2. Envío y cupón: se aplican solo si **ninguna** línea del pedido está ya `entregado`, para no cobrarlos dos veces.
3. Se inserta en `venta` con `total` = total calculado; `metodo_pago`: nequi → "Transferencia", efectivo → "Efectivo"
   y cualquier otro → "Transferencia"; `dinero_recibido` = total y `cambio` = 0. El cliente es el del pedido si existe
   en `clientes`; si no, el genérico (1), con el nombre del pedido en la nota. `id_apartado` = la primera línea confirmada.
   La nota es corta: "Pedido web #N".
4. Un `detalle_venta` por línea confirmada, en unidad mínima, con precio por unidad = `precio_aplicado`.
   **No descuenta stock.** Si el factor es nulo o 0, se trata como 1.
5. `UPDATE apartados SET estado = 'entregado' WHERE id_pedido = ? AND estado = 'confirmado'`, y commit.
6. Se imprime **después** del commit. Si la impresora falla, la venta queda guardada y se reimprime con F6/F7.

## Panel de administración (decidido por el usuario)
- Las estadísticas de ventas o caja **excluyen** las ventas con `id_apartado`. Se muestra aparte
  "Pedidos web entregados" (cantidad y monto), para que la caja cuadre con el efectivo físico.

## Protecciones en otras pantallas
- Editar una factura con `id_apartado` (actualizar documentos) queda **bloqueado** con un mensaje.
  Esa edición devuelve y vuelve a descontar stock que el POS nunca descontó.
- El ticket y el PDF reciben `envio` y `descuento` (por defecto 0, así las otras pantallas no cambian) y los muestran.
- Anular (F5) solo marca la venta como ANULADA (ya es así); el pedido sigue entregado en la tienda.
- El informe de inventario cuenta la entrega como venta. Es correcto: la tienda ya descontó ese stock, así que el
  informe cuadra con `producto.stock`.

## Decisiones mías (revísalas)
- El envío y el cupón quedan en el total y en la nota de la venta, no como líneas: `detalle_venta` exige un producto real.
  Por eso, en las facturas de pedidos web, la suma de las líneas puede no coincidir con el total.
- El cliente se busca en `clientes` por `pedidos.id_cliente` (la tabla es compartida). Si no tiene, se usa el genérico (1).
- Se reemplaza `utils/entregarApartado.py` y la ruta actual por línea suelta (`es_apartado`) deja de usarse en F9.
