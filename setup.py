"""Configuración del paquete para desarrollo."""
from setuptools import setup, find_packages

setup(
    name="app-stock",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        # Aquí irían las dependencias principales del proyecto
    ],
    python_requires=">=3.8",
)
