@echo off
echo ========================================
echo    CONFIGURACION AUTOMATICA APP-STOCK
echo ========================================
echo.

echo [1/4] Verificando MySQL...
mysql --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: MySQL no esta instalado
    echo.
    echo SOLUCION:
    echo 1. Instalar XAMPP desde: https://www.apachefriends.org/
    echo 2. O instalar MySQL desde: https://dev.mysql.com/downloads/
    echo.
    pause
    exit /b 1
)

echo [2/4] Creando base de datos...
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS app_stock;" 2>nul
if %errorlevel% neq 0 (
    echo ERROR: No se pudo crear la base de datos
    echo Verifique que MySQL este ejecutandose y las credenciales sean correctas
    pause
    exit /b 1
)

echo [3/4] Configurando permisos...
mysql -u root -p -e "GRANT ALL PRIVILEGES ON app_stock.* TO 'app_user'@'localhost' IDENTIFIED BY 'app_password';" 2>nul
mysql -u root -p -e "FLUSH PRIVILEGES;" 2>nul

echo [4/4] Creando archivo de configuracion...
echo MYSQL_HOST=localhost > .env
echo MYSQL_PORT=3306 >> .env
echo MYSQL_USER=app_user >> .env
echo MYSQL_PASSWORD=app_password >> .env
echo MYSQL_DATABASE=app_stock >> .env

echo.
echo ========================================
echo    CONFIGURACION COMPLETADA
echo ========================================
echo.
echo La aplicacion esta lista para usar.
echo Ejecute App-Stock.exe para comenzar.
echo.
pause
