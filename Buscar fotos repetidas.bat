@echo off
cd /d "%~dp0"
echo Buscando fotos y videos repetidos...
echo.
python buscar_repetidas.py
if errorlevel 1 py buscar_repetidas.py
