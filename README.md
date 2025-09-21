# 🏪 Sistema de Gestión de Inventario y Ventas

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)

**Una aplicación moderna y completa para la gestión de inventario y ventas de pequeñas y medianas empresas.**

[Características](#-características) • [Instalación](#-instalación) • [Uso](#-uso) • [Capturas](#-capturas) • [Tecnologías](#-tecnologías)

</div>

---

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Instalación](#-instalación)
- [Configuración](#-configuración)
- [Uso](#-uso)
- [Capturas de Pantalla](#-capturas-de-pantalla)
- [Tecnologías](#-tecnologías)
- [Arquitectura](#-arquitectura)
- [Contribuir](#-contribuir)
- [Licencia](#-licencia)

---

## ✨ Características

### 🛍️ **Gestión de Productos**

- ➕ **Agregar productos** con código de barras, nombre, precio y stock
- ✏️ **Editar productos** existentes
- 🗑️ **Eliminar productos** del inventario
- 📋 **Lista completa** con búsqueda y filtros
- 🔍 **Búsqueda por código de barras** o nombre

### 💰 **Sistema de Ventas**

- 🛒 **Carrito de compras** intuitivo
- 📊 **Cálculo automático** de totales y subtotales
- 💳 **Múltiples métodos de pago** (efectivo)
- 🧾 **Cálculo de vuelto** automático
- ✏️ **Editar cantidades** en tiempo real
- 🗑️ **Eliminar productos** del carrito
- 📈 **Control de stock** en tiempo real

### 🎨 **Interfaz de Usuario**

- 🖥️ **Diseño moderno** con ttkbootstrap
- 🌙 **Tema profesional** (Flatly)
- 📱 **Interfaz intuitiva** y fácil de usar
- 🎯 **Navegación por pestañas** (Productos/Ventas)
- ⚡ **Responsive** y optimizada

### 🗄️ **Base de Datos**

- 🐬 **MySQL** para almacenamiento robusto
- 🔗 **Relaciones bien estructuradas** (Productos, Ventas, Detalles)
- 📊 **Integridad referencial** garantizada
- 🔄 **Transacciones** seguras

---

## 🚀 Instalación

### Prerrequisitos

- **Python 3.8+**
- **MySQL Server 5.7+**
- **Git**

### 1. Clonar el repositorio

```bash
git clone https://github.com/EzequielPedulla/App-stock.git
cd App-stock
```

### 2. Crear entorno virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Instalar dependencias de desarrollo (opcional)

```bash
pip install -r requirements-dev.txt
```

---

## ⚙️ Configuración

### 1. Configurar MySQL

Crea una base de datos MySQL:

```sql
CREATE DATABASE app_stock;
```

### 2. Configurar variables de entorno

Crea un archivo `.env` en la raíz del proyecto:

```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=tu_password
MYSQL_DATABASE=app_stock
```

### 3. Ejecutar la aplicación

```bash
python main.py
```

---

## 🎯 Uso

### Gestión de Productos

1. **Agregar Producto:**

   - Ingresa código de barras, nombre, precio y stock
   - Haz clic en "Guardar"

2. **Editar Producto:**

   - Selecciona un producto de la lista
   - Haz clic en "Editar"
   - Modifica los datos y guarda

3. **Eliminar Producto:**
   - Selecciona un producto de la lista
   - Haz clic en "Eliminar"
   - Confirma la eliminación

### Proceso de Venta

1. **Agregar Productos:**

   - Ingresa el código de barras del producto
   - Especifica la cantidad
   - Presiona Enter o haz clic en "Agregar"

2. **Gestionar Carrito:**

   - Edita cantidades haciendo clic en "Editar"
   - Elimina productos con "Eliminar"
   - El total se calcula automáticamente

3. **Finalizar Venta:**
   - Haz clic en "Confirmar Venta"
   - Ingresa el monto pagado
   - El sistema calcula el vuelto automáticamente

---

## 📸 Capturas de Pantalla

### Pantalla Principal

```
┌─────────────────────────────────────────────────────────────┐
│  🏪 Sistema de Gestión de Inventario                        │
├─────────────────┬───────────────────────────────────────────┤
│  📦 Productos   │  Agregar Producto                         │
│  💰 Ventas      │  ┌─────────────────────────────────────┐  │
│                 │  │ Código: [123456789012]              │  │
│                 │  │ Nombre: [Producto]                  │  │
│                 │  │ Precio: [10.50]                     │  │
│                 │  │ Stock:  [100]                       │  │
│                 │  └─────────────────────────────────────┘  │
│                 │  Lista de Productos                      │
│                 │  ┌─────────────────────────────────────┐  │
│                 │  │ Código    │ Nombre │ Precio │ Stock │  │
│                 │  │ 123456... │ Prod1  │ $10.50 │  100  │  │
│                 │  └─────────────────────────────────────┘  │
└─────────────────┴───────────────────────────────────────────┘
```

---

## 🛠️ Tecnologías

### Backend

- **Python 3.8+** - Lenguaje principal
- **PyMySQL** - Conector MySQL
- **tkinter** - Framework GUI base

### Frontend

- **ttkbootstrap** - Componentes modernos
- **Custom CSS** - Estilos personalizados

### Base de Datos

- **MySQL 5.7+** - Sistema de gestión de base de datos

### Desarrollo

- **pytest** - Testing framework
- **ruff** - Linter y formatter
- **coverage** - Cobertura de código

---

## 🏗️ Arquitectura

El proyecto sigue el patrón **MVC (Model-View-Controller)**:

```
app/
├── models/          # Modelos de datos
│   ├── product.py   # Modelo Producto
│   └── database.py  # Conexión BD
├── views/           # Interfaces de usuario
│   ├── main_window.py    # Ventana principal
│   ├── product_form.py   # Formulario productos
│   ├── product_list.py   # Lista productos
│   └── sale_form.py      # Formulario ventas
├── controllers/     # Lógica de negocio
│   ├── product_controller.py
│   └── sale_controller.py
└── __init__.py
```

### Características de la Arquitectura

- ✅ **Separación clara** de responsabilidades
- ✅ **Código reutilizable** y mantenible
- ✅ **Fácil testing** de componentes
- ✅ **Escalabilidad** para futuras funcionalidades

---

## 🧪 Testing

Ejecutar tests:

```bash
# Tests unitarios
pytest

# Tests con cobertura
pytest --cov=app

# Tests específicos
pytest tests/test_integration.py
```

---

## 🚀 Roadmap

### Próximas Funcionalidades

- [ ] 📊 **Reportes y Analytics**
- [ ] 👥 **Sistema de Usuarios**
- [ ] 🏷️ **Categorías de Productos**
- [ ] 📱 **API REST**
- [ ] 🐳 **Docker Support**
- [ ] 📈 **Dashboard Analytics**

---

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

---

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

---

## 👨‍💻 Autor

**Ezequiel Pedulla**

- GitHub: [@EzequielPedulla](https://github.com/EzequielPedulla)
- Email: tu-email@ejemplo.com

---

## 🙏 Agradecimientos

- [ttkbootstrap](https://github.com/israel-dryer/ttkbootstrap) - Por los componentes modernos
- [PyMySQL](https://github.com/PyMySQL/PyMySQL) - Por el conector MySQL
- Comunidad Python - Por el apoyo y recursos

---

<div align="center">

**⭐ Si te gusta este proyecto, ¡dale una estrella! ⭐**

</div>
