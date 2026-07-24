# 🛒 Sistema POS y Gestión de Inventario

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flet](https://img.shields.io/badge/GUI-Flet-violet.svg)](https://flet.dev/)
[![MySQL](https://img.shields.io/badge/Database-MySQL-orange.svg)](https://www.mysql.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Sistema integral de Punto de Venta (POS), gestión de compras, emisión de remisiones y control de inventario en tiempo real desarrollado en Python con Flet y MySQL.

---

## 🚀 Guía de Instalación y Configuración

Sigue estos pasos para clonar, configurar y ejecutar el proyecto en tu entorno local.

### 📋 Requisitos Previos

Asegúrate de tener instalado en tu equipo:

- **Git** ([Descargar Git](https://git-scm.com/))
- **Python 3.10** o superior ([Descargar Python](https://www.python.org/downloads/))
- **Servidor MySQL** (Recomendado: **Laragon** corriendo en el puerto `3306`)

---

### 1️⃣ Clonar el Repositorio

Abre la terminal o consola de comandos y ejecuta:

```bash
git clone https://github.com/tu-usuario/tu-repositorio.git
cd tu-repositorio
```

---

### 2️⃣ Configurar la Base de Datos

1. Inicia tu servidor MySQL (Laragon ).
2. Abre tu gestor de base de datos (phpMyAdmin).
3. Importa el archivo  `database.sql` incluido en la carpeta database. Este archivo:

   - Crea la base de datos por defecto (`pos_db`).
   - Crea todas las 10 tablas requeridas con sus llaves primarias y foráneas.
   - Crea un usuario administrador inicial (`admin` / `admin123`) y el cliente general.
4. Verifica las credenciales de conexión en `App/database/bd.py`:

```python
# Configuración en App/database/bd.py
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "pos_db") # Cambiar si se usa un nombre personalizado
```

---

### 3️⃣ Crear el Entorno Virtual e Instalar Dependencias

Es una buena práctica utilizar un entorno virtual para aislar las dependencias del proyecto.

#### En Windows (PowerShell):

```powershell
# Crear el entorno virtual
python -m venv venv

# Activar el entorno virtual
.\venv\Scripts\Activate.ps1

# Instalar las librerías necesarias
pip install -r App/requirements.txt
```

#### En Linux / macOS (Bash / Zsh):

```bash
# Crear el entorno virtual
python3 -m venv venv

# Activar el entorno virtual
source venv/bin/activate

# Instalar las librerías necesarias
pip install -r App/requirements.txt
```

---

### 4️⃣ Ejecutar la Aplicación

Con el entorno virtual activado y MySQL en ejecución, inicia la aplicación desde la raíz del proyecto:

```bash
python App/main.py
```

---

## 🛠️ Solución de Problemas Frecuentes (FAQ)

| Problema                                        | Causa Posible                                                              | Solución                                                                                                                       |
| :---------------------------------------------- | :------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------ |
| `Error de conexión a la base de datos`       | El servicio MySQL está apagado o las credenciales no coinciden            | Asegúrate de que MySQL en Laragon/XAMPP esté iniciado y revisa el archivo`App/database/bd.py`.                              |
| `Script Execution Disabled` (PowerShell)      | Política de ejecución restringida en Windows                             | Ejecuta en PowerShell:`Set-ExecutionPolicy Unrestricted -Scope Process` y luego reactiva con `.\venv\Scripts\Activate.ps1`. |
| `ModuleNotFoundError: No module named 'flet'` | El entorno virtual no está activado o no se instalaron los requerimientos | Activa el entorno virtual (`.\venv\Scripts\Activate.ps1`) y vuelve a correr `pip install -r App/requirements.txt`.          |

---

## 📁 Estructura del Proyecto

```text
Proyecto/
├── App/
│   ├── main.py              # Punto de entrada principal
│   ├── requirements.txt     # Librerías dependientes
│   ├── database/            # Conexión a MySQL
|   ├── docs/                # Manuales (tecnico y de usuario)
│   ├── models/              # Consultas y persistencia de datos (SQL)
│   ├── controllers/         # Reglas y lógica de negocio
│   ├── views/               # Interfaces de usuario con Flet
│   ├── routers/             # Navegación y enrutamiento entre pantallas
│   └── utils/               # Generador PDF, reportes Excel y modales
└── README.md                # Guía de presentación e instalación para GitHub
```

---

## 👥 Contribuciones y Soporte

Para más detalles sobre la arquitectura interna, modelos de datos y flujo de trabajo, consulta el archivo `MANUAL_TECNICO.pdf`
