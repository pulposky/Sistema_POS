# Rediseño del POS: diseño

Fecha: 2026-11-27. Estado: aprobado por el usuario el 2026-11-27. Repo: `Proyecto` (POS de escritorio en Python + Flet, base `tienda_db` compartida con la tienda web).

## Intención

El usuario quiere el POS "más bonito, más rápido y más entendible para el usuario", siguiendo con Flet,
actualizando la versión si hace falta y usando sus controles propios. Eligió la **plantilla A**
(una sola ventana con menú lateral) y las **8 mejoras de lógica** propuestas. Eligió construirlo
**por secciones**: primero la ventana nueva, después cada pantalla, reutilizando la lógica probada.

Quien lo usa: cajeros (rol `facturador`) y administradores (`admin`/`administrador`) en el mostrador,
con teclado y a veces lector de código de barras, en Windows.

## Objetivos

1. Una sola ventana. Se cambia de sección sin abrir otro proceso ni cerrar sesión.
2. Aspecto moderno y uniforme: un tema único, iconos, tamaños de letra legibles, colores con significado
   (verde = cobrar, rojo = borrar/anular, ámbar = pendiente).
3. Más rápido: nada de `subprocess` para abrir pantallas; las secciones ya visitadas no se reconstruyen
   desde cero cada vez.
4. Más entendible: cada acción da una respuesta visible en pantalla; los atajos se ven en los botones.
5. Las 8 mejoras de lógica (abajo), todas.

## No objetivos

- No cambia la base de datos ni las reglas del negocio: stock atómico, presentaciones, F9 por pedido
  completo, ventas web aparte en el panel. Las reglas de `Marketplace/docs/PARA-EL-POS.md` siguen igual.
- No se reescriben modelos ni controladores salvo lo que pidan las 8 mejoras.
- No se hace versión táctil, web ni móvil.
- No se crean ni editan presentaciones desde el POS (eso es de la tienda).

## Anti-objetivos (fracaso aunque "funcione")

- Que una venta tarde más pasos o más teclas que hoy.
- Que se rompa algo que hoy funciona: el stock, F9, las presentaciones, la reimpresión o los PDF.
- Que el POS quede sin poder usarse mientras dura el cambio.

## Restricciones

- Flet hoy está en 0.85.2; la última es 1.1.4. La 1.0 quitó las APIs obsoletas y cambió Tabs, Theme
  y el manejo de eventos ([guía oficial](https://flet.dev/docs/updates/breaking-changes/)).
  Ruta: subir a la última 0.86.x, correr la app y corregir cada aviso de obsoleto; luego pasar a 1.1.x.
- El POS se sigue empaquetando como .exe (README, "Generar el Ejecutable").
- Las pruebas son scripts con asserts en `tests/` (`.venv\Scripts\python tests\x.py`). Siguen pasando en cada paso.
- Cada paso deja el POS usable y se sube por separado.

## Formas consideradas

1. **Ventana nueva y pantallas rehechas una por una (elegida).** Primero la ventana con menú lateral, el
   tema y los avisos; después cada sección. Se reutilizan los modelos y controladores que ya tienen tests.
   Poco riesgo y avance visible; durante la transición conviven pantallas nuevas y viejas.
2. **Todo de nuevo de una vez.** Queda uniforme desde el primer día, pero son semanas sin poder usarlo y
   hay mucho riesgo de romper stock, F9 o presentaciones. Descartada.
3. **Solo cambiar la apariencia.** Es lo más rápido, pero no da la ventana única ni la velocidad, y no
   resuelve la mayoría de las mejoras. Descartada.

## Diseño

### La ventana (plantilla A)

```
┌────────────┬───────────────────────────────────────┬──────────────┐
│ [logo]     │ Barra: sección · usuario · hora        │              │
│ Vender     │───────────────────────────────────────│  Panel de    │
│ Pedidos web│  Contenido de la sección               │  la sección  │
│  (8)       │                                        │  (en Vender: │
│ Facturas   │                                        │  cliente,    │
│ Inventario │                                        │  totales,    │
│ Compras    │                                        │  Cobrar F2)  │
│ Remisiones │                                        │              │
│ Entradas*  │                                        │              │
│ Admin*     │                                        │              │
│ ─────────  │                                        │              │
│ Salir      │                                        │              │
└────────────┴───────────────────────────────────────┴──────────────┘
* solo para admin
```

- Menú lateral con `ft.NavigationRail` (icono + texto). Cambiar de sección cambia el contenido de la
  derecha; la ventana no se cierra.
- Al abrir: pantalla de inicio de sesión centrada (logo, usuario, contraseña, Ingresar). Después del login
  se entra directo a **Vender**. Se eliminan la pantalla de bienvenida (SenaEmpresa / Administración /
  Soporte) y el menú de botones; "Soporte" pasa a un ítem del menú (mi decisión: hoy es un botón aparte
  en la bienvenida).
- La ventana abre maximizada y recuerda su tamaño mínimo (mejora 5).
- Tema único en `ft.Theme` (color semilla verde SENA, tipografía del sistema, esquinas redondeadas medianas),
  definido en un solo archivo. Modo claro (mi decisión: hoy es claro y es mostrador con luz).
- Cada sección es un objeto que se construye una vez y se guarda; volver a ella la muestra tal como quedó
  (una venta a medias no se pierde al ir a Inventario y volver). Mi decisión.

### Atajos de teclado

Un solo manejador de teclado en la ventana, que reenvía la tecla a la sección activa. Se mantienen los
atajos actuales de Vender (F1 cliente, F2 cobrar, F3 buscar producto, F4 nueva venta, F5 borrar,
F6/F7 consultar, F8 crear cliente, F9 pedidos web, Esc volver/cerrar diálogo). Ctrl+1…7 salta a cada sección
(mi decisión). Cada botón muestra su atajo.

- **F4 "nueva venta"**: hoy la segunda vez abre otra ventana. Pasa a abrir una **venta en espera**: la venta
  actual se guarda en una lista de "ventas abiertas" (pestañas pequeñas arriba de la tabla) y se empieza una
  vacía. Así se atiende a otro cliente sin perder la primera, que es lo que hoy resuelve la segunda ventana.
  Mi decisión.
- El mismo mecanismo de "documentos en espera" sirve para **Compras y Remisiones**, que hoy también abren
  otra ventana con el segundo F4 (`comprar.py:533`, `remision.py:717`). Es un solo componente compartido, no tres.
  Lo decidió el usuario.
- Lo que está en espera vive solo en memoria. Si al salir o cerrar hay documentos en espera, se pregunta
  antes ("Tienes 2 ventas en espera. ¿Salir igual?"). Lo decidió el usuario.
- **F6/F7** en Vender llevan a la sección Facturas. Vender deja de tener su propio "modo consulta"
  (`modo_consulta` en `vender.py` se elimina); la consulta de solo lectura vive solo en Facturas. Lo decidió el usuario.

### Secciones

| Sección | Qué cambia |
|---|---|
| Vender | Buscador grande arriba (nombre o código, Enter agrega; lector de código de barras = escribir + Enter). Tabla de líneas con presentación en desplegable, cantidad editable, quitar línea. Panel derecho: cliente, subtotal, descuento, total grande, botón Cobrar (F2). |
| Pedidos web | Hoy es el diálogo F9. Pasa a sección propia con la misma lista y detalle, y "Entregar e imprimir". F9 desde Vender salta aquí. |
| Facturas | Une "Consultar facturas" y "Actualizar facturas": lista con filtros; abrir una factura la muestra **solo lectura**; "Editar" (admin) y "Anular" son botones aparte (mejora 7). |
| Inventario, Compras, Remisiones, Entradas | Misma función que hoy con el layout y los componentes nuevos. |
| Admin | El panel actual (indicadores, usuarios, productos, respaldo) como sección. Visible solo para admin. "Nuevo usuario" queda dentro de Admin → Usuarios. |

### Componentes comunes (un solo archivo de UI compartida)

- `aviso(texto, tipo)`: barra de aviso abajo (éxito, error, info). Reemplaza los `print` dirigidos al usuario.
- `confirmar(...)`: diálogo de confirmación.
- `tabla(...)`: tabla con encabezado fijo y desplazamiento.
- `boton_accion(texto, icono, atajo, tipo)`: botón con su atajo visible.
- Los diálogos actuales de `utils/` (buscar producto, buscar cliente, método de pago, crear cliente/proveedor)
  se pasan a este estilo cuando se toca la sección que los usa.

### Las 8 mejoras de lógica

1. **Una sola ventana**: se quita `utils/abrirNuevaVentana.py` y la lectura de `POS_VIEW`/`POS_USUARIO` en `main.py`.
2. **Admin sin cerrar sesión**: si el usuario conectado es admin, entra a "Admin", "Entradas" y "Editar factura"
   directo. Un facturador ve esos ítems con un candado; al tocarlos sale el diálogo de contraseña de admin actual
   (`solicitarAdmin`) y, si es correcta, entra (como hoy con `admin_authorized=True`). Lo decidió el usuario.
3. **Mensajes visibles**: todo `print` que hoy avisa algo al cajero (unos 40, en `views/` y `utils/`) pasa a
   `aviso(...)`. Los `print` de depuración se quedan.
4. **Sin impresora**: si el ticket no se pudo imprimir, el aviso lo dice y ofrece "Abrir PDF" (genera el PDF
   con `generar_factura_pdf` y lo abre con el visor del sistema).
5. **Ventana maximizada** al abrir; se quitan los `pagina.window.width/height` de cada vista.
6. **Contador de pedidos web** en el ítem "Pedidos web" del menú. Se actualiza al entrar a la sección, al
   entregar un pedido y cada 60 s (mi decisión; un pedido nuevo puede llegar mientras el cajero vende).
7. **Consultar ≠ editar**: abrir una factura vieja nunca deja el botón Cobrar activo.
8. **Nequi**: el método de pago "Nequi" existe en el POS (además de Efectivo, Transferencia, Mixto, Crédito) y
   la entrega F9 guarda "Nequi" tal cual, en vez de convertirlo a "Transferencia" (`ventasModel._METODO_PAGO_POS`).
   Los indicadores del panel que suman transferencias cuentan también Nequi. Mixto sigue siendo efectivo +
   transferencia (no incluye Nequi). El ticket y el PDF muestran el nombre del método tal cual. Las ventas ya
   guardadas como "Transferencia" no se tocan. Lo decidió el usuario.

### Orden de trabajo (cada paso se sube por separado y deja el POS usable)

1. Subir Flet a 0.86.x y corregir avisos de obsoleto; luego a 1.1.x. Probar que todas las pantallas actuales abren.
2. Ventana nueva: login, menú lateral, tema, componentes comunes, teclado central. Las secciones aún no
   rehechas se muestran con su vista actual dentro del área de contenido. Para eso cada vista vieja recibe un
   cambio mecánico y pequeño: en vez de `pagina.clean()` + `pagina.add(...)` devuelve su contenido, quita sus
   `pagina.window.width/height` y registra su manejador de teclado en el central en lugar de pisar
   `pagina.on_keyboard_event`. Lo mismo con los diálogos de `utils/` que lo hacen. Este paso es más grande que
   los demás por eso.
3. Vender (con ventas en espera y mejoras 3, 4 y 7 para esa pantalla).
4. Pedidos web (mejoras 6 y 8).
5. Facturas.
6. Inventario, Compras, Remisiones, Entradas.
7. Admin (mejora 2) y limpieza final: quitar `inicio.py`, `menu.py`, `abrirNuevaVentana.py`, `POS_VIEW`.
   Actualizar README (atajos, capturas) y manuales.

## Pruebas

- Los tests actuales (`test_guardar_factura`, `test_entrega_pedido`, `test_ticket_y_panel`) pasan en cada paso.
- Tests nuevos con asserts para la lógica nueva que no es pantalla: ventas en espera (guardar, recuperar,
  cobrar una sin tocar la otra), el contador de pedidos web, y la conversión de método de pago con Nequi.
- Cada sección se prueba en vivo con computer use sobre la ventana real, igual que la prueba del
  2026-11-27, con respaldo y restauración de `tienda_db`.

## Lo que queda al constructor

- Nombres de archivos y carpetas de la UI nueva, respetando `views/`, `controllers/`, `models/`, `utils/`.
- Los colores exactos dentro del tema, siempre que verde/rojo/ámbar tengan el significado de arriba.
- Cómo se ve cada diálogo, dentro del estilo común.
