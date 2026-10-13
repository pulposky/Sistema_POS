<h1 align="center">🖥️ Sistema POS</h1>
<h3 align="center">Punto de venta, compras, remisiones e inventario en tiempo real</h3>

<p align="center">
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10%2B-blue.svg" alt="Python"></a>
  <a href="https://flet.dev/"><img src="https://img.shields.io/badge/GUI-Flet%20v0.85-violet.svg" alt="Flet"></a>
  <a href="https://www.mysql.com/"><img src="https://img.shields.io/badge/Database-MySQL-orange.svg" alt="MySQL"></a>
  <a href="#-plataforma"><img src="https://img.shields.io/badge/Platform-Windows-0078D6.svg" alt="Windows"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License MIT"></a>
</p>

<p align="center">
  <b>El POS de escritorio que trabaja de la mano con tu tienda en línea.</b><br>
  Vende en mostrador, gestiona tu inventario al instante y entrega las
  reservas hechas en el <b>Marketplace Web</b>, todo desde una sola aplicación.
</p>

---

## 📑 Tabla de Contenidos

- [✨ ¿Qué es este sistema?](#-qué-es-este-sistema)
- [💡 Beneficios](#-beneficios)
- [🚀 Características principales](#-características-principales)
- [🌐 Integración con el Marketplace Web](#-integración-con-el-marketplace-web)
- [👥 Roles y permisos](#-roles-y-permisos)
- [⌨ Atajos de teclado](#-atajos-de-teclado)
- [🧰 Tecnologías](#-tecnologías)
- [💻 Plataforma](#-plataforma)
- [🚀 Guía de Instalación y Configuración](#-guía-de-instalación-y-configuración)
- [📦 Generar el Ejecutable (.exe)](#-generar-el-ejecutable-exe)
- [📁 Estructura del Proyecto](#-estructura-del-proyecto)
- [📚 Manuales](#-manuales)
- [🛠 Solución de Problemas Frecuentes (FAQ)](#-solución-de-problemas-frecuentes-faq)
- [👥 Soporte y Contribuciones](#-soporte-y-contribuciones)

---

## ✨ ¿Qué es este sistema?

Es un sistema integral de **Punto de Venta (POS), gestión de compras,
emisión de remisiones y control de inventario en tiempo real**. Fue construido en
**Python** con **Flet** para ofrecer una interfaz moderna de escritorio y **MySQL**
como motor de datos.

Nació pensado para el trabajo diario de una caja real: **rápido, con atajos de teclado,
multiusuario y con documentos listos para imprimir**. Además, está **vinculado al
[Marketplace Web](https://github.com/pulposky/Marketplace)**, la tienda en línea donde
tus clientes reservan productos: ambos comparten la misma base de datos, por lo que el
inventario y los clientes se mantienen **sincronizados** entre el mostrador y la web.

> 🎯 **En una frase:** vende, compra, entrega y controla tu inventario desde un solo
> lugar, sin descuadres y sin doble digitación.

---

## 💡 Beneficios

- ⚡ **Caja ultrarrápida** — Todo el flujo de venta funciona con atajos de teclado (F1–F9): buscar cliente, agregar producto, facturar, entregar reservas y más.
- 📦 **Inventario siempre exacto** — El stock se calcula en tiempo real sumando entradas y compras y restando ventas y remisiones.
- 🧾 **Documentos profesionales** — Facturas, comprobantes de compra y remisiones en **PDF de 58 mm** y **ticket térmico** para impresoras de recibos.
- 🌐 **Un solo inventario para web y tienda** — Las reservas del Marketplace se convierten en ventas presenciales con un clic.
- 👥 **Multiusuario con roles** — Admin, Aprendiz y Consultas, con contraseñas **cifradas con bcrypt**.
- 📊 **Reportes en Excel** — Exporta inventario y documentos filtrados con un solo atajo.
- 🪟 **Multi-ventana** — Abre varias ventas o compras a la vez sin detener lo que estás haciendo.
- 🧩 **Fácil de desplegar** — Empaquétalo como un único `.exe` y llévalo a cualquier equipo.

---

## 🚀 Características principales

### 🧾 Facturación / Punto de venta
- Búsqueda de productos por nombre o **código** y de clientes, con selección de cantidad.
- Edición **en línea** de cantidad y descuento directamente sobre la tabla.
- Cálculo automático de **subtotal, descuento y total** en tiempo real.
- Múltiples **métodos de pago**: Transferencia, Efectivo, Mixto y Crédito, con notas por empresa.
- Generación de **PDF** y **ticket térmico** de la factura.
- Consulta de facturas guardadas y navegación entre ellas (F6/F7), impresión y anulación con permisos.
- **Entrega de apartados web** reservados en el Marketplace (F9).
- Creación rápida de productos o clientes desde el mismo diálogo (F8).

### 🛒 Compras
- Registro de compras por **proveedor** con la misma agilidad de la venta.
- Actualización automática de inventario y costos.
- Comprobante en PDF/ticket, consulta, impresión y anulación con permisos.

### ♻️ Remisiones
- Emisión de remisiones por **cliente** y **tipo/motivo** (incluye "Retiro Transformación" con notas).
- Conteo de productos y cantidades, sin manejo de precios.
- Impresión y consulta de remisiones históricas.

### 📦 Inventario
- **Stock calculado en tiempo real** (entradas + compras − ventas − remisiones).
- Barra superior con usuario y hora, y recarga instantánea (F5).
- Exportación del informe completo a **Excel**.

### ➕ Entradas de inventario
- Suma de stock por compras, devoluciones u otros movimientos **sin alterar precios ni costos**.

### 🔍 Consulta de documentos
- Filtros por tipo (Venta, Compra, Remisión, Todos), número, cliente/proveedor, usuario, rango de fechas y producto.
- Vista **normal** (una fila por documento) y **detallada** (una fila por producto vendido).
- Exportación de los resultados filtrados a **Excel** (F2).

### ✏️ Actualización de documentos
- Edición de documentos existentes para corregir errores sin perder trazabilidad.

### 👤 Usuarios y seguridad
- Creación de usuarios con asignación de rol.
- **Login con contraseña cifrada (bcrypt)** y control granular por rol.
- **Acceso asistido para Aprendices:** los botones reservados al administrador
  (Entradas, Nuevo Usuario y Actualizar Facturas) solicitan la **contraseña de un
  administrador** antes de permitir el acceso.

---

## 🌐 Integración con el Marketplace Web

Este sistema se conecta con el **[Marketplace Web](https://github.com/pulposky/Marketplace)**
(Node.js + Express + EJS), una plataforma de **reserva en línea** de productos agrícolas
y procesados. Ambos sistemas **comparten la misma base de datos MySQL** (`pos_db`),
lo que permite sincronizar inventario y clientes entre el canal en línea y las
transacciones presenciales.

| POS 🖥️ (este sistema)                        | Marketplace 🌐 (Node.js)                          |
| :------------------------------------------- | :----------------------------------------------- |
| Pago presencial y facturación                | Reserva en línea de productos                    |
| Gestión de inventario, compras y remisiones  | Catálogo público con búsqueda y filtros          |
| Código de producto y búsqueda rápida         | Sistema de apartados con notificaciones          |
| Registro de ventas y control de caja         | Dashboard de estadísticas y registro de visitas  |

### 🔄 Flujo de una reserva en línea

```text
Cliente reserva en la Web  →  Apartado (pendiente/confirmado)
        →  Cajero abre "Apartado [F9]" en el POS
        →  Se precarga el producto reservado
        →  Se factura: el apartado pasa a "entregado"
        →  Inventario sincronizado en ambos canales
```

### Reparto de tablas compartidas

| Tabla      | Uso en el POS               | Uso en el Marketplace         |
| :--------- | :-------------------------- | :---------------------------- |
| `usuarios` | Login de cajeros            | Login de admin y empleados    |
| `clientes` | Consumidor final en ventas  | Registro de clientes que reservan |
| `producto` | Inventario físico (`stock`) | Stock en línea (`limite_venta`) |
| `apartados` | Entrega de reservas (F9)   | Reservas generadas por el cliente |
| `notificaciones` | Alertas para el admin  | Avisos del sistema            |

### Instalación conjunta

1. Ejecuta el `database.sql` de este POS para crear todas las tablas.
2. Clona el Marketplace y ejecuta su `schema.sql` — no borra nada (`CREATE TABLE IF NOT EXISTS`).
3. Si la web se instaló primero, ejecuta el bloque de `ALTER TABLE` incluido al final del
   `database.sql` de este POS (o las migraciones de `App/database/migrations/`) para agregar
   la columna `limite_venta` y las tablas de la web.

---

## 👥 Roles y permisos

| Rol | Acceso |
| :--- | :--- |
| **Admin / Administrador** | Acceso total: facturación, compras, remisiones, inventario, entradas, usuarios, consultas y actualización de documentos. |
| **Aprendiz** | Facturación, compras, remisiones, inventario y consultas. Las funciones exclusivas del admin (Entradas, Nuevo Usuario y Actualizar Facturas) piden la **contraseña de un administrador** para entrar. No puede anular documentos. |
| **Consultas** | Solo la pantalla de **Consultar Facturas**; el resto de módulos queda bloqueado. |

> 🔐 La contraseña se valida con **bcrypt** contra la de cualquier usuario administrador
> registrado, y se solicita **cada vez** que el Aprendiz intenta abrir una función restringida.

---

## ⌨ Atajos de teclado

Pensado para operar sin soltar el teclado, como en una caja de supermercado.

### Facturación (`F1`–`F9`)

| Tecla | Acción |
| :---: | :--- |
| `F1` | Buscar cliente |
| `F2` | Facturar (confirmar venta) |
| `F3` | Buscar producto |
| `F4` | Nueva factura (1.ª vez limpia · 2.ª vez abre nueva ventana) |
| `F5` | Borrar / anular factura |
| `F6` / `F7` | Siguiente / anterior factura guardada |
| `F8` | Crear producto o cliente |
| `F9` | Entregar apartado web |
| `Esc` | Volver al menú principal |

### Compras y Remisiones

| Tecla | Acción |
| :---: | :--- |
| `F1` | Buscar proveedor / cliente |
| `F2` | Confirmar compra / generar remisión |
| `F3` | Buscar producto |
| `F4` | Nuevo documento (o abrir en ventana nueva) |
| `F5` | Borrar / anular documento |
| `F6` / `F7` | Siguiente / anterior documento guardado |
| `F8` | Crear producto, proveedor o cliente |

### Inventario y Consultas

| Tecla | Acción |
| :---: | :--- |
| `F5` | Recargar la lista |
| `F2` | Exportar a Excel (en Consultar Facturas) |
| `Esc` | Volver al menú principal |

> En el menú y las pantallas de bienvenida también puedes navegar con `↑` / `↓`.

---

## 🧰 Tecnologías

| Componente | Tecnología |
| :--- | :--- |
| Lenguaje | **Python 3.10+** |
| Interfaz de escritorio | **Flet 0.85** |
| Base de datos | **MySQL** (`mysql-connector-python`) |
| Seguridad | **bcrypt** (contraseñas cifradas) |
| PDF de recibos (58 mm) | **ReportLab** + **Pillow** |
| Ticket térmico | **win32print** / **python-escpos** |
| Reportes | **openpyxl** (Excel) |
| Configuración | **python-dotenv** |
| Empaquetado | **PyInstaller** |

---

## 💻 Plataforma

- **Sistema operativo:** Windows (por la impresión térmica directa y el empaquetado `.exe`).
- **Requisitos:** Python 3.10+ y un servidor **MySQL** local (Laragon, XAMPP, etc.).
- **Opcional:** impresora térmica de recibos **XPrinter XP-58C** (o compatible de 58 mm).

---

## 🚀 Guía de Instalación y Configuración

Sigue estos pasos para clonar, configurar y ejecutar el proyecto en tu entorno local.

### 📋 Requisitos Previos

- **Git** ([Descargar Git](https://git-scm.com/))
- **Python 3.10** o superior ([Descargar Python](https://www.python.org/downloads/))
- **Servidor MySQL** — cualquiera de estos funciona:
  - **Laragon** (recomendado): inicia el servicio MySQL desde el botón "Start All".
  - **XAMPP**: inicia el servicio MySQL desde el panel de control (botón "Start" junto a MySQL).

> ⚠️ Si usas **XAMPP** y también tienes **Laragon** instalado, asegúrate de que solo uno
> esté corriendo a la vez, ya que ambos usan el puerto `3306` por defecto.

### 1️⃣ Clonar el Repositorio

```bash
git clone https://github.com/pulposky/Sistema_POS.git
cd Sistema_POS
```

### 2️⃣ Configurar la Base de Datos

1. Inicia tu servidor MySQL (Laragon o XAMPP).
2. Abre phpMyAdmin en tu navegador (`http://localhost/phpmyadmin`).
3. Importa el archivo `App/database/database.sql` (pestaña **Importar**). Este archivo crea:
   - La base de datos `pos_db`.
   - Todas las tablas con sus llaves primarias y foráneas.
   - Un usuario administrador inicial (`admin` / `admin123`) y el cliente general.
4. Verifica las credenciales de conexión en `App/database/bd.py`:

```python
# Configuración en App/database/bd.py
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")  # Laragon: vacío | XAMPP: vacío por defecto
DB_NAME = os.getenv("DB_NAME", "pos_db")
DB_PORT = int(os.getenv("DB_PORT", "3306"))  # Ambos usan 3306 por defecto
```

> 💡 Si tu usuario `root` tiene contraseña, crea un archivo `.env` en la raíz del proyecto:
>
> ```ini
> DB_HOST=localhost
> DB_USER=root
> DB_PASSWORD=tu_contraseña
> DB_NAME=pos_db
> DB_PORT=3306
> ```

> 📝 El nombre de la base de datos (`pos_db`) es configurable: debes usar **el mismo**
> nombre en tu `App/database/database.sql`, en `bd.py` y en tu archivo `.env`.

### 3️⃣ Crear el Entorno Virtual e Instalar Dependencias

**Windows (PowerShell):**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r App/requirements.txt
```

**Linux / macOS (Bash / Zsh):**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r App/requirements.txt
```

### 4️⃣ Ejecutar la Aplicación

Con el entorno virtual activado y MySQL en ejecución:

```bash
python App/main.py
```

---

## 📦 Generar el Ejecutable (.exe)

Para distribuir el sistema sin que el usuario final instale Python, el proyecto incluye
el archivo `App/main.spec` con la configuración de **PyInstaller**. El ejecutable se
genera a partir de ese archivo (puedes ajustar su nombre dentro de `main.spec`).

```bash
pip install pyinstaller
pyinstaller App/main.spec
```

El ejecutable resultante quedará en `dist/` y los archivos temporales en `build/`.

---

## 📁 Estructura del Proyecto

```text
Proyecto/
├── App/
│   ├── assets/               # Recursos gráficos (íconos, imágenes)
│   ├── main.py                # Punto de entrada principal
│   ├── requirements.txt       # Librerías dependientes
│   ├── database/              # Conexión a MySQL, database.sql y migraciones
│   ├── docs/                  # Manuales (técnico y de usuario)
│   ├── models/                # Consultas y persistencia de datos (SQL)
│   ├── controllers/           # Reglas y lógica de negocio
│   ├── views/                 # Interfaces de usuario con Flet
│   ├── routers/               # Navegación y enrutamiento entre pantallas
│   └── utils/                 # Generador PDF, reportes Excel y modales
└── README.md                  # Esta guía
```

---

## 📚 Manuales

Desde la pantalla de bienvenida, el botón **"Soporte"** permite descargar:

- 📘 **Manual de Usuario** (`App/docs/Manual_de_Usuario_Sistema_POS.pdf`)
- 📗 **Manual Técnico** (`App/docs/Manual_Tecnico.pdf`)

---

## 🛠 Solución de Problemas Frecuentes (FAQ)

| Problema | Causa posible | Solución |
| :--- | :--- | :--- |
| `Error de conexión a la base de datos: 2003 ... Can't connect to MySQL server` | MySQL no está corriendo | Inicia el servicio MySQL (Laragon/XAMPP) y verifica que nada más use el puerto 3306. |
| `Error de conexión: Unknown database 'pos_db'` | La base de datos no fue creada | Importa `App/database/database.sql` en phpMyAdmin. |
| `Access denied for user 'root'@'localhost'` | La contraseña de root no coincide | Actualiza `DB_PASSWORD` en `bd.py` o crea el archivo `.env`. |
| `Puerto 3306 en uso` | Laragon y XAMPP corriendo a la vez | Detén uno de los dos; solo puede haber un MySQL en el puerto 3306. |
| `Script Execution Disabled` (PowerShell) | Política de ejecución restringida | `Set-ExecutionPolicy Unrestricted -Scope Process` y reactiva el entorno. |
| `ModuleNotFoundError: No module named 'flet'` | Entorno virtual inactivo o sin dependencias | Activa el entorno (`.\.venv\Scripts\Activate.ps1`) y corre `pip install -r App/requirements.txt`. |
| El Aprendiz no puede abrir Entradas / Nuevo Usuario / Actualizar Facturas | Funciones reservadas al admin | Ingresa la **contraseña de un administrador** cuando el sistema la solicite. |

---

## 👥 Soporte y Contribuciones

¿Ideas, mejoras o reportes de errores? Abre un **Issue** o envía un **Pull Request**.
Para detalles de la arquitectura interna, modelos de datos y flujo de trabajo, consulta
el `Manual_Tecnico.pdf` incluido en `App/docs/`.

<p align="center">
  Hecho con 💚 en <b>Python + Flet + MySQL</b> · vinculado al
  <a href="https://github.com/pulposky/Marketplace">Marketplace Web</a>.
</p>
