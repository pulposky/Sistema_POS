# Presentaciones en el POS: plan de implementación

> **Para agentes:** usar superpowers:executing-plans. Pasos con casillas `- [ ]`.

**Objetivo:** vender por presentación (Caja x10, Par...) con precio = precio unidad × factor y stock -= cantidad × factor.

**Arquitectura:** la fila de venta (dict en `productos`) gana `factor`, `presentaciones` y `precio_unidad`.
La celda "Unidad" de la tabla (columna 3) pasa a ser un desplegable cuando hay presentaciones.
El modelo convierte a unidad mínima al guardar.

**Tecnología:** Python, Flet y mysql-connector. La prueba es un script con asserts (`tests/`).

**Diseño:** `docs/superpowers/specs/2026-11-26-presentaciones-pos-design.md`

## Restricciones generales
- No se toca el esquema de ninguna tabla.
- Stock atómico: `UPDATE ... WHERE stock >= ?` (ya existe, parte 1).
- Las líneas `es_apartado` no cambian: siguen en unidad mínima y no descuentan stock.

## Revisión: casos a vigilar
1. Un producto sin presentaciones: la fila funciona igual que antes (factor 1, sin desplegable).
2. Cambiar la presentación con un descuento manual ya puesto: el subtotal respeta el descuento.
3. Un producto con oferta vigente: el precio de la caja es el precio con oferta × factor.
4. Un producto cuyas presentaciones no tienen factor 1: igual se puede vender por unidad (se agrega como primera opción).
5. Pasarse de stock por factor (3 cajas x10 con stock 25): la fila muestra el aviso y el guardado se rechaza.

---

### Tarea 1: Modelo y controlador

**Archivos:**
- Modificar: `App/models/ventasModel.py`. Agregar `obtener_presentaciones` y, en `guardar_factura`, quitar la regla de huevos ×30 y usar el factor.
- Modificar: `App/controllers/ventasController.py`. Cambiar `agregar_producto_a_venta` y `obtener_stock_restante`, y agregar `cambiar_presentacion`.
- Prueba: `tests/test_guardar_factura.py`

**Interfaces:**
- `ventasModel.obtener_presentaciones(id_producto: int) -> list[dict]` con `{'nombre': str, 'factor': int}`.
  Lee las presentaciones activas ordenadas por `orden` y devuelve `[]` si hay un error.
- `ventasController.cambiar_presentacion(producto: dict, factor: int) -> dict`. Toma el nombre
  de `producto['presentaciones']` y fija `factor`, `unidad`=nombre, `precio`=`precio_unidad`×factor,
  `precio_original`=`precio_original_unidad`×factor y recalcula el `subtotal` con el descuento manual.
- `agregar_producto_a_venta`: si la línea no es `es_apartado`, carga `presentaciones`. La primera opción es
  `{'nombre': unidad, 'factor': 1}`, a menos que ya exista una con factor 1. También fija `factor=1`,
  `precio_unidad` y `precio_original_unidad`.
- `obtener_stock_restante`: `stock - cantidad * factor`.
- `guardar_factura`: `unidades = cantidad * factor`. En el detalle, la cantidad va en unidades y `precio_unitario` es `subtotal / unidades`.

- [ ] Pruebas nuevas (asserts):
  - `cambiar_presentacion`: precio 4500, caja ×10, cantidad 2 y descuento 10 % → precio 45000 y subtotal 81000.
  - `guardar_factura`: una línea con factor 10 y cantidad 2, con stock 25 → queda en 5 y el detalle guarda 20.
  - Lo mismo con cantidad 3 → None y el stock sigue en 25.
  - `obtener_stock_restante` con stock 25, cantidad 3 y factor 10 → -5.
- [ ] Ejecutar: fallan.
- [ ] Implementar.
- [ ] Ejecutar `.venv/Scripts/python tests/test_guardar_factura.py` → `OK`.

### Tarea 2: Pantalla de vender

**Archivos:** modificar `App/views/vender.py`. Cambiar el encabezado de la columna 3 a "Presentación" y la celda 3 en
`agregar_producto_a_tabla` y `eliminar_producto` (las dos reconstrucciones de fila).

- [ ] Agregar `crear_celda_presentacion(producto, index)`: si `len(presentaciones) > 1`, muestra un `ft.Dropdown` con las opciones
  "nombre" y valor `factor`. `on_select`/`on_change` llama a `cambiar_presentacion` y redibuja las celdas 3, 4 (precio),
  6 (subtotal) y 8 (acciones), y luego `actualizar_totales()`. Si no hay presentaciones, deja el texto de `unidad`, como ahora.
- [ ] Verificar: compila y, en la app real, agregar "Bisagra cierre lento" y cambiarla a Caja x10. El precio se multiplica por 10 y el total se actualiza.
