"""Configuración del paquete para desarrollo."""
from setuptools import setup, find_packages

setup(
    name="app-stock",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "ttkbootstrap>=1.10.1",
        "sqlite3",
    ],
    python_requires=">=3.8",
    author="Eze",
    description="Aplicación de gestión de inventario y ventas",
    keywords="inventory, sales, management",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "Programming Language :: Python :: 3.8",
    ],
)
