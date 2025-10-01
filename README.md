# 🏪 App-Stock - Sistema de Gestión de Inventario y Ventas

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![Tests](https://img.shields.io/badge/tests-20%20passed-brightgreen.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

Sistema completo de gestión de inventario, ventas y reportes con exportación a PDF/Excel e impresión de tickets.

## ✨ Características Principales

- 🛍️ **Gestión de Productos** - CRUD completo con búsqueda y control de stock
- 💰 **Sistema de Ventas** - Carrito intuitivo con cálculo automático de totales
- 📊 **Reportes Profesionales** - Exportación a PDF y Excel con gráficos
- 🎫 **Tickets de Venta** - Generación e impresión automática
- ❌ **Anulación de Ventas** - Cancelación con reintegro de stock
- ➕ **Artículos Varios** - Venta de productos no registrados
- 🎨 **Interfaz Moderna** - Diseño profesional con ttkbootstrap

## 🚀 Instalación Rápida

### Opción 1: Instalador Automático (Recomendado)

```bash
# Descargar el instalador desde releases
# Ejecutar App-Stock-Installer-v1.0.exe como administrador
# ¡Listo! Todo se configura automáticamente
```

### Opción 2: Instalación Manual

```bash
# Clonar repositorio
git clone https://github.com/EzequielPedulla/App-stock.git
cd App-stock

# Crear entorno virtual e instalar dependencias
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configurar base de datos
cp .env.example .env
# Editar .env con tus credenciales MySQL

# Crear base de datos
mysql -u root -p -e "CREATE DATABASE app_stock;"

# Ejecutar
python main.py
```

## 🛠️ Stack Tecnológico

**Backend:** Python 3.11+ • PyMySQL • python-dotenv  
**Frontend:** tkinter • ttkbootstrap  
**Reportes:** ReportLab • OpenPyXL • Matplotlib  
**Testing:** pytest • pytest-cov • pytest-mock  
**Distribución:** PyInstaller • Inno Setup

## 📊 Funcionalidades Detalladas

### Gestión de Productos

- ✅ Agregar, editar, eliminar productos
- ✅ Control de stock automático
- ✅ Búsqueda por código de barras
- ✅ Alertas de stock bajo

### Sistema de Ventas

- ✅ Carrito de compras intuitivo
- ✅ Cálculo automático de totales
- ✅ Tickets de venta en PDF
- ✅ Impresión directa
- ✅ Artículos "Varios" para productos no registrados

### Reportes y Exportación

- ✅ Reportes completos con gráficos
- ✅ Exportación a PDF y Excel
- ✅ Historial de ventas
- ✅ Anulación de ventas con reintegro de stock

## 🧪 Tests

```bash
# Ejecutar tests
pytest

# Con cobertura
pytest --cov=app

# Tests específicos
pytest tests/test_export_service.py -v
pytest tests/test_cancel_sale.py -v
```

## 📁 Estructura del Proyecto

```
App-Stock/
├── app/
│   ├── controllers/    # Lógica de negocio
│   ├── models/         # Modelos y base de datos
│   ├── services/       # Exportación PDF/Excel
│   └── views/          # Interfaz gráfica
├── tests/              # Suite de tests
├── docs/               # Documentación
├── installers/         # Scripts de instalación
├── imagenes/           # Recursos gráficos
└── main.py             # Punto de entrada
```



### Para Desarrolladores

- Clona el repositorio
- Instala dependencias
- Configura base de datos
- Ejecuta `python main.py`

### Para Usuarios Finales

- Descarga `App-Stock-Installer-v1.0.exe`
- Ejecuta como administrador
- ¡Listo para usar!

## 📖 Documentación

- [Instrucciones de Instalación](docs/INSTRUCCIONES.txt)
- [Guía de Creación de Instalador](docs/COMO_CREAR_INSTALADOR.txt)


## 👨‍💻 Autor

**Ezequiel Pedulla**

- GitHub: [@EzequielPedulla](https://github.com/EzequielPedulla)
- Proyecto: [App-Stock](https://github.com/EzequielPedulla/App-stock)

