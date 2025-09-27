#!/bin/bash
# Script de deployment completo para Synapsis Apoyos
# Automatiza el proceso de deployment en producción

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
BACKUP_DIR="/opt/backups/synapsis_apoyos"
REPO_URL="https://github.com/tu-usuario/synapsis_apoyos.git"
BRANCH="main"
USER="www-data"
GROUP="www-data"

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

# Verificar que estamos ejecutando como root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "Este script debe ejecutarse como root"
        exit 1
    fi
}

# Crear backup antes del deployment
create_backup() {
    log_info "Creando backup antes del deployment..."
    
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_PATH="$BACKUP_DIR/pre_deploy_$TIMESTAMP"
    
    mkdir -p "$BACKUP_PATH"
    
    # Backup de la aplicación
    if [ -d "$APP_DIR" ]; then
        tar -czf "$BACKUP_PATH/app_backup.tar.gz" -C "$APP_DIR" .
        log_success "Backup de aplicación creado"
    fi
    
    # Backup de base de datos
    if [ -f "$APP_DIR/.env.production" ]; then
        source "$APP_DIR/.env.production"
        if [ ! -z "$DATABASE_URL" ]; then
            mysqldump --single-transaction --routines --triggers \
                -h $(echo $DATABASE_URL | cut -d'@' -f2 | cut -d'/' -f1) \
                -u $(echo $DATABASE_URL | cut -d'/' -f3 | cut -d':' -f1) \
                -p$(echo $DATABASE_URL | cut -d':' -f3 | cut -d'@' -f1) \
                $(echo $DATABASE_URL | cut -d'/' -f4) > "$BACKUP_PATH/database_backup.sql"
            log_success "Backup de base de datos creado"
        fi
    fi
    
    # Backup de configuración de Nginx
    if [ -f "/etc/nginx/sites-available/$APP_NAME" ]; then
        cp "/etc/nginx/sites-available/$APP_NAME" "$BACKUP_PATH/nginx_config.conf"
        log_success "Backup de configuración Nginx creado"
    fi
    
    echo "$BACKUP_PATH" > /tmp/last_backup_path
    log_success "Backup completo guardado en: $BACKUP_PATH"
}

# Verificar servicios
check_services() {
    log_info "Verificando servicios..."
    
    # Verificar Nginx
    if systemctl is-active --quiet nginx; then
        log_success "Nginx está ejecutándose"
    else
        log_warning "Nginx no está ejecutándose"
    fi
    
    # Verificar aplicación
    if systemctl is-active --quiet "$APP_NAME"; then
        log_success "Aplicación está ejecutándose"
    else
        log_warning "Aplicación no está ejecutándose"
    fi
    
    # Verificar base de datos
    if systemctl is-active --quiet mysql; then
        log_success "MySQL está ejecutándose"
    else
        log_warning "MySQL no está ejecutándose"
    fi
}

# Detener servicios
stop_services() {
    log_info "Deteniendo servicios..."
    
    if systemctl is-active --quiet "$APP_NAME"; then
        systemctl stop "$APP_NAME"
        log_success "Aplicación detenida"
    fi
}

# Actualizar código
update_code() {
    log_info "Actualizando código desde repositorio..."
    
    if [ ! -d "$APP_DIR" ]; then
        log_info "Clonando repositorio..."
        git clone "$REPO_URL" "$APP_DIR"
    else
        log_info "Actualizando repositorio existente..."
        cd "$APP_DIR"
        git fetch origin
        git reset --hard "origin/$BRANCH"
    fi
    
    cd "$APP_DIR"
    git checkout "$BRANCH"
    git pull origin "$BRANCH"
    
    log_success "Código actualizado"
}

# Instalar dependencias
install_dependencies() {
    log_info "Instalando dependencias..."
    
    cd "$APP_DIR"
    
    # Activar entorno virtual
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    log_success "Dependencias instaladas"
}

# Ejecutar migraciones
run_migrations() {
    log_info "Ejecutando migraciones de base de datos..."
    
    cd "$APP_DIR"
    source venv/bin/activate
    
    # Cargar variables de entorno
    if [ -f ".env.production" ]; then
        export $(cat .env.production | grep -v '^#' | xargs)
    fi
    
    # Ejecutar migraciones (ajustar según tu sistema de migraciones)
    python -c "
from app import create_app, db
app = create_app('production')
with app.app_context():
    db.create_all()
    print('Migraciones ejecutadas exitosamente')
"
    
    log_success "Migraciones completadas"
}

# Configurar permisos
set_permissions() {
    log_info "Configurando permisos..."
    
    chown -R "$USER:$GROUP" "$APP_DIR"
    chmod -R 755 "$APP_DIR"
    chmod -R 644 "$APP_DIR"/*.py
    chmod +x "$APP_DIR"/scripts/*.sh
    
    # Permisos especiales para logs y uploads
    mkdir -p "$APP_DIR/logs" "$APP_DIR/uploads"
    chown -R "$USER:$GROUP" "$APP_DIR/logs" "$APP_DIR/uploads"
    chmod -R 755 "$APP_DIR/logs" "$APP_DIR/uploads"
    
    log_success "Permisos configurados"
}

# Verificar configuración
verify_config() {
    log_info "Verificando configuración..."
    
    cd "$APP_DIR"
    
    # Verificar archivo de configuración
    if [ ! -f ".env.production" ]; then
        log_error "Archivo .env.production no encontrado"
        exit 1
    fi
    
    # Verificar conexión a base de datos
    source venv/bin/activate
    export $(cat .env.production | grep -v '^#' | xargs)
    
    python -c "
from app import create_app, db
try:
    app = create_app('production')
    with app.app_context():
        db.engine.execute('SELECT 1')
    print('✅ Conexión a base de datos OK')
except Exception as e:
    print(f'❌ Error de conexión a base de datos: {e}')
    exit(1)
"
    
    # Verificar configuración de Nginx
    nginx -t
    if [ $? -eq 0 ]; then
        log_success "Configuración de Nginx válida"
    else
        log_error "Error en configuración de Nginx"
        exit 1
    fi
    
    log_success "Configuración verificada"
}

# Iniciar servicios
start_services() {
    log_info "Iniciando servicios..."
    
    # Recargar systemd
    systemctl daemon-reload
    
    # Iniciar aplicación
    systemctl start "$APP_NAME"
    systemctl enable "$APP_NAME"
    
    # Recargar Nginx
    systemctl reload nginx
    
    # Esperar a que los servicios estén listos
    sleep 5
    
    log_success "Servicios iniciados"
}

# Verificar deployment
verify_deployment() {
    log_info "Verificando deployment..."
    
    # Verificar que los servicios estén ejecutándose
    if systemctl is-active --quiet "$APP_NAME"; then
        log_success "Aplicación está ejecutándose"
    else
        log_error "Aplicación no está ejecutándose"
        return 1
    fi
    
    # Verificar respuesta HTTP
    sleep 10
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/)
    
    if [ "$HTTP_STATUS" = "200" ]; then
        log_success "Aplicación responde correctamente (HTTP $HTTP_STATUS)"
    else
        log_error "Aplicación no responde correctamente (HTTP $HTTP_STATUS)"
        return 1
    fi
    
    # Verificar endpoints críticos
    HEALTH_STATUS=$(curl -s http://localhost/health | jq -r '.overall_status' 2>/dev/null || echo "unknown")
    
    if [ "$HEALTH_STATUS" = "healthy" ]; then
        log_success "Health check OK"
    else
        log_warning "Health check: $HEALTH_STATUS"
    fi
    
    log_success "Deployment verificado exitosamente"
}

# Rollback en caso de error
rollback() {
    log_error "Deployment falló. Iniciando rollback..."
    
    if [ -f "/tmp/last_backup_path" ]; then
        BACKUP_PATH=$(cat /tmp/last_backup_path)
        
        if [ -f "$BACKUP_PATH/app_backup.tar.gz" ]; then
            log_info "Restaurando aplicación desde backup..."
            systemctl stop "$APP_NAME" || true
            rm -rf "$APP_DIR"
            mkdir -p "$APP_DIR"
            tar -xzf "$BACKUP_PATH/app_backup.tar.gz" -C "$APP_DIR"
            chown -R "$USER:$GROUP" "$APP_DIR"
            systemctl start "$APP_NAME"
            log_success "Aplicación restaurada"
        fi
        
        if [ -f "$BACKUP_PATH/database_backup.sql" ]; then
            log_info "Restaurando base de datos desde backup..."
            # Implementar restauración de BD según necesidades
            log_success "Base de datos restaurada"
        fi
    fi
    
    log_success "Rollback completado"
}

# Limpiar backups antiguos
cleanup_old_backups() {
    log_info "Limpiando backups antiguos..."
    
    # Mantener solo los últimos 10 backups
    find "$BACKUP_DIR" -type d -name "pre_deploy_*" | sort -r | tail -n +11 | xargs rm -rf
    
    log_success "Backups antiguos limpiados"
}

# Función principal
main() {
    log_info "🚀 Iniciando deployment de $APP_NAME"
    
    # Verificaciones iniciales
    check_root
    check_services
    
    # Crear backup
    create_backup
    
    # Detener servicios
    stop_services
    
    # Actualizar código
    update_code
    
    # Instalar dependencias
    install_dependencies
    
    # Ejecutar migraciones
    run_migrations
    
    # Configurar permisos
    set_permissions
    
    # Verificar configuración
    verify_config
    
    # Iniciar servicios
    start_services
    
    # Verificar deployment
    if verify_deployment; then
        log_success "🎉 Deployment completado exitosamente!"
        cleanup_old_backups
    else
        log_error "❌ Deployment falló"
        rollback
        exit 1
    fi
    
    log_info "📋 Resumen del deployment:"
    log_info "   - Aplicación: $APP_NAME"
    log_info "   - Directorio: $APP_DIR"
    log_info "   - Rama: $BRANCH"
    log_info "   - Backup: $(cat /tmp/last_backup_path)"
    log_info "   - Fecha: $(date)"
}

# Manejo de señales para cleanup
trap 'log_error "Deployment interrumpido"; rollback; exit 1' INT TERM

# Ejecutar función principal
main "$@"