@echo off
title App-Stock - Sistema de Inventario

echo ========================================
echo    INICIANDO APP-STOCK...
echo ========================================
echo.

echo Verificando MySQL...
mysql --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: MySQL no esta disponible
    echo.
    echo SOLUCION:
    echo 1. Inicie XAMPP Control Panel
    echo 2. Haga clic en "Start" junto a MySQL
    echo 3. Vuelva a ejecutar este archivo
    echo.
    pause
    exit /b 1
)

echo MySQL OK - Iniciando aplicacion...
echo.

REM Verificar si existe archivo de configuracion
if not exist ".env" (
    echo Archivo de configuracion no encontrado.
    echo Ejecutando configuracion automatica...
    call configurar.bat
    if %errorlevel% neq 0 (
        echo Error en la configuracion. Verifique las instrucciones.
        pause
        exit /b 1
    )
)

echo Iniciando App-Stock...
start "" "App-Stock.exe"

echo.
echo Aplicacion iniciada correctamente.
echo Puede cerrar esta ventana.
timeout /t 3 >nul
