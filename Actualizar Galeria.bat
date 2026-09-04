@echo off
cd /d "%~dp0"
echo Actualizando galeria (miniaturas y listado de fotos)...
echo.
python generar_datos.py
if errorlevel 1 (
    echo.
    echo No se pudo ejecutar con "python". Probando con "py"...
    py generar_datos.py
)
echo.
pause
