@echo off
title Crear Instalador App-Stock
color 0B

echo.
echo ========================================
echo    CREANDO INSTALADOR APP-STOCK
echo ========================================
echo.

echo Este script creara el instalador automatico
echo que incluye XAMPP y toda la configuracion.
echo.

echo [1/3] Verificando archivos necesarios...
if not exist "App-Stock.exe" (
    echo ERROR: App-Stock.exe no encontrado
    echo Copie el ejecutable desde la carpeta dist/
    pause
    exit /b 1
)

if not exist "App-Stock-Installer.iss" (
    echo ERROR: App-Stock-Installer.iss no encontrado
    pause
    exit /b 1
)

echo Archivos OK

echo.
echo [2/3] Verificando Inno Setup...
where iscc >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Inno Setup no esta instalado
    echo.
    echo SOLUCION:
    echo 1. Descargue Inno Setup desde: https://jrsoftware.org/isinfo.php
    echo 2. Instale Inno Setup
    echo 3. Vuelva a ejecutar este script
    echo.
    pause
    exit /b 1
)

echo Inno Setup OK

echo.
echo [3/3] Compilando instalador...
iscc "App-Stock-Installer.iss"
if %errorlevel% neq 0 (
    echo ERROR: No se pudo compilar el instalador
    echo Verifique que todos los archivos esten presentes
    pause
    exit /b 1
)

echo.
echo ========================================
echo    INSTALADOR CREADO EXITOSAMENTE
echo ========================================
echo.
echo El instalador se encuentra en:
echo %CD%\App-Stock-Installer-v1.0.exe
echo.
echo Este archivo puede ser distribuido a los clientes.
echo Contiene todo lo necesario para instalar App-Stock.
echo.
pause
