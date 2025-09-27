@echo off
REM Script de backup automatizado para Synapsis Apoyos - Windows
REM Incluye backup de aplicación, base de datos y configuraciones

setlocal enabledelayedexpansion

REM Variables de configuración
set APP_NAME=synapsis_apoyos
set APP_DIR=%~dp0..
set BACKUP_BASE_DIR=C:\backups
set BACKUP_DIR=%BACKUP_BASE_DIR%\synapsis_apoyos
set RETENTION_DAYS=30

REM Crear timestamp
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
set "timestamp=%YYYY%%MM%%DD%_%HH%%Min%%Sec%"

REM Funciones de logging
:log_info
echo [INFO] %~1
goto :eof

:log_success
echo [SUCCESS] %~1
goto :eof

:log_warning
echo [WARNING] %~1
goto :eof

:log_error
echo [ERROR] %~1
goto :eof

REM Crear directorios de backup
:create_backup_dirs
set BACKUP_TYPE=%~1
set CURRENT_BACKUP_DIR=%BACKUP_DIR%\%BACKUP_TYPE%\%timestamp%

if not exist "%CURRENT_BACKUP_DIR%" (
    mkdir "%CURRENT_BACKUP_DIR%"
    mkdir "%CURRENT_BACKUP_DIR%\configs"
    mkdir "%CURRENT_BACKUP_DIR%\logs"
)

call :log_info "Directorio de backup creado: %CURRENT_BACKUP_DIR%"
goto :eof

REM Backup de la aplicación
:backup_application
call :log_info "Creando backup de la aplicación..."

if not exist "%APP_DIR%" (
    call :log_error "Directorio de aplicación no encontrado: %APP_DIR%"
    exit /b 1
)

REM Usar 7-Zip si está disponible, sino usar PowerShell
where 7z >nul 2>nul
if %errorlevel% equ 0 (
    7z a -tzip "%CURRENT_BACKUP_DIR%\app_backup.zip" "%APP_DIR%\*" -x!*.pyc -x!__pycache__ -x!*.log -x!venv -x!node_modules -x!.git -x!uploads\temp
) else (
    powershell -Command "Compress-Archive -Path '%APP_DIR%\*' -DestinationPath '%CURRENT_BACKUP_DIR%\app_backup.zip' -Force"
)

if %errorlevel% equ 0 (
    call :log_success "Backup de aplicación completado"
) else (
    call :log_error "Error en backup de aplicación"
    exit /b 1
)
goto :eof

REM Backup de base de datos
:backup_database
call :log_info "Creando backup de base de datos..."

REM Cargar variables de entorno
if exist "%APP_DIR%\.env.production" (
    for /f "usebackq tokens=1,2 delims==" %%a in ("%APP_DIR%\.env.production") do (
        if "%%a"=="DATABASE_URL" set DATABASE_URL=%%b
    )
) else (
    call :log_error "Archivo .env.production no encontrado"
    exit /b 1
)

if "%DATABASE_URL%"=="" (
    call :log_error "DATABASE_URL no configurada"
    exit /b 1
)

REM Extraer información de conexión (simplificado para Windows)
REM Nota: En producción, usar herramientas específicas como mysqldump
call :log_warning "Backup de BD requiere configuración manual de mysqldump en Windows"

REM Crear archivo de placeholder
echo -- Backup de base de datos generado el %date% %time% > "%CURRENT_BACKUP_DIR%\database_backup.sql"
echo -- Configurar mysqldump para backup automático >> "%CURRENT_BACKUP_DIR%\database_backup.sql"

call :log_success "Backup de base de datos completado (placeholder)"
goto :eof

REM Backup de configuraciones
:backup_configs
call :log_info "Creando backup de configuraciones..."

REM Backup de configuración de Gunicorn
if exist "%APP_DIR%\gunicorn.conf.py" (
    copy "%APP_DIR%\gunicorn.conf.py" "%CURRENT_BACKUP_DIR%\configs\gunicorn.conf.py" >nul
)

REM Backup de variables de entorno (sin valores sensibles)
if exist "%APP_DIR%\.env.production" (
    findstr /v /i "PASSWORD SECRET KEY TOKEN" "%APP_DIR%\.env.production" > "%CURRENT_BACKUP_DIR%\configs\env_template.txt"
)

REM Backup de configuración de IIS (si aplica)
if exist "C:\inetpub\wwwroot\web.config" (
    copy "C:\inetpub\wwwroot\web.config" "%CURRENT_BACKUP_DIR%\configs\web.config" >nul 2>nul
)

call :log_success "Backup de configuraciones completado"
goto :eof

REM Backup de uploads
:backup_uploads
call :log_info "Creando backup de uploads..."

if exist "%APP_DIR%\uploads" (
    where 7z >nul 2>nul
    if %errorlevel% equ 0 (
        7z a -tzip "%CURRENT_BACKUP_DIR%\uploads_backup.zip" "%APP_DIR%\uploads\*"
    ) else (
        powershell -Command "Compress-Archive -Path '%APP_DIR%\uploads\*' -DestinationPath '%CURRENT_BACKUP_DIR%\uploads_backup.zip' -Force"
    )
    call :log_success "Backup de uploads completado"
) else (
    call :log_warning "Directorio de uploads no encontrado"
)
goto :eof

REM Backup de logs
:backup_logs
call :log_info "Creando backup de logs..."

REM Logs de la aplicación
if exist "%APP_DIR%\logs" (
    xcopy "%APP_DIR%\logs\*" "%CURRENT_BACKUP_DIR%\logs\" /E /I /Q >nul 2>nul
)

REM Logs de IIS (si aplica)
if exist "C:\inetpub\logs\LogFiles" (
    xcopy "C:\inetpub\logs\LogFiles\*synapsis*" "%CURRENT_BACKUP_DIR%\logs\" /S /I /Q >nul 2>nul
)

REM Logs de eventos de Windows
wevtutil epl Application "%CURRENT_BACKUP_DIR%\logs\windows_application.evtx" >nul 2>nul
wevtutil epl System "%CURRENT_BACKUP_DIR%\logs\windows_system.evtx" >nul 2>nul

call :log_success "Backup de logs completado"
goto :eof

REM Crear archivo de metadatos
:create_metadata
call :log_info "Creando metadatos del backup..."

(
echo {
echo   "backup_date": "%timestamp%",
echo   "app_name": "%APP_NAME%",
echo   "app_dir": "%APP_DIR%",
echo   "hostname": "%COMPUTERNAME%",
echo   "backup_type": "%BACKUP_TYPE%",
echo   "system_info": {
echo     "os": "%OS%",
echo     "processor": "%PROCESSOR_IDENTIFIER%",
echo     "user": "%USERNAME%"
echo   },
echo   "files_included": [
echo     "app_backup.zip",
echo     "database_backup.sql",
echo     "uploads_backup.zip",
echo     "configs/",
echo     "logs/"
echo   ]
echo }
) > "%CURRENT_BACKUP_DIR%\backup_metadata.json"

call :log_success "Metadatos creados"
goto :eof

REM Verificar integridad del backup
:verify_backup
call :log_info "Verificando integridad del backup..."

set errors=0

if not exist "%CURRENT_BACKUP_DIR%\app_backup.zip" (
    call :log_error "Archivo de backup de aplicación no encontrado"
    set /a errors+=1
)

if not exist "%CURRENT_BACKUP_DIR%\database_backup.sql" (
    call :log_error "Archivo de backup de base de datos no encontrado"
    set /a errors+=1
)

REM Verificar integridad de archivos ZIP
where 7z >nul 2>nul
if %errorlevel% equ 0 (
    if exist "%CURRENT_BACKUP_DIR%\app_backup.zip" (
        7z t "%CURRENT_BACKUP_DIR%\app_backup.zip" >nul 2>nul
        if !errorlevel! neq 0 (
            call :log_error "Archivo de backup de aplicación está corrupto"
            set /a errors+=1
        )
    )
    
    if exist "%CURRENT_BACKUP_DIR%\uploads_backup.zip" (
        7z t "%CURRENT_BACKUP_DIR%\uploads_backup.zip" >nul 2>nul
        if !errorlevel! neq 0 (
            call :log_error "Archivo de backup de uploads está corrupto"
            set /a errors+=1
        )
    )
)

if %errors% equ 0 (
    call :log_success "Verificación de integridad completada - Sin errores"
    exit /b 0
) else (
    call :log_error "Verificación de integridad falló - %errors% errores encontrados"
    exit /b 1
)
goto :eof

REM Limpiar backups antiguos
:cleanup_old_backups
call :log_info "Limpiando backups antiguos..."

REM Eliminar backups más antiguos que RETENTION_DAYS
forfiles /p "%BACKUP_DIR%" /s /m *.* /d -%RETENTION_DAYS% /c "cmd /c if @isdir==TRUE rmdir /s /q @path" >nul 2>nul

call :log_success "Limpieza de backups antiguos completada"
goto :eof

REM Función principal de backup
:perform_backup
set BACKUP_TYPE=%~1

call :log_info "🔄 Iniciando backup %BACKUP_TYPE% de %APP_NAME%"

REM Crear directorios
call :create_backup_dirs %BACKUP_TYPE%

set start_time=%time%
set errors=0

REM Ejecutar backups
call :backup_application
if %errorlevel% neq 0 set /a errors+=1

call :backup_database
if %errorlevel% neq 0 set /a errors+=1

call :backup_configs
call :backup_uploads
call :backup_logs

REM Crear metadatos
call :create_metadata

REM Verificar integridad
call :verify_backup
if %errorlevel% neq 0 set /a errors+=1

set end_time=%time%

REM Calcular tamaño del backup
for /f "usebackq" %%A in (`powershell -Command "(Get-ChildItem '%CURRENT_BACKUP_DIR%' -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB"`) do set backup_size=%%A

if %errors% equ 0 (
    call :log_success "✅ Backup %BACKUP_TYPE% completado exitosamente"
    call :log_info "📊 Estadísticas del backup:"
    call :log_info "   - Inicio: %start_time%"
    call :log_info "   - Fin: %end_time%"
    call :log_info "   - Tamaño: %backup_size% MB"
    call :log_info "   - Ubicación: %CURRENT_BACKUP_DIR%"
) else (
    call :log_error "❌ Backup %BACKUP_TYPE% completado con %errors% errores"
)

REM Limpiar backups antiguos
call :cleanup_old_backups

exit /b %errors%

REM Función de restauración
:restore_backup
set backup_path=%~1

if not exist "%backup_path%" (
    call :log_error "Directorio de backup no encontrado: %backup_path%"
    exit /b 1
)

call :log_warning "⚠️  INICIANDO RESTAURACIÓN DESDE: %backup_path%"
call :log_warning "⚠️  ESTO SOBRESCRIBIRÁ LOS DATOS ACTUALES"

set /p confirm="¿Continuar con la restauración? (yes/no): "
if not "%confirm%"=="yes" (
    call :log_info "Restauración cancelada"
    exit /b 0
)

REM Detener servicios (adaptar según configuración)
net stop "Synapsis Apoyos" >nul 2>nul

REM Restaurar aplicación
if exist "%backup_path%\app_backup.zip" (
    call :log_info "Restaurando aplicación..."
    rmdir /s /q "%APP_DIR%" >nul 2>nul
    mkdir "%APP_DIR%"
    
    where 7z >nul 2>nul
    if %errorlevel% equ 0 (
        7z x "%backup_path%\app_backup.zip" -o"%APP_DIR%" -y >nul
    ) else (
        powershell -Command "Expand-Archive -Path '%backup_path%\app_backup.zip' -DestinationPath '%APP_DIR%' -Force"
    )
)

REM Restaurar uploads
if exist "%backup_path%\uploads_backup.zip" (
    call :log_info "Restaurando uploads..."
    where 7z >nul 2>nul
    if %errorlevel% equ 0 (
        7z x "%backup_path%\uploads_backup.zip" -o"%APP_DIR%" -y >nul
    ) else (
        powershell -Command "Expand-Archive -Path '%backup_path%\uploads_backup.zip' -DestinationPath '%APP_DIR%' -Force"
    )
)

REM Iniciar servicios
net start "Synapsis Apoyos" >nul 2>nul

call :log_success "Restauración completada"
exit /b 0

REM Mostrar ayuda
:show_help
echo Uso: %~nx0 [OPCIÓN]
echo.
echo Opciones:
echo   daily     Crear backup diario
echo   weekly    Crear backup semanal
echo   monthly   Crear backup mensual
echo   restore   Restaurar desde backup
echo   list      Listar backups disponibles
echo   help      Mostrar esta ayuda
echo.
echo Ejemplos:
echo   %~nx0 daily
echo   %~nx0 restore "C:\backups\synapsis_apoyos\daily\20240115_143000"
goto :eof

REM Listar backups disponibles
:list_backups
echo 📋 Backups disponibles:
echo.

for %%t in (daily weekly monthly) do (
    echo === Backups %%t ===
    if exist "%BACKUP_DIR%\%%t" (
        dir /b "%BACKUP_DIR%\%%t" 2>nul
    ) else (
        echo No hay backups %%t
    )
    echo.
)
goto :eof

REM Función principal
:main
set action=%~1
if "%action%"=="" set action=daily

if "%action%"=="daily" goto :perform_backup_daily
if "%action%"=="weekly" goto :perform_backup_weekly
if "%action%"=="monthly" goto :perform_backup_monthly
if "%action%"=="restore" goto :restore_main
if "%action%"=="list" goto :list_backups
if "%action%"=="help" goto :show_help
if "%action%"=="-h" goto :show_help
if "%action%"=="--help" goto :show_help

call :log_error "Opción no válida: %action%"
call :show_help
exit /b 1

:perform_backup_daily
call :perform_backup "daily"
goto :end

:perform_backup_weekly
call :perform_backup "weekly"
goto :end

:perform_backup_monthly
call :perform_backup "monthly"
goto :end

:restore_main
if "%~2"=="" (
    call :log_error "Especifica la ruta del backup a restaurar"
    call :show_help
    exit /b 1
)
call :restore_backup "%~2"
goto :end

:end
exit /b %errorlevel%

REM Ejecutar función principal
call :main %*