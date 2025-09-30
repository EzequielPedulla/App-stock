@echo off
echo ========================================
echo    INSTALADOR XAMPP PARA APP-STOCK
echo ========================================
echo.

echo Este script descargara e instalara XAMPP automaticamente
echo XAMPP incluye MySQL, Apache y phpMyAdmin
echo.

set /p continuar="¿Desea continuar? (S/N): "
if /i "%continuar%" neq "S" (
    echo Instalacion cancelada.
    pause
    exit /b 0
)

echo.
echo [1/3] Descargando XAMPP...
echo Por favor, descargue XAMPP manualmente desde:
echo https://www.apachefriends.org/download.html
echo.
echo Seleccione la version para Windows (64-bit)
echo.

echo [2/3] Instalando XAMPP...
echo 1. Ejecute el instalador descargado
echo 2. Seleccione: MySQL, Apache, phpMyAdmin
echo 3. Instale en la ubicacion por defecto
echo 4. NO inicie XAMPP al finalizar
echo.

echo [3/3] Configurando MySQL...
echo Despues de instalar XAMPP:
echo 1. Inicie XAMPP Control Panel
echo 2. Inicie MySQL
echo 3. Ejecute configurar.bat
echo.

echo ========================================
echo    INSTRUCCIONES COMPLETAS
echo ========================================
echo.
echo 1. Descargar XAMPP: https://www.apachefriends.org/
echo 2. Instalar XAMPP (solo MySQL y Apache)
echo 3. Iniciar XAMPP Control Panel
echo 4. Iniciar MySQL
echo 5. Ejecutar configurar.bat
echo 6. Ejecutar App-Stock.exe
echo.
pause
