# 🏪 App Stock - Sistema de Gestión de Inventario y Ventas

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![Tests](https://img.shields.io/badge/tests-20%20passed-brightgreen.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

Sistema completo de gestión de inventario, ventas y reportes con exportación a PDF/Excel e impresión de tickets.

## ✨ Características Principales

- 🛍️ **Gestión de Productos** - CRUD completo con búsqueda y control de stock
- 💰 **Sistema de Ventas** - Carrito intuitivo con cálculo automático de totales
- 📊 **Reportes Profesionales** - Exportación a PDF y Excel con gráficos
- 🎫 **Tickets de Venta** - Generación e impresión automática
- 🎨 **Interfaz Moderna** - Diseño profesional con ttkbootstrap

## 🚀 Instalación Rápida

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

## 📊 Exportación de Reportes

### PDF

- Reportes completos con gráficos de productos más vendidos
- Tickets individuales de venta
- Impresión directa a impresora predeterminada

### Excel

- Historial de ventas completo
- Inventario con resaltado de stock bajo
- Formato profesional con colores y bordes

## 🧪 Tests

```bash
# Ejecutar tests
pytest

# Con cobertura
pytest --cov=app

```

## 📁 Estructura

```
App-Stock/
├── app/
│   ├── controllers/    # Lógica de negocio
│   ├── models/         # Modelos y base de datos
│   ├── services/       # Exportación PDF/Excel
│   └── views/          # Interfaz gráfica
├── tests/              # Suite de tests
├── reportes/           # PDFs y Excel generados
└── main.py             # Punto de entrada
```
