#!/bin/bash
# Script de backup automatizado para Synapsis Apoyos
# Incluye backup de aplicación, base de datos y configuraciones

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables de configuración
APP_NAME="synapsis_apoyos"
APP_DIR="/opt/synapsis_apoyos"
BACKUP_BASE_DIR="/opt/backups"
BACKUP_DIR="$BACKUP_BASE_DIR/synapsis_apoyos"
REMOTE_BACKUP_DIR="/mnt/backup_remote"  # Para backups remotos
RETENTION_DAYS=30
RETENTION_WEEKS=12
RETENTION_MONTHS=12

# Configuración de notificaciones
NOTIFICATION_EMAIL="admin@tu-dominio.com"
SLACK_WEBHOOK_URL=""  # Configurar si se usa Slack

# Funciones de utilidad
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Función para enviar notificaciones
send_notification() {
    local status="$1"
    local message="$2"
    
    # Email notification
    if [ ! -z "$NOTIFICATION_EMAIL" ] && command -v mail >/dev/null 2>&1; then
        echo "$message" | mail -s "Backup $status - Synapsis Apoyos" "$NOTIFICATION_EMAIL"
    fi
    
    # Slack notification
    if [ ! -z "$SLACK_WEBHOOK_URL" ] && command -v curl >/dev/null 2>&1; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"🔄 Backup $status - Synapsis Apoyos\\n$message\"}" \
            "$SLACK_WEBHOOK_URL" >/dev/null 2>&1
    fi
}

# Crear directorios de backup
create_backup_dirs() {
    local timestamp="$1"
    
    DAILY_DIR="$BACKUP_DIR/daily/$timestamp"
    WEEKLY_DIR="$BACKUP_DIR/weekly/$timestamp"
    MONTHLY_DIR="$BACKUP_DIR/monthly/$timestamp"
    
    mkdir -p "$DAILY_DIR" "$WEEKLY_DIR" "$MONTHLY_DIR"
    mkdir -p "$BACKUP_DIR/logs"
}

# Backup de la aplicación
backup_application() {
    local backup_path="$1"
    
    log_info "Creando backup de la aplicación..."
    
    if [ ! -d "$APP_DIR" ]; then
        log_error "Directorio de aplicación no encontrado: $APP_DIR"
        return 1
    fi
    
    # Crear archivo tar excluyendo archivos temporales
    tar -czf "$backup_path/app_backup.tar.gz" \
        --exclude="*.pyc" \
        --exclude="__pycache__" \
        --exclude="*.log" \
        --exclude="venv" \
        --exclude="node_modules" \
        --exclude=".git" \
        --exclude="uploads/temp" \
        -C "$APP_DIR" .
    
    if [ $? -eq 0 ]; then
        log_success "Backup de aplicación completado"
        return 0
    else
        log_error "Error en backup de aplicación"
        return 1
    fi
}

# Backup de base de datos
backup_database() {
    local backup_path="$1"
    
    log_info "Creando backup de base de datos..."
    
    # Cargar variables de entorno
    if [ -f "$APP_DIR/.env.production" ]; then
        source "$APP_DIR/.env.production"
    else
        log_error "Archivo .env.production no encontrado"
        return 1
    fi
    
    if [ -z "$DATABASE_URL" ]; then
        log_error "DATABASE_URL no configurada"
        return 1
    fi
    
    # Extraer información de conexión
    DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
    DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
    DB_USER=$(echo $DATABASE_URL | sed -n 's/.*\/\/\([^:]*\):.*/\1/p')
    DB_PASS=$(echo $DATABASE_URL | sed -n 's/.*\/\/[^:]*:\([^@]*\)@.*/\1/p')
    DB_NAME=$(echo $DATABASE_URL | sed -n 's/.*\/\([^?]*\).*/\1/p')
    
    # Backup con mysqldump
    mysqldump \
        --single-transaction \
        --routines \
        --triggers \
        --events \
        --add-drop-database \
        --create-options \
        --disable-keys \
        --extended-insert \
        --quick \
        --lock-tables=false \
        -h "$DB_HOST" \
        -P "$DB_PORT" \
        -u "$DB_USER" \
        -p"$DB_PASS" \
        "$DB_NAME" > "$backup_path/database_backup.sql"
    
    if [ $? -eq 0 ]; then
        # Comprimir backup de BD
        gzip "$backup_path/database_backup.sql"
        log_success "Backup de base de datos completado"
        return 0
    else
        log_error "Error en backup de base de datos"
        return 1
    fi
}

# Backup de configuraciones
backup_configs() {
    local backup_path="$1"
    
    log_info "Creando backup de configuraciones..."
    
    mkdir -p "$backup_path/configs"
    
    # Backup de configuración de Nginx
    if [ -f "/etc/nginx/sites-available/$APP_NAME" ]; then
        cp "/etc/nginx/sites-available/$APP_NAME" "$backup_path/configs/nginx_$APP_NAME.conf"
    fi
    
    # Backup de configuración de systemd
    if [ -f "/etc/systemd/system/$APP_NAME.service" ]; then
        cp "/etc/systemd/system/$APP_NAME.service" "$backup_path/configs/$APP_NAME.service"
    fi
    
    # Backup de configuración de Gunicorn
    if [ -f "$APP_DIR/gunicorn.conf.py" ]; then
        cp "$APP_DIR/gunicorn.conf.py" "$backup_path/configs/gunicorn.conf.py"
    fi
    
    # Backup de variables de entorno (sin valores sensibles)
    if [ -f "$APP_DIR/.env.production" ]; then
        grep -v -E "(PASSWORD|SECRET|KEY|TOKEN)" "$APP_DIR/.env.production" > "$backup_path/configs/env_template.txt"
    fi
    
    # Backup de certificados SSL (solo públicos)
    if [ -d "/etc/letsencrypt/live" ]; then
        mkdir -p "$backup_path/configs/ssl"
        find /etc/letsencrypt/live -name "*.pem" -exec cp {} "$backup_path/configs/ssl/" \;
    fi
    
    log_success "Backup de configuraciones completado"
}

# Backup de uploads y archivos de usuario
backup_uploads() {
    local backup_path="$1"
    
    log_info "Creando backup de uploads..."
    
    if [ -d "$APP_DIR/uploads" ]; then
        tar -czf "$backup_path/uploads_backup.tar.gz" -C "$APP_DIR" uploads/
        log_success "Backup de uploads completado"
    else
        log_warning "Directorio de uploads no encontrado"
    fi
}

# Backup de logs
backup_logs() {
    local backup_path="$1"
    
    log_info "Creando backup de logs..."
    
    mkdir -p "$backup_path/logs"
    
    # Logs de la aplicación
    if [ -d "$APP_DIR/logs" ]; then
        cp -r "$APP_DIR/logs"/* "$backup_path/logs/" 2>/dev/null || true
    fi
    
    # Logs de Nginx
    if [ -d "/var/log/nginx" ]; then
        cp /var/log/nginx/*$APP_NAME* "$backup_path/logs/" 2>/dev/null || true
    fi
    
    # Logs de systemd
    journalctl -u "$APP_NAME" --since "1 week ago" > "$backup_path/logs/systemd_$APP_NAME.log" 2>/dev/null || true
    
    log_success "Backup de logs completado"
}

# Crear archivo de metadatos
create_metadata() {
    local backup_path="$1"
    local timestamp="$2"
    
    cat > "$backup_path/backup_metadata.json" << EOF
{
    "backup_date": "$timestamp",
    "app_name": "$APP_NAME",
    "app_dir": "$APP_DIR",
    "hostname": "$(hostname)",
    "backup_type": "$BACKUP_TYPE",
    "git_commit": "$(cd $APP_DIR && git rev-parse HEAD 2>/dev/null || echo 'unknown')",
    "git_branch": "$(cd $APP_DIR && git branch --show-current 2>/dev/null || echo 'unknown')",
    "system_info": {
        "os": "$(lsb_release -d 2>/dev/null | cut -f2 || echo 'unknown')",
        "kernel": "$(uname -r)",
        "uptime": "$(uptime -p)"
    },
    "backup_size": "$(du -sh $backup_path | cut -f1)",
    "files_included": [
        "app_backup.tar.gz",
        "database_backup.sql.gz",
        "uploads_backup.tar.gz",
        "configs/",
        "logs/"
    ]
}
EOF
}

# Verificar integridad del backup
verify_backup() {
    local backup_path="$1"
    
    log_info "Verificando integridad del backup..."
    
    local errors=0
    
    # Verificar archivos principales
    if [ ! -f "$backup_path/app_backup.tar.gz" ]; then
        log_error "Archivo de backup de aplicación no encontrado"
        ((errors++))
    fi
    
    if [ ! -f "$backup_path/database_backup.sql.gz" ]; then
        log_error "Archivo de backup de base de datos no encontrado"
        ((errors++))
    fi
    
    # Verificar integridad de archivos tar
    if [ -f "$backup_path/app_backup.tar.gz" ]; then
        if ! tar -tzf "$backup_path/app_backup.tar.gz" >/dev/null 2>&1; then
            log_error "Archivo de backup de aplicación está corrupto"
            ((errors++))
        fi
    fi
    
    if [ -f "$backup_path/uploads_backup.tar.gz" ]; then
        if ! tar -tzf "$backup_path/uploads_backup.tar.gz" >/dev/null 2>&1; then
            log_error "Archivo de backup de uploads está corrupto"
            ((errors++))
        fi
    fi
    
    # Verificar integridad de backup de BD
    if [ -f "$backup_path/database_backup.sql.gz" ]; then
        if ! gunzip -t "$backup_path/database_backup.sql.gz" 2>/dev/null; then
            log_error "Archivo de backup de base de datos está corrupto"
            ((errors++))
        fi
    fi
    
    if [ $errors -eq 0 ]; then
        log_success "Verificación de integridad completada - Sin errores"
        return 0
    else
        log_error "Verificación de integridad falló - $errors errores encontrados"
        return 1
    fi
}

# Sincronizar con backup remoto
sync_remote_backup() {
    local backup_path="$1"
    
    if [ ! -d "$REMOTE_BACKUP_DIR" ]; then
        log_warning "Directorio de backup remoto no disponible: $REMOTE_BACKUP_DIR"
        return 1
    fi
    
    log_info "Sincronizando con backup remoto..."
    
    rsync -av --delete "$backup_path/" "$REMOTE_BACKUP_DIR/$(basename $backup_path)/"
    
    if [ $? -eq 0 ]; then
        log_success "Sincronización remota completada"
        return 0
    else
        log_error "Error en sincronización remota"
        return 1
    fi
}

# Limpiar backups antiguos
cleanup_old_backups() {
    log_info "Limpiando backups antiguos..."
    
    # Limpiar backups diarios (mantener últimos 30 días)
    find "$BACKUP_DIR/daily" -type d -mtime +$RETENTION_DAYS -exec rm -rf {} + 2>/dev/null || true
    
    # Limpiar backups semanales (mantener últimas 12 semanas)
    find "$BACKUP_DIR/weekly" -type d -mtime +$((RETENTION_WEEKS * 7)) -exec rm -rf {} + 2>/dev/null || true
    
    # Limpiar backups mensuales (mantener últimos 12 meses)
    find "$BACKUP_DIR/monthly" -type d -mtime +$((RETENTION_MONTHS * 30)) -exec rm -rf {} + 2>/dev/null || true
    
    log_success "Limpieza de backups antiguos completada"
}

# Función principal de backup
perform_backup() {
    local backup_type="$1"
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    
    BACKUP_TYPE="$backup_type"
    
    log_info "🔄 Iniciando backup $backup_type de $APP_NAME"
    
    # Crear directorios
    create_backup_dirs "$timestamp"
    
    # Determinar directorio de backup según tipo
    case "$backup_type" in
        "daily")
            CURRENT_BACKUP_DIR="$DAILY_DIR"
            ;;
        "weekly")
            CURRENT_BACKUP_DIR="$WEEKLY_DIR"
            ;;
        "monthly")
            CURRENT_BACKUP_DIR="$MONTHLY_DIR"
            ;;
        *)
            CURRENT_BACKUP_DIR="$DAILY_DIR"
            ;;
    esac
    
    local start_time=$(date +%s)
    local errors=0
    
    # Ejecutar backups
    backup_application "$CURRENT_BACKUP_DIR" || ((errors++))
    backup_database "$CURRENT_BACKUP_DIR" || ((errors++))
    backup_configs "$CURRENT_BACKUP_DIR"
    backup_uploads "$CURRENT_BACKUP_DIR"
    backup_logs "$CURRENT_BACKUP_DIR"
    
    # Crear metadatos
    create_metadata "$CURRENT_BACKUP_DIR" "$timestamp"
    
    # Verificar integridad
    verify_backup "$CURRENT_BACKUP_DIR" || ((errors++))
    
    # Sincronizar con backup remoto
    sync_remote_backup "$CURRENT_BACKUP_DIR"
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    # Generar reporte
    local backup_size=$(du -sh "$CURRENT_BACKUP_DIR" | cut -f1)
    
    if [ $errors -eq 0 ]; then
        log_success "✅ Backup $backup_type completado exitosamente"
        log_info "📊 Estadísticas del backup:"
        log_info "   - Duración: ${duration}s"
        log_info "   - Tamaño: $backup_size"
        log_info "   - Ubicación: $CURRENT_BACKUP_DIR"
        
        send_notification "SUCCESS" "Backup $backup_type completado exitosamente en ${duration}s. Tamaño: $backup_size"
    else
        log_error "❌ Backup $backup_type completado con $errors errores"
        send_notification "ERROR" "Backup $backup_type completado con $errors errores. Revisar logs."
    fi
    
    # Limpiar backups antiguos
    cleanup_old_backups
    
    return $errors
}

# Función de restauración
restore_backup() {
    local backup_path="$1"
    
    if [ ! -d "$backup_path" ]; then
        log_error "Directorio de backup no encontrado: $backup_path"
        exit 1
    fi
    
    log_warning "⚠️  INICIANDO RESTAURACIÓN DESDE: $backup_path"
    log_warning "⚠️  ESTO SOBRESCRIBIRÁ LOS DATOS ACTUALES"
    
    read -p "¿Continuar con la restauración? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        log_info "Restauración cancelada"
        exit 0
    fi
    
    # Detener servicios
    systemctl stop "$APP_NAME" || true
    
    # Restaurar aplicación
    if [ -f "$backup_path/app_backup.tar.gz" ]; then
        log_info "Restaurando aplicación..."
        rm -rf "$APP_DIR"
        mkdir -p "$APP_DIR"
        tar -xzf "$backup_path/app_backup.tar.gz" -C "$APP_DIR"
        chown -R www-data:www-data "$APP_DIR"
    fi
    
    # Restaurar base de datos
    if [ -f "$backup_path/database_backup.sql.gz" ]; then
        log_info "Restaurando base de datos..."
        source "$APP_DIR/.env.production"
        gunzip -c "$backup_path/database_backup.sql.gz" | mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME"
    fi
    
    # Restaurar uploads
    if [ -f "$backup_path/uploads_backup.tar.gz" ]; then
        log_info "Restaurando uploads..."
        tar -xzf "$backup_path/uploads_backup.tar.gz" -C "$APP_DIR"
    fi
    
    # Iniciar servicios
    systemctl start "$APP_NAME"
    
    log_success "Restauración completada"
}

# Mostrar ayuda
show_help() {
    echo "Uso: $0 [OPCIÓN]"
    echo ""
    echo "Opciones:"
    echo "  daily     Crear backup diario"
    echo "  weekly    Crear backup semanal"
    echo "  monthly   Crear backup mensual"
    echo "  restore   Restaurar desde backup"
    echo "  list      Listar backups disponibles"
    echo "  help      Mostrar esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  $0 daily"
    echo "  $0 restore /opt/backups/synapsis_apoyos/daily/20240115_143000"
}

# Listar backups disponibles
list_backups() {
    echo "📋 Backups disponibles:"
    echo ""
    
    for type in daily weekly monthly; do
        echo "=== Backups $type ==="
        if [ -d "$BACKUP_DIR/$type" ]; then
            ls -la "$BACKUP_DIR/$type" | grep "^d" | awk '{print $9, $6, $7, $8}' | grep -v "^\.$\|^\.\.$"
        else
            echo "No hay backups $type"
        fi
        echo ""
    done
}

# Función principal
main() {
    case "${1:-daily}" in
        "daily"|"weekly"|"monthly")
            perform_backup "$1"
            ;;
        "restore")
            if [ -z "$2" ]; then
                log_error "Especifica la ruta del backup a restaurar"
                show_help
                exit 1
            fi
            restore_backup "$2"
            ;;
        "list")
            list_backups
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            log_error "Opción no válida: $1"
            show_help
            exit 1
            ;;
    esac
}

# Ejecutar función principal
main "$@"