# Presentaciones en el POS (diseño corto)

**Para qué:** que el POS venda por Caja, Par, Rollo, etc. igual que la tienda web, con un solo stock
(`producto.stock` en unidad mínima), y quitar la regla adivinada de "huevos ×30".

**Fuera de alcance:** crear o editar presentaciones desde el POS (eso se hace en la tienda).
La pantalla F9 por pedido completo es la parte 3.

## Enfoques considerados
- **Columna "Presentación" en la tabla de venta** (elegido por el usuario): entra en Unidad
  sin preguntar y se cambia en la fila. No agrega pasos.
- Ventanita al agregar con F3: es rápida con el teclado, pero suma un paso en cada venta.
- Una fila por presentación en el buscador F3: alarga la lista.

## Cómo funciona
- Al agregar un producto se leen sus presentaciones activas
  (`producto_presentacion` con `activo = 1`, ordenadas por `orden`).
- La fila tiene un desplegable solo si el producto tiene presentaciones. La primera opción
  siempre es la unidad mínima (factor 1, con el nombre de `producto.unidad`). Si ya existe
  una presentación con factor 1, se usa esa en vez de repetirla.
- Precio de la fila = precio por unidad con la oferta vigente × factor (igual que el carrito web).
- Stock que se descuenta = cantidad × factor, de forma atómica (parte 1).
- El aviso de stock de la pantalla también compara cantidad × factor.
- Las líneas de un pedido web (F9) no cambian: siguen en unidad mínima y sin descontar stock.

## Decisiones mías (revísalas)
- `detalle_venta` guarda la cantidad en **unidad mínima** y el precio **por unidad mínima**
  (2 cajas ×10 → 20 und a $4.500). Así no se agregan columnas y los totales y reportes cuadran.
  El ticket de la venta en curso muestra "2 Caja x10". Una factura consultada después se verá
  como "20 und".
- Se borra la detección de huevos por nombre (×30). En `tienda_db` no hay productos de huevos.
