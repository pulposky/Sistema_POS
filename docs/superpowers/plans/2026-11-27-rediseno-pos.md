# Rediseño del POS: plan de implementación

> **Para agentes:** SUB-SKILL REQUERIDO: superpowers:subagent-driven-development (recomendado) o superpowers:executing-plans. Pasos con casillas `- [ ]`.

**Objetivo:** el POS pasa a una sola ventana con menú lateral (plantilla A), con un tema único y las 8 mejoras de lógica, sin romper nada de lo que hoy funciona.

**Arquitectura:** una "carcasa" (`ui/shell.py`) tiene el login, un `ft.NavigationRail` y un área de contenido. Cada sección es una función que devuelve un `Seccion` (contenido + manejador de teclado + al mostrar). La carcasa construye cada sección una vez y la guarda. Modelos y controladores se reutilizan; solo cambian las vistas y lo que piden las mejoras.

**Tecnología:** Python, Flet (0.85.2 → 0.86.5 → 1.1.4), mysql-connector, ReportLab. Pruebas: scripts con asserts en `tests/`.

**Diseño:** `docs/superpowers/specs/2026-11-27-rediseno-pos-design.md` (aprobado 2026-11-27).

## Restricciones globales

- No se toca el esquema de ninguna tabla. Las reglas de `Marketplace/docs/PARA-EL-POS.md` siguen (stock atómico, no tocar tablas web).
- Cada tarea deja el POS usable, pasa los tests y se sube en su propio commit.
- Tests: `.venv\Scripts\python tests\<archivo>.py` desde la raíz del repo; cada uno imprime `OK...`.
- Atajos de Vender: F1 cliente, F2 cobrar, F3 buscar producto, F4 nueva venta / en espera, F5 borrar, F6/F7 → Facturas, F8 crear cliente, F9 → Pedidos web, Esc cierra el diálogo abierto. Ctrl+1…7 = secciones en el orden del menú.
- Colores con significado: verde = cobrar/confirmar, rojo = borrar/anular, ámbar = pendiente.
- Textos en español, frase normal (no Title Case), sin "por favor" ni "exitosamente".
- Prueba en vivo de cada sección: respaldar `tienda_db` (stock, estados de apartados, máximos de venta/detalle_venta/clientes), probar con computer use sobre la ventana real (pedir acceso a la ruta de `flet.exe`, nunca `open_application`), restaurar y verificar que quedó igual.
- La lógica que no es pantalla y es nueva lleva test con asserts.

## Puntos a vigilar (no los cubre ningún test automático salvo donde se indica)

1. Cambiar de sección con una venta a medias y volver: la venta sigue igual (prueba en vivo en la Tarea 7).
2. Dos ventas en espera con el mismo producto y stock justo: al cobrar la segunda sale el aviso de stock y esa venta sigue abierta, sin perderse (prueba en vivo en la Tarea 7).
3. Esc con un diálogo abierto cierra solo el diálogo, nunca la sección ni la sesión (test en la Tarea 5).
4. Facturador con clave de admin equivocada: se queda donde estaba y ve un aviso (prueba en vivo en la Tarea 5).
5. La base se cae mientras el POS está abierto: el contador de pedidos web no rompe la app; la sección muestra un aviso (test en la Tarea 8).

---

### Tarea 1: Flet 0.86.5 sin avisos de obsoleto

**Archivos:** `App/requirements.txt` (y el `requirements.txt` de la raíz si existe), las vistas que den aviso.

- [ ] Instalar `flet==0.86.5` en `.venv` y fijarlo en `requirements.txt`.
- [ ] Lanzar `cd App && ..\.venv\Scripts\python -W default main.py > %TEMP%\pos.log 2>&1` y recorrer con computer use: login, menú, Vender (buscar producto, método de pago, F9), Compras, Remisión, Inventario, Entradas, Consultar facturas, Actualizar facturas, Nuevo usuario, panel Admin.
- [ ] Corregir cada `DeprecationWarning` de Flet que aparezca en el log usando el reemplazo que indica el propio aviso.
- [ ] Repetir el recorrido: el log no tiene `DeprecationWarning` de Flet ni tracebacks. Los 3 tests pasan.
- [ ] Commit `chore: subir Flet a 0.86.5 y quitar APIs obsoletas`.

### Tarea 2: Flet 1.1.4

**Archivos:** `requirements.txt`, lo que rompa.

- [ ] Leer la guía "Migrating from Flet 0.28 to 1.0" y las de 1.0.0 y 1.1.0 en https://flet.dev/docs/updates/breaking-changes/. Anotar en el commit qué cambios afectan a este código (Tabs, Theme, eventos, `InputBorder`).
- [ ] Instalar `flet==1.1.4` (con el extra de escritorio que pida la guía) y fijarlo.
- [ ] Mismo recorrido que la Tarea 1; corregir hasta que no haya tracebacks ni avisos de Flet.
- [ ] Comprobar que `flet build windows` (o el comando del README, "Generar el Ejecutable") sigue funcionando; si cambió, actualizar el README.
- [ ] Commit `chore: subir Flet a 1.1.4`.

### Tarea 3: Tema y componentes comunes

**Archivos:**
- Crear: `App/ui/__init__.py`, `App/ui/tema.py`, `App/ui/componentes.py`
- Test: `tests/test_ui_componentes.py`

**Interfaces:**
- Produce: `crear_tema() -> ft.Theme` (semilla verde SENA `#39A900`, esquinas medianas). `COLOR_COBRAR`, `COLOR_BORRAR`, `COLOR_PENDIENTE` (constantes de color).
- Produce: `aviso(pagina: ft.Page, texto: str, tipo: str = "info") -> None`, con `tipo` en `{"exito", "error", "info"}`; muestra un `ft.SnackBar` (reemplaza a `utils/notificaciones.mostrar_notificacion`, que pasa a llamarlo).
- Produce: `boton_accion(texto: str, icono, al_tocar, atajo: str | None = None, tipo: str = "normal") -> ft.Control`, con `tipo` en `{"normal", "cobrar", "borrar"}`; el texto visible es `"{texto} ({atajo})"` si hay atajo.
- Produce: `confirmar(pagina, mensaje: str, al_responder: Callable[[bool], None]) -> None` (reutiliza `utils/confirmacion.confirmar_view`).

- [ ] Test: `boton_accion("Cobrar", ft.Icons.PAYMENTS, lambda e: None, "F2", "cobrar")` contiene un texto `"Cobrar (F2)"`; sin atajo, el texto es `"Cobrar"`; `tipo="desconocido"` lanza `ValueError`. `crear_tema()` devuelve `ft.Theme` con `color_scheme_seed == "#39A900"`.
- [ ] Ejecutar: falla (no existe `ui`).
- [ ] Implementar `tema.py` y `componentes.py`. `aviso` en una página falsa con `overlay=[]` y `update()` agrega un `SnackBar` abierto.
- [ ] Ejecutar: `OK`. Los otros tests pasan.
- [ ] Commit `feat(ui): tema y componentes comunes`.

### Tarea 4: Documentos en espera

**Archivos:**
- Crear: `App/controllers/esperaController.py`
- Test: `tests/test_espera.py`

**Interfaces:**
- Produce: clase `DocumentosEnEspera` con:
  - `actual -> dict` (el documento en pantalla; empieza como `nuevo()`),
  - `nuevo: Callable[[], dict]` (se pasa al crearla, arma un documento vacío),
  - `poner_en_espera() -> None` (guarda `actual` si tiene líneas y empieza uno nuevo),
  - `retomar(indice: int) -> None` (el documento en espera pasa a `actual`; si `actual` tenía líneas, pasa a espera),
  - `terminar_actual() -> None` (descarta `actual` tras cobrar/guardar y empieza uno nuevo),
  - `en_espera -> list[dict]`, `cuantos_en_espera() -> int`.
  Un documento es un dict con al menos `"productos": list`, `"cliente"`.

- [ ] Test con asserts:
  - poner en espera una venta con 1 línea → `cuantos_en_espera() == 1` y `actual["productos"] == []`;
  - poner en espera una venta vacía → no se guarda (`cuantos_en_espera()` no cambia);
  - retomar 0 con `actual` con líneas → se intercambian (la de pantalla queda en espera);
  - `terminar_actual()` no toca las que están en espera;
  - `retomar(5)` con 1 en espera lanza `IndexError`.
- [ ] Ejecutar: falla. Implementar. Ejecutar: `OK`.
- [ ] Commit `feat: documentos en espera`.

### Tarea 5: Carcasa (una ventana, menú lateral, teclado central)

**Archivos:**
- Crear: `App/ui/shell.py`
- Modificar: `App/main.py` (arranca la carcasa; se mantiene `POS_VIEW` hasta la Tarea 12), `App/views/login.py` (devuelve `Seccion`, al entrar llama `al_entrar(usuario)`)
- Test: `tests/test_shell.py`

**Interfaces:**
- Produce en `ui/shell.py`:
  - `@dataclass Seccion(contenido: ft.Control, al_teclado: Callable[[ft.KeyboardEvent], bool] | None = None, al_mostrar: Callable[[], None] | None = None, puede_salir: Callable[[], str | None] | None = None)`. `al_teclado` devuelve True si usó la tecla. `puede_salir` devuelve un texto de advertencia (ej. ventas en espera) o None.
  - `@dataclass Contexto(pagina, usuario: dict, ir_a: Callable[..., None], pedir_admin: Callable[[Callable[[dict], None]], None])`.
  - `ITEMS_MENU`: lista ordenada de `(clave, texto, icono, solo_admin)`: `vender`, `pedidos_web`, `facturas`, `inventario`, `compras`, `remisiones`, `entradas` (admin), `admin` (admin), y al final `soporte` y `salir`.
  - `items_visibles(rol: str) -> list[tuple[clave, bloqueado: bool]]`: admin ve todo sin candado; facturador ve todo y `entradas`/`admin` con `bloqueado=True`.
  - `class Shell(pagina)`: `registrar(clave, fabrica: Callable[[Contexto], Seccion])`, `ir_a(clave, **kw)`, `mostrar_login()`, `poner_contador(clave, n: int | None)`.
- Reglas de `Shell`:
  - Ventana maximizada al abrir (`pagina.window.maximized = True`), tema de `crear_tema()`.
  - `ir_a` construye la sección la primera vez y la reutiliza después; llama `al_mostrar` cada vez.
  - Ítem bloqueado → `pedir_admin` (usa `utils/solicitarAdmin.solicitar_password_admin`); con clave correcta entra; mal o cancelado, se queda y `aviso(..., "error")` si fue error.
  - Teclado: si hay un diálogo abierto en `pagina.overlay`/`pagina.dialog`, Esc lo cierra y nada más. Ctrl+1…7 → `ir_a` del ítem visible en esa posición. Lo demás va a `al_teclado` de la sección activa.
  - `salir`: junta `puede_salir()` de las secciones construidas; si alguna devuelve texto, pide `confirmar`; al salir se borran las secciones guardadas y vuelve al login.
  - Mientras una vista vieja no esté rehecha, su fábrica es un adaptador que llama a la vista vieja (ver Tarea 6).

- [ ] Test: `items_visibles("admin")` no tiene bloqueados y trae `entradas`; `items_visibles("facturador")` marca `entradas` y `admin` como bloqueados; `items_visibles("otro")` lanza `PermissionError`. Con una página falsa: `ir_a("vender")` dos veces llama a la fábrica una sola vez y `al_mostrar` dos veces; Esc con un diálogo abierto lo cierra y no llama a `al_teclado`; `salir` con una sección cuyo `puede_salir` devuelve texto no vuelve al login hasta confirmar.
- [ ] Ejecutar: falla. Implementar. Ejecutar: `OK`.
- [ ] En vivo: login → entra a Vender; menú lateral funciona; facturador con clave equivocada se queda y ve aviso.
- [ ] Commit `feat(ui): ventana única con menú lateral`.

### Tarea 6: Vistas viejas dentro de la carcasa

**Archivos:** `App/views/{vender,comprar,remision,inventario,entradas,consultarFacturas,actualizarFacturas,crearUsuario,adminPanel}.py`, `App/utils/{buscarProducto,buscarCliente,buscarProveedor,metodoPago,crearP_C,entregarApartado,solicitarAdmin}.py`, `App/routers/navegacion.py`.

**Interfaces:**
- Consume: `Seccion`, `Contexto`, `Shell.registrar` (Tarea 5).
- Cambio mecánico en cada vista: la firma pasa a `nombre(contexto: Contexto) -> Seccion`. En vez de `pagina.clean(); pagina.add(X)` devuelve `Seccion(contenido=X, al_teclado=teclado)`. Se quitan `pagina.window.width/height`. Donde llamaba `ir_a_menu(usuario)` llama `contexto.ir_a("vender")`. Los diálogos de `utils/` que pisan `pagina.on_keyboard_event` dejan de hacerlo (Esc lo maneja la carcasa).
- `routers/navegacion.py` pasa a registrar las fábricas en la carcasa; `views/menu.py` e `views/inicio.py` dejan de usarse y se borran.
- Antes de borrar `inicio.py`, su diálogo "Soporte" (descargar manual de usuario y manual técnico con FilePicker) pasa a `App/ui/soporte.py` como `abrir_soporte(pagina: ft.Page) -> None`; el ítem `soporte` del menú lo llama (no es una sección).
- F4 sigue abriendo otra ventana (`abrir_nueva_instancia`) hasta las Tareas 7 y 11.

- [ ] Aplicar el cambio a cada vista y diálogo.
- [ ] `grep -rn "pagina.clean()\|pagina.window.width\|on_keyboard_event =" App/views App/utils` solo encuentra `ui/shell.py`.
- [ ] Tests pasan. Recorrido en vivo de todas las secciones sin tracebacks.
- [ ] Commit `refactor(ui): vistas dentro de la ventana única`.

### Tarea 7: Vender nuevo

**Archivos:**
- Modificar: `App/views/vender.py` (se rehace la pantalla), `App/controllers/ventasController.py` si hace falta
- Test: `tests/test_vender_logica.py`

**Interfaces:**
- Consume: `DocumentosEnEspera` (Tarea 4), `aviso`, `boton_accion` (Tarea 3), `Seccion` (Tarea 5).
- Produce: `vender(contexto) -> Seccion` con `puede_salir` que devuelve `"Tienes N ventas en espera."` si `N > 0`.
- `ventasController.imprimir_o_ofrecer_pdf(id_venta: int, usuario: dict) -> tuple[bool, str | None]`: intenta imprimir; si falla, genera el PDF con `generar_factura_pdf(..., abrir=False)` y devuelve `(False, ruta_pdf)`.

- [ ] Test: `imprimir_o_ofrecer_pdf` con `imprimir_factura_datos` forzado a fallar devuelve `(False, ruta)` y el archivo existe (carpeta temporal como en `test_ticket_y_panel.py`); con impresión correcta devuelve `(True, None)`.
- [ ] Ejecutar: falla. Implementar. Ejecutar: `OK`.
- [ ] Pantalla: buscador grande arriba con foco (nombre o código; Enter agrega; código exacto agrega directo), tabla de líneas (presentación en desplegable, cantidad editable, quitar), pestañas de ventas en espera arriba de la tabla, panel derecho con cliente, subtotal, descuento, total grande y `boton_accion("Cobrar", ..., "F2", "cobrar")`.
- [ ] F4: primera vez con líneas → `poner_en_espera()`; las pestañas permiten `retomar`. Se quita `abrir_nueva_instancia` de Vender.
- [ ] F6/F7 → `contexto.ir_a("facturas")`. F9 → `contexto.ir_a("pedidos_web")`. Se borra `modo_consulta` y todo lo de consulta de esta vista (`cargar_factura`, `siguiente_factura`, `anterior_factura`, `imprimir_factura_consultada`, `borrar_factura_actual`).
- [ ] Todo `print` dirigido al cajero pasa a `aviso`. Si el ticket no se imprime: aviso con botón "Abrir PDF".
- [ ] En vivo (con respaldo): venta Caja x10; poner en espera, ir a Inventario y volver (la venta sigue); dos ventas en espera con el mismo producto y stock justo (la segunda avisa y sigue abierta); restaurar.
- [ ] Commit `feat(vender): pantalla nueva con ventas en espera`.

### Tarea 8: Pedidos web y Nequi

**Archivos:**
- Crear: `App/views/pedidosWeb.py` (a partir de `utils/entregarApartado.py`, que se borra)
- Modificar: `App/models/ventasModel.py:996` (`_METODO_PAGO_POS`), `App/utils/metodoPago.py`, `tests/test_entrega_pedido.py`
- Test: `tests/test_entrega_pedido.py`, `tests/test_pedidos_contador.py`

**Interfaces:**
- Produce: `pedidos_web(contexto) -> Seccion`; `contar_pedidos_por_entregar() -> int | None` en `ventasModel` (None si la base falla; no lanza).
- La carcasa llama `poner_contador("pedidos_web", contar_pedidos_por_entregar())` al iniciar sesión, al entregar y cada 60 s con `pagina.run_task`.

- [ ] Test: en `test_entrega_pedido.py` cambiar la aserción de la línea 113 a `metodo == 'Nequi'` y agregar un pedido con `metodo_pago='efectivo'` → `'Efectivo'`. En `test_pedidos_contador.py`: con `conectar` falso que lanza excepción, `contar_pedidos_por_entregar()` devuelve `None`; con una base falsa que devuelve 3 pedidos, devuelve 3.
- [ ] Ejecutar: falla. Implementar (`'nequi': 'Nequi'`; `contar_pedidos_por_entregar` = `len(obtener_pedidos_por_entrega())` con try/except y el comentario `# shortcut: trae los pedidos completos para contarlos; si son cientos, cambiar a un COUNT`). Ejecutar: `OK`.
- [ ] `metodoPago.py`: "Nequi" como opción aparte que funciona como Transferencia por el total. Mixto no cambia.
- [ ] Sección: lista y detalle como hoy el diálogo, "Entregar e imprimir" con el mismo aviso de "Abrir PDF" de la Tarea 7. Ítem del menú con el contador en ámbar.
- [ ] En vivo (con respaldo): entregar el pedido #31 ($37.500, guarda "Nequi"); el contador baja en 1; restaurar.
- [ ] Commit `feat: sección de pedidos web, contador y Nequi`.

### Tarea 9: Facturas

**Archivos:**
- Crear: `App/views/facturas.py` (une `consultarFacturas.py` y `actualizarFacturas.py`, que se borran)
- Test: los existentes

**Interfaces:**
- Consume: `ventasController.cargar_factura`, `ajustes_venta_web`, `imprimir_o_ofrecer_pdf` (Tarea 7), `actualizarDocumentosModel` (sin cambios).
- Produce: `facturas(contexto) -> Seccion`.

- [ ] Lista con filtros (los mismos de `consultarFacturas.py`). Abrir una factura la muestra en solo lectura con total guardado (envío y cupón en ventas web, como hoy en Vender).
- [ ] Botones: "Reimprimir", "Editar" (admin directo; facturador con clave de admin; bloqueado en ventas web como hoy) y "Anular" (rojo, con `confirmar`). En solo lectura no existe botón de cobrar.
- [ ] En vivo (con respaldo): consultar una venta web y una normal, reimprimir sin impresora (sale "Abrir PDF"), editar como facturador con clave; restaurar.
- [ ] Commit `feat(facturas): consulta y edición en una sección`.

### Tarea 10: Inventario y Entradas

**Archivos:** `App/views/inventario.py`, `App/views/entradas.py`.

- [ ] Rehacer con los componentes comunes, misma funcionalidad. Los `print` al usuario pasan a `aviso`.
- [ ] En vivo: buscar producto, exportar informe, registrar una entrada (con respaldo); restaurar.
- [ ] Commit `feat(ui): inventario y entradas`.

### Tarea 11: Compras y Remisiones

**Archivos:** `App/views/comprar.py`, `App/views/remision.py`.

**Interfaces:** Consume `DocumentosEnEspera` (Tarea 4), igual que Vender.

- [ ] Rehacer con los componentes comunes; F4 usa documentos en espera (se quita `abrir_nueva_instancia` de las dos). `puede_salir` avisa si hay en espera.
- [ ] En vivo (con respaldo): una compra y una remisión, cada una con una segunda en espera; restaurar.
- [ ] Commit `feat(ui): compras y remisiones con documentos en espera`.

### Tarea 12: Admin y limpieza final

**Archivos:**
- Modificar: `App/views/adminPanel.py` (sección; "Nuevo usuario" dentro de la pestaña Usuarios, usando `views/crearUsuario.py`)
- Borrar: `App/utils/abrirNuevaVentana.py`, lectura de `POS_VIEW`/`POS_USUARIO` en `App/main.py`, `App/utils/notificaciones.py` si ya nadie lo usa
- Modificar: `README.md` (atajos, flujo de una ventana, versión de Flet), manuales en `docs/` si nombran pantallas viejas

- [ ] Admin como sección; admin entra directo, facturador con candado y clave.
- [ ] `grep -rn "abrir_nueva_instancia\|POS_VIEW\|menu_view\|inicio_view" App` no encuentra nada.
- [ ] Todos los tests pasan; recorrido en vivo de todas las secciones como admin y como facturador sin tracebacks.
- [ ] Commit `refactor: quitar ventanas aparte y pantallas viejas; README`.
