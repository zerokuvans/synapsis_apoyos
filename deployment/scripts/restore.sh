#!/bin/bash
# Script de restauración para Synapsis Apoyos
# Permite restaurar desde diferentes tipos de backup con verificaciones de seguridad

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
RESTORE_LOG="/var/log/synapsis_restore.log"

# Funciones de utilidad
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] $1" >> "$RESTORE_LOG"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [SUCCESS] $1" >> "$RESTORE_LOG"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [WARNING] $1" >> "$RESTORE_LOG"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] $1" >> "$RESTORE_LOG"
}

# Verificar si el usuario es root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "Este script debe ejecutarse como root"
        exit 1
    fi
}

# Verificar integridad del backup
verify_backup_integrity() {
    local backup_path="$1"
    
    log_info "Verificando integridad del backup: $backup_path"
    
    if [ ! -d "$backup_path" ]; then
        log_error "Directorio de backup no encontrado: $backup_path"
        return 1
    fi
    
    # Verificar archivo de metadatos
    if [ ! -f "$backup_path/backup_metadata.json" ]; then
        log_warning "Archivo de metadatos no encontrado"
    else
        log_info "Metadatos del backup encontrados"
        cat "$backup_path/backup_metadata.json" | jq . 2>/dev/null || log_warning "Metadatos no válidos"
    fi
    
    # Verificar archivos principales
    local missing_files=0
    
    if [ ! -f "$backup_path/app_backup.tar.gz" ]; then
        log_error "Backup de aplicación no encontrado"
        ((missing_files++))
    else
        # Verificar integridad del archivo tar
        if ! tar -tzf "$backup_path/app_backup.tar.gz" >/dev/null 2>&1; then
            log_error "Backup de aplicación está corrupto"
            ((missing_files++))
        else
            log_success "Backup de aplicación verificado"
        fi
    fi
    
    if [ ! -f "$backup_path/database_backup.sql.gz" ]; then
        log_error "Backup de base de datos no encontrado"
        ((missing_files++))
    else
        # Verificar integridad del archivo gzip
        if ! gunzip -t "$backup_path/database_backup.sql.gz" 2>/dev/null; then
            log_error "Backup de base de datos está corrupto"
            ((missing_files++))
        else
            log_success "Backup de base de datos verificado"
        fi
    fi
    
    if [ -f "$backup_path/uploads_backup.tar.gz" ]; then
        if ! tar -tzf "$backup_path/uploads_backup.tar.gz" >/dev/null 2>&1; then
            log_warning "Backup de uploads está corrupto"
        else
            log_success "Backup de uploads verificado"
        fi
    fi
    
    if [ $missing_files -gt 0 ]; then
        log_error "Faltan $missing_files archivos críticos del backup"
        return 1
    fi
    
    log_success "Verificación de integridad completada"
    return 0
}

# Crear backup de seguridad antes de restaurar
create_safety_backup() {
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local safety_backup_dir="/tmp/synapsis_safety_backup_$timestamp"
    
    log_info "Creando backup de seguridad antes de la restauración..."
    
    mkdir -p "$safety_backup_dir"
    
    # Backup rápido de la aplicación actual
    if [ -d "$APP_DIR" ]; then
        tar -czf "$safety_backup_dir/current_app.tar.gz" -C "$APP_DIR" . 2>/dev/null || true
    fi
    
    # Backup rápido de la base de datos
    if [ -f "$APP_DIR/.env.production" ]; then
        source "$APP_DIR/.env.production"
        if [ ! -z "$DATABASE_URL" ]; then
            # Extraer información de conexión
            DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
            DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
            DB_USER=$(echo $DATABASE_URL | sed -n 's/.*\/\/\([^:]*\):.*/\1/p')
            DB_PASS=$(echo $DATABASE_URL | sed -n 's/.*\/\/[^:]*:\([^@]*\)@.*/\1/p')
            DB_NAME=$(echo $DATABASE_URL | sed -n 's/.*\/\([^?]*\).*/\1/p')
            
            mysqldump --single-transaction -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" | gzip > "$safety_backup_dir/current_database.sql.gz" 2>/dev/null || true
        fi
    fi
    
    echo "$safety_backup_dir" > "/tmp/synapsis_last_safety_backup.txt"
    log_success "Backup de seguridad creado en: $safety_backup_dir"
}

# Detener servicios
stop_services() {
    log_info "Deteniendo servicios..."
    
    # Detener aplicación
    systemctl stop "$APP_NAME" 2>/dev/null || true
    
    # Detener Nginx si está configurado para la aplicación
    if systemctl is-active --quiet nginx; then
        systemctl stop nginx
        log_info "Nginx detenido"
    fi
    
    # Esperar a que los procesos terminen
    sleep 5
    
    # Verificar que no hay procesos de la aplicación ejecutándose
    if pgrep -f "$APP_NAME" >/dev/null; then
        log_warning "Procesos de la aplicación aún ejecutándose, terminando forzadamente..."
        pkill -f "$APP_NAME" || true
        sleep 2
    fi
    
    log_success "Servicios detenidos"
}

# Iniciar servicios
start_services() {
    log_info "Iniciando servicios..."
    
    # Iniciar aplicación
    systemctl start "$APP_NAME"
    
    # Verificar que el servicio inició correctamente
    sleep 5
    if systemctl is-active --quiet "$APP_NAME"; then
        log_success "Servicio $APP_NAME iniciado correctamente"
    else
        log_error "Error al iniciar el servicio $APP_NAME"
        systemctl status "$APP_NAME" || true
        return 1
    fi
    
    # Iniciar Nginx
    if systemctl is-enabled --quiet nginx; then
        systemctl start nginx
        if systemctl is-active --quiet nginx; then
            log_success "Nginx iniciado correctamente"
        else
            log_error "Error al iniciar Nginx"
            return 1
        fi
    fi
    
    return 0
}

# Restaurar aplicación
restore_application() {
    local backup_path="$1"
    
    log_info "Restaurando aplicación desde: $backup_path/app_backup.tar.gz"
    
    # Crear backup del directorio actual
    if [ -d "$APP_DIR" ]; then
        mv "$APP_DIR" "${APP_DIR}.old.$(date +%s)" 2>/dev/null || true
    fi
    
    # Crear directorio de aplicación
    mkdir -p "$APP_DIR"
    
    # Extraer backup
    if ! tar -xzf "$backup_path/app_backup.tar.gz" -C "$APP_DIR"; then
        log_error "Error al extraer backup de aplicación"
        return 1
    fi
    
    # Restaurar permisos
    chown -R www-data:www-data "$APP_DIR"
    chmod -R 755 "$APP_DIR"
    
    # Permisos especiales para directorios sensibles
    if [ -d "$APP_DIR/uploads" ]; then
        chmod -R 775 "$APP_DIR/uploads"
    fi
    
    if [ -d "$APP_DIR/logs" ]; then
        chmod -R 775 "$APP_DIR/logs"
    fi
    
    log_success "Aplicación restaurada correctamente"
    return 0
}

# Restaurar base de datos
restore_database() {
    local backup_path="$1"
    
    log_info "Restaurando base de datos desde: $backup_path/database_backup.sql.gz"
    
    # Cargar variables de entorno
    if [ ! -f "$APP_DIR/.env.production" ]; then
        log_error "Archivo .env.production no encontrado después de restaurar aplicación"
        return 1
    fi
    
    source "$APP_DIR/.env.production"
    
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
    
    # Verificar conexión a la base de datos
    if ! mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" -e "SELECT 1;" >/dev/null 2>&1; then
        log_error "No se puede conectar a la base de datos"
        return 1
    fi
    
    # Crear backup de la base de datos actual
    log_info "Creando backup de la base de datos actual..."
    mysqldump --single-transaction -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" | gzip > "/tmp/db_backup_before_restore_$(date +%s).sql.gz"
    
    # Restaurar base de datos
    log_info "Restaurando base de datos..."
    if ! gunzip -c "$backup_path/database_backup.sql.gz" | mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME"; then
        log_error "Error al restaurar base de datos"
        return 1
    fi
    
    log_success "Base de datos restaurada correctamente"
    return 0
}

# Restaurar uploads
restore_uploads() {
    local backup_path="$1"
    
    if [ ! -f "$backup_path/uploads_backup.tar.gz" ]; then
        log_warning "Backup de uploads no encontrado, omitiendo..."
        return 0
    fi
    
    log_info "Restaurando uploads desde: $backup_path/uploads_backup.tar.gz"
    
    # Crear backup del directorio actual de uploads
    if [ -d "$APP_DIR/uploads" ]; then
        mv "$APP_DIR/uploads" "$APP_DIR/uploads.old.$(date +%s)" 2>/dev/null || true
    fi
    
    # Extraer uploads
    if ! tar -xzf "$backup_path/uploads_backup.tar.gz" -C "$APP_DIR"; then
        log_error "Error al extraer backup de uploads"
        return 1
    fi
    
    # Restaurar permisos
    if [ -d "$APP_DIR/uploads" ]; then
        chown -R www-data:www-data "$APP_DIR/uploads"
        chmod -R 775 "$APP_DIR/uploads"
    fi
    
    log_success "Uploads restaurados correctamente"
    return 0
}

# Restaurar configuraciones
restore_configs() {
    local backup_path="$1"
    
    if [ ! -d "$backup_path/configs" ]; then
        log_warning "Backup de configuraciones no encontrado, omitiendo..."
        return 0
    fi
    
    log_info "Restaurando configuraciones..."
    
    # Restaurar configuración de Nginx
    if [ -f "$backup_path/configs/nginx_$APP_NAME.conf" ]; then
        cp "$backup_path/configs/nginx_$APP_NAME.conf" "/etc/nginx/sites-available/$APP_NAME"
        log_info "Configuración de Nginx restaurada"
    fi
    
    # Restaurar configuración de systemd
    if [ -f "$backup_path/configs/$APP_NAME.service" ]; then
        cp "$backup_path/configs/$APP_NAME.service" "/etc/systemd/system/$APP_NAME.service"
        systemctl daemon-reload
        log_info "Configuración de systemd restaurada"
    fi
    
    log_success "Configuraciones restauradas"
    return 0
}

# Verificar restauración
verify_restoration() {
    log_info "Verificando restauración..."
    
    local errors=0
    
    # Verificar que la aplicación está ejecutándose
    if ! systemctl is-active --quiet "$APP_NAME"; then
        log_error "El servicio $APP_NAME no está ejecutándose"
        ((errors++))
    fi
    
    # Verificar conectividad HTTP
    local app_url="http://localhost:5000"
    if curl -f -s "$app_url/health" >/dev/null 2>&1; then
        log_success "Aplicación responde correctamente en $app_url"
    else
        log_warning "La aplicación no responde en $app_url"
        ((errors++))
    fi
    
    # Verificar conexión a base de datos
    if [ -f "$APP_DIR/.env.production" ]; then
        source "$APP_DIR/.env.production"
        if [ ! -z "$DATABASE_URL" ]; then
            DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
            DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
            DB_USER=$(echo $DATABASE_URL | sed -n 's/.*\/\/\([^:]*\):.*/\1/p')
            DB_PASS=$(echo $DATABASE_URL | sed -n 's/.*\/\/[^:]*:\([^@]*\)@.*/\1/p')
            DB_NAME=$(echo $DATABASE_URL | sed -n 's/.*\/\([^?]*\).*/\1/p')
            
            if mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" -e "SELECT 1;" >/dev/null 2>&1; then
                log_success "Conexión a base de datos verificada"
            else
                log_error "Error de conexión a base de datos"
                ((errors++))
            fi
        fi
    fi
    
    # Verificar permisos de archivos
    if [ -d "$APP_DIR" ]; then
        if [ "$(stat -c %U "$APP_DIR")" = "www-data" ]; then
            log_success "Permisos de archivos correctos"
        else
            log_warning "Permisos de archivos incorrectos"
        fi
    fi
    
    if [ $errors -eq 0 ]; then
        log_success "✅ Verificación de restauración completada sin errores"
        return 0
    else
        log_error "❌ Verificación de restauración completada con $errors errores"
        return 1
    fi
}

# Rollback en caso de error
rollback_restoration() {
    log_warning "🔄 Iniciando rollback de la restauración..."
    
    # Detener servicios
    stop_services
    
    # Restaurar desde backup de seguridad
    if [ -f "/tmp/synapsis_last_safety_backup.txt" ]; then
        local safety_backup_dir=$(cat "/tmp/synapsis_last_safety_backup.txt")
        
        if [ -d "$safety_backup_dir" ]; then
            log_info "Restaurando desde backup de seguridad: $safety_backup_dir"
            
            # Restaurar aplicación
            if [ -f "$safety_backup_dir/current_app.tar.gz" ]; then
                rm -rf "$APP_DIR"
                mkdir -p "$APP_DIR"
                tar -xzf "$safety_backup_dir/current_app.tar.gz" -C "$APP_DIR"
                chown -R www-data:www-data "$APP_DIR"
            fi
            
            # Restaurar base de datos
            if [ -f "$safety_backup_dir/current_database.sql.gz" ] && [ -f "$APP_DIR/.env.production" ]; then
                source "$APP_DIR/.env.production"
                if [ ! -z "$DATABASE_URL" ]; then
                    DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
                    DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
                    DB_USER=$(echo $DATABASE_URL | sed -n 's/.*\/\/\([^:]*\):.*/\1/p')
                    DB_PASS=$(echo $DATABASE_URL | sed -n 's/.*\/\/[^:]*:\([^@]*\)@.*/\1/p')
                    DB_NAME=$(echo $DATABASE_URL | sed -n 's/.*\/\([^?]*\).*/\1/p')
                    
                    gunzip -c "$safety_backup_dir/current_database.sql.gz" | mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME"
                fi
            fi
            
            log_success "Rollback completado desde backup de seguridad"
        fi
    fi
    
    # Iniciar servicios
    start_services
}

# Función principal de restauración
perform_restoration() {
    local backup_path="$1"
    local skip_confirmation="$2"
    
    log_info "🔄 Iniciando restauración desde: $backup_path"
    
    # Verificar integridad del backup
    if ! verify_backup_integrity "$backup_path"; then
        log_error "El backup no pasó la verificación de integridad"
        exit 1
    fi
    
    # Mostrar información del backup
    if [ -f "$backup_path/backup_metadata.json" ]; then
        echo ""
        echo "📋 Información del backup:"
        cat "$backup_path/backup_metadata.json" | jq . 2>/dev/null || cat "$backup_path/backup_metadata.json"
        echo ""
    fi
    
    # Confirmación del usuario
    if [ "$skip_confirmation" != "--yes" ]; then
        echo -e "${YELLOW}⚠️  ADVERTENCIA: Esta operación sobrescribirá los datos actuales${NC}"
        echo -e "${YELLOW}⚠️  Se creará un backup de seguridad antes de proceder${NC}"
        echo ""
        read -p "¿Continuar con la restauración? (yes/no): " confirm
        if [ "$confirm" != "yes" ]; then
            log_info "Restauración cancelada por el usuario"
            exit 0
        fi
    fi
    
    local start_time=$(date +%s)
    local errors=0
    
    # Crear backup de seguridad
    create_safety_backup
    
    # Detener servicios
    stop_services
    
    # Ejecutar restauración
    restore_application "$backup_path" || ((errors++))
    restore_database "$backup_path" || ((errors++))
    restore_uploads "$backup_path"
    restore_configs "$backup_path"
    
    # Iniciar servicios
    if ! start_services; then
        ((errors++))
    fi
    
    # Verificar restauración
    sleep 10  # Esperar a que los servicios se estabilicen
    if ! verify_restoration; then
        ((errors++))
    fi
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    if [ $errors -eq 0 ]; then
        log_success "✅ Restauración completada exitosamente en ${duration}s"
        
        # Limpiar backup de seguridad después de verificación exitosa
        if [ -f "/tmp/synapsis_last_safety_backup.txt" ]; then
            local safety_backup_dir=$(cat "/tmp/synapsis_last_safety_backup.txt")
            if [ -d "$safety_backup_dir" ]; then
                rm -rf "$safety_backup_dir"
                rm -f "/tmp/synapsis_last_safety_backup.txt"
                log_info "Backup de seguridad limpiado"
            fi
        fi
    else
        log_error "❌ Restauración completada con $errors errores"
        echo ""
        echo -e "${YELLOW}¿Desea hacer rollback a la versión anterior? (yes/no):${NC}"
        read -p "" rollback_confirm
        if [ "$rollback_confirm" = "yes" ]; then
            rollback_restoration
        fi
    fi
    
    return $errors
}

# Listar backups disponibles
list_available_backups() {
    echo "📋 Backups disponibles para restauración:"
    echo ""
    
    for type in daily weekly monthly; do
        echo "=== Backups $type ==="
        if [ -d "$BACKUP_DIR/$type" ]; then
            for backup_dir in "$BACKUP_DIR/$type"/*; do
                if [ -d "$backup_dir" ]; then
                    local backup_name=$(basename "$backup_dir")
                    local backup_size=$(du -sh "$backup_dir" 2>/dev/null | cut -f1)
                    local backup_date=$(date -d "${backup_name:0:8}" +"%Y-%m-%d" 2>/dev/null || echo "Fecha inválida")
                    
                    echo "  📁 $backup_name"
                    echo "     Fecha: $backup_date"
                    echo "     Tamaño: $backup_size"
                    
                    if [ -f "$backup_dir/backup_metadata.json" ]; then
                        local git_commit=$(cat "$backup_dir/backup_metadata.json" | jq -r '.git_commit' 2>/dev/null || echo "unknown")
                        echo "     Commit: $git_commit"
                    fi
                    echo ""
                fi
            done
        else
            echo "  No hay backups $type disponibles"
        fi
        echo ""
    done
}

# Mostrar ayuda
show_help() {
    echo "Script de Restauración - Synapsis Apoyos"
    echo ""
    echo "Uso: $0 [COMANDO] [OPCIONES]"
    echo ""
    echo "Comandos:"
    echo "  restore <ruta_backup> [--yes]  Restaurar desde backup específico"
    echo "  list                           Listar backups disponibles"
    echo "  verify <ruta_backup>           Verificar integridad de backup"
    echo "  rollback                       Rollback a backup de seguridad"
    echo "  help                           Mostrar esta ayuda"
    echo ""
    echo "Opciones:"
    echo "  --yes                          Omitir confirmación (usar con precaución)"
    echo ""
    echo "Ejemplos:"
    echo "  $0 list"
    echo "  $0 restore /opt/backups/synapsis_apoyos/daily/20240115_143000"
    echo "  $0 restore /opt/backups/synapsis_apoyos/daily/20240115_143000 --yes"
    echo "  $0 verify /opt/backups/synapsis_apoyos/daily/20240115_143000"
}

# Función principal
main() {
    # Verificar permisos de root
    check_root
    
    # Crear directorio de logs si no existe
    mkdir -p "$(dirname "$RESTORE_LOG")"
    
    case "${1:-help}" in
        "restore")
            if [ -z "$2" ]; then
                log_error "Especifica la ruta del backup a restaurar"
                show_help
                exit 1
            fi
            perform_restoration "$2" "$3"
            ;;
        "list")
            list_available_backups
            ;;
        "verify")
            if [ -z "$2" ]; then
                log_error "Especifica la ruta del backup a verificar"
                show_help
                exit 1
            fi
            verify_backup_integrity "$2"
            ;;
        "rollback")
            rollback_restoration
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            log_error "Comando no válido: $1"
            show_help
            exit 1
            ;;
    esac
}

# Ejecutar función principal
main "$@"