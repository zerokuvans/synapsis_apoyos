@echo off
echo Deteniendo Synapsis Apoyos...

REM Buscar y terminar procesos de Gunicorn
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq python.exe" /fo table /nh ^| findstr gunicorn') do (
    echo Terminando proceso %%i
    taskkill /pid %%i /f
)

echo Servidor detenido.
pause
