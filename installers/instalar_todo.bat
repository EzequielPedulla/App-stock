@echo off
title Instalador App-Stock - Configuracion Automatica
color 0A

echo.
echo ========================================
echo    INSTALADOR APP-STOCK AUTOMATICO
echo ========================================
echo.
echo Este instalador configurara todo automaticamente:
echo - XAMPP (MySQL + Apache)
echo - Base de datos App-Stock
echo - Configuracion de la aplicacion
echo.
echo Tiempo estimado: 5-10 minutos
echo.

set /p continuar="¿Desea continuar? (S/N): "
if /i "%continuar%" neq "S" (
    echo Instalacion cancelada.
    pause
    exit /b 0
)

echo.
echo [1/6] Verificando permisos de administrador...
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Se requieren permisos de administrador
    echo Haga clic derecho en este archivo y seleccione "Ejecutar como administrador"
    pause
    exit /b 1
)
echo Permisos OK

echo.
echo [2/6] Descargando XAMPP...
if not exist "xampp-windows-x64-8.2.12-0-VS16-installer.exe" (
    echo Descargando XAMPP desde Apache Friends...
    powershell -Command "& {Invoke-WebRequest -Uri 'https://sourceforge.net/projects/xampp/files/XAMPP%20Windows/8.2.12/xampp-windows-x64-8.2.12-0-VS16-installer.exe' -OutFile 'xampp-windows-x64-8.2.12-0-VS16-installer.exe'}"
    if %errorlevel% neq 0 (
        echo ERROR: No se pudo descargar XAMPP
        echo Descargue manualmente desde: https://www.apachefriends.org/
        pause
        exit /b 1
    )
)
echo XAMPP descargado

echo.
echo [3/6] Instalando XAMPP...
echo Instalando XAMPP en C:\xampp...
xampp-windows-x64-8.2.12-0-VS16-installer.exe --mode unattended --unattendedmodeui none --debuglevel 2 --installer-language en --prefix C:\xampp --components mysql,apache
if %errorlevel% neq 0 (
    echo ERROR: No se pudo instalar XAMPP
    echo Instale manualmente desde el archivo descargado
    pause
    exit /b 1
)
echo XAMPP instalado

echo.
echo [4/6] Iniciando servicios XAMPP...
net start mysql
if %errorlevel% neq 0 (
    echo Iniciando MySQL manualmente...
    C:\xampp\mysql\bin\mysqld.exe --install
    net start mysql
)
echo MySQL iniciado

echo.
echo [5/6] Configurando base de datos...
C:\xampp\mysql\bin\mysql.exe -u root -e "CREATE DATABASE IF NOT EXISTS app_stock;"
C:\xampp\mysql\bin\mysql.exe -u root -e "CREATE USER IF NOT EXISTS 'app_user'@'localhost' IDENTIFIED BY 'app_password';"
C:\xampp\mysql\bin\mysql.exe -u root -e "GRANT ALL PRIVILEGES ON app_stock.* TO 'app_user'@'localhost';"
C:\xampp\mysql\bin\mysql.exe -u root -e "FLUSH PRIVILEGES;"
echo Base de datos configurada

echo.
echo [6/6] Creando configuracion de la aplicacion...
echo MYSQL_HOST=localhost > .env
echo MYSQL_PORT=3306 >> .env
echo MYSQL_USER=app_user >> .env
echo MYSQL_PASSWORD=app_password >> .env
echo MYSQL_DATABASE=app_stock >> .env
echo Configuracion creada

echo.
echo ========================================
echo    INSTALACION COMPLETADA EXITOSAMENTE
echo ========================================
echo.
echo La aplicacion App-Stock esta lista para usar.
echo.
echo Para iniciar la aplicacion:
echo 1. Haga doble clic en App-Stock.exe
echo 2. O use el acceso directo en el escritorio
echo.
echo Para detener/iniciar MySQL:
echo - Abra XAMPP Control Panel
echo - Use los botones Start/Stop
echo.
echo ¡Gracias por usar App-Stock!
echo.
pause
