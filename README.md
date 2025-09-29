# 🏪 Sistema de Gestión de Inventario y Ventas

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

---

## 🚀 Instalación y Configuración

### 1. Clonar el repositorio

```bash
git clone <repository-url>
cd App-Stock
```

### 2. Crear entorno virtual

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Crea un archivo `.env` en la raíz del proyecto con:

```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=tu_contraseña_aquí
MYSQL_DATABASE=app_stock
```

> ⚠️ **IMPORTANTE**: Nunca subas el archivo `.env` al repositorio. Ya está incluido en `.gitignore`.

### 5. Crear la base de datos

```sql
CREATE DATABASE app_stock;
```

Las tablas se crearán automáticamente al iniciar la aplicación.

### 6. Ejecutar la aplicación

```bash
python main.py
```
