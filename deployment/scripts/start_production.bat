@echo off
echo Iniciando Synapsis Apoyos en modo producción...
set FLASK_ENV=production
set FLASK_DEBUG=False

REM Crear directorio de logs si no existe
if not exist "logs" mkdir logs

REM Iniciar con Gunicorn
echo Iniciando servidor con Gunicorn...
gunicorn --config deployment/configs/gunicorn_windows.conf.py run:app

pause
