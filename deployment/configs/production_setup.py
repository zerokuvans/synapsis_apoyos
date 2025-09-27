#!/usr/bin/env python3
"""
Script de configuración para producción de Synapsis Apoyos
Ejecutar este script para preparar la aplicación para producción
"""

import os
import sys
import secrets
import subprocess
from pathlib import Path

def generate_secret_key():
    """Genera una clave secreta segura"""
    return secrets.token_urlsafe(32)

def create_production_env():
    """Crea el archivo .env para producción"""
    secret_key = generate_secret_key()
    
    env_content = f"""# ========================================
# CONFIGURACIÓN DE PRODUCCIÓN - SYNAPSIS APOYOS
# ========================================
# IMPORTANTE: Configura todos los valores antes de desplegar

# Configuración de la aplicación
SECRET_KEY={secret_key}
FLASK_ENV=production
FLASK_DEBUG=False
FLASK_HOST=0.0.0.0
FLASK_PORT=5000

# API Keys (CONFIGURAR ANTES DE DESPLEGAR)
GOOGLE_MAPS_API_KEY=TU_GOOGLE_MAPS_API_KEY_REAL

# Configuración de base de datos de producción
# Formato: mysql+pymysql://usuario:password@host:puerto/nombre_bd
DATABASE_URL=mysql+pymysql://synapsis_user:PASSWORD_SEGURA@localhost:3306/synapsis_apoyos_prod

# Configuración de correo electrónico de producción
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=noreply@tudominio.com
MAIL_PASSWORD=TU_APP_PASSWORD_REAL
MAIL_DEFAULT_SENDER=Synapsis Apoyos <noreply@tudominio.com>

# Configuración de logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/synapsis_apoyos/app.log

# Configuración de Sentry (opcional, para monitoreo de errores)
# SENTRY_DSN=https://tu_sentry_dsn_aqui

# ========================================
# CHECKLIST ANTES DE PRODUCCIÓN:
# ========================================
# [ ] Cambiar GOOGLE_MAPS_API_KEY por tu clave real
# [ ] Configurar DATABASE_URL con datos reales de producción
# [ ] Configurar email corporativo real
# [ ] Configurar dominio y SSL
# [ ] Crear usuario de base de datos con permisos limitados
# [ ] Configurar backup automático de base de datos
# [ ] Configurar monitoreo y alertas
# [ ] Revisar permisos de archivos y directorios
# [ ] Configurar firewall
"""
    
    with open('.env.production', 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("✅ Archivo .env.production creado con clave secreta generada")
    print("⚠️  IMPORTANTE: Configura todas las variables antes de desplegar")

def create_database_setup_script():
    """Crea script SQL para configurar la base de datos de producción"""
    sql_content = """-- ========================================
-- CONFIGURACIÓN DE BASE DE DATOS PARA PRODUCCIÓN
-- ========================================

-- Crear base de datos
CREATE DATABASE IF NOT EXISTS synapsis_apoyos_prod 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- Crear usuario específico para la aplicación
CREATE USER IF NOT EXISTS 'synapsis_user'@'localhost' IDENTIFIED BY 'CAMBIAR_PASSWORD_AQUI';

-- Otorgar permisos específicos (principio de menor privilegio)
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX, DROP 
ON synapsis_apoyos_prod.* 
TO 'synapsis_user'@'localhost';

-- Aplicar cambios
FLUSH PRIVILEGES;

-- Verificar usuario creado
SELECT User, Host FROM mysql.user WHERE User = 'synapsis_user';

-- ========================================
-- INSTRUCCIONES:
-- ========================================
-- 1. Cambiar 'CAMBIAR_PASSWORD_AQUI' por una contraseña segura
-- 2. Ejecutar este script como root: mysql -u root -p < database_setup.sql
-- 3. Actualizar DATABASE_URL en .env.production con los datos reales
-- 4. Ejecutar las migraciones: python -c "from app import create_app, db; app=create_app('production'); app.app_context().push(); db.create_all()"
"""
    
    with open('database_setup.sql', 'w', encoding='utf-8') as f:
        f.write(sql_content)
    
    print("✅ Script database_setup.sql creado")

def create_gunicorn_config():
    """Crea configuración para Gunicorn"""
    gunicorn_config = """# Configuración de Gunicorn para Synapsis Apoyos
import multiprocessing
import os

# Configuración del servidor
bind = "127.0.0.1:5000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gevent"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2

# Configuración de archivos
user = "www-data"  # Cambiar por el usuario apropiado
group = "www-data"  # Cambiar por el grupo apropiado
tmp_upload_dir = None
secure_scheme_headers = {
    'X-FORWARDED-PROTOCOL': 'ssl',
    'X-FORWARDED-PROTO': 'https',
    'X-FORWARDED-SSL': 'on'
}

# Logging
accesslog = "/var/log/synapsis_apoyos/gunicorn_access.log"
errorlog = "/var/log/synapsis_apoyos/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Configuración de proceso
pidfile = "/var/run/synapsis_apoyos/gunicorn.pid"
daemon = False
preload_app = True

# Configuración de memoria
max_requests_jitter = 100
worker_tmp_dir = "/dev/shm"

# Hooks
def when_ready(server):
    server.log.info("Synapsis Apoyos server is ready. Listening on: %s", server.address)

def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")

def pre_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)
"""
    
    with open('gunicorn.conf.py', 'w', encoding='utf-8') as f:
        f.write(gunicorn_config)
    
    print("✅ Configuración de Gunicorn creada")

def create_nginx_config():
    """Crea configuración de ejemplo para Nginx"""
    nginx_config = """# Configuración de Nginx para Synapsis Apoyos
# Guardar como: /etc/nginx/sites-available/synapsis_apoyos

server {
    listen 80;
    server_name tudominio.com www.tudominio.com;
    
    # Redirigir HTTP a HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name tudominio.com www.tudominio.com;
    
    # Configuración SSL
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Headers de seguridad
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";
    
    # Configuración de archivos estáticos
    location /static {
        alias /path/to/synapsis_apoyos/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }
    
    # Configuración de uploads (si los hay)
    location /uploads {
        alias /path/to/synapsis_apoyos/uploads;
        expires 1y;
        add_header Cache-Control "public";
    }
    
    # Proxy a la aplicación Flask
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
        
        # Configuración para WebSockets
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 128k;
        proxy_buffers 4 256k;
        proxy_busy_buffers_size 256k;
    }
    
    # Configuración de logs
    access_log /var/log/nginx/synapsis_apoyos_access.log;
    error_log /var/log/nginx/synapsis_apoyos_error.log;
    
    # Configuración de límites
    client_max_body_size 16M;
    client_body_timeout 60s;
    client_header_timeout 60s;
}
"""
    
    with open('nginx_synapsis_apoyos.conf', 'w', encoding='utf-8') as f:
        f.write(nginx_config)
    
    print("✅ Configuración de Nginx creada")

def create_systemd_service():
    """Crea archivo de servicio systemd"""
    service_content = """[Unit]
Description=Synapsis Apoyos - Sistema de Gestión de Apoyos
After=network.target mysql.service
Requires=mysql.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/path/to/synapsis_apoyos
Environment=PATH=/path/to/synapsis_apoyos/venv/bin
Environment=FLASK_ENV=production
EnvironmentFile=/path/to/synapsis_apoyos/.env.production
ExecStart=/path/to/synapsis_apoyos/venv/bin/gunicorn --config gunicorn.conf.py run:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=10
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/path/to/synapsis_apoyos/logs
ReadWritePaths=/var/log/synapsis_apoyos
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
"""
    
    with open('synapsis_apoyos.service', 'w', encoding='utf-8') as f:
        f.write(service_content)
    
    print("✅ Archivo de servicio systemd creado")

def create_deployment_script():
    """Crea script de deployment"""
    deploy_script = """#!/bin/bash
# Script de deployment para Synapsis Apoyos

set -e

echo "🚀 Iniciando deployment de Synapsis Apoyos..."

# Variables
APP_DIR="/path/to/synapsis_apoyos"
BACKUP_DIR="/backups/synapsis_apoyos"
VENV_DIR="$APP_DIR/venv"

# Crear backup de la base de datos
echo "📦 Creando backup de base de datos..."
mkdir -p $BACKUP_DIR
mysqldump -u synapsis_user -p synapsis_apoyos_prod > "$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql"

# Activar entorno virtual
echo "🔧 Activando entorno virtual..."
source $VENV_DIR/bin/activate

# Actualizar dependencias
echo "📚 Actualizando dependencias..."
pip install -r requirements.txt

# Ejecutar migraciones de base de datos
echo "🗄️ Ejecutando migraciones..."
python -c "from app import create_app, db; app=create_app('production'); app.app_context().push(); db.create_all()"

# Recolectar archivos estáticos (si es necesario)
echo "📁 Procesando archivos estáticos..."
# Aquí puedes agregar comandos para minificar CSS/JS si es necesario

# Reiniciar servicios
echo "🔄 Reiniciando servicios..."
sudo systemctl reload synapsis_apoyos
sudo systemctl reload nginx

# Verificar que los servicios estén funcionando
echo "✅ Verificando servicios..."
sleep 5
if systemctl is-active --quiet synapsis_apoyos; then
    echo "✅ Synapsis Apoyos está funcionando"
else
    echo "❌ Error: Synapsis Apoyos no está funcionando"
    exit 1
fi

if systemctl is-active --quiet nginx; then
    echo "✅ Nginx está funcionando"
else
    echo "❌ Error: Nginx no está funcionando"
    exit 1
fi

echo "🎉 Deployment completado exitosamente!"
"""
    
    with open('deploy.sh', 'w', encoding='utf-8') as f:
        f.write(deploy_script)
    
    # Hacer el script ejecutable
    os.chmod('deploy.sh', 0o755)
    
    print("✅ Script de deployment creado")

def main():
    """Función principal"""
    print("🔧 Configurando Synapsis Apoyos para producción...\n")
    
    try:
        create_production_env()
        create_database_setup_script()
        create_gunicorn_config()
        create_nginx_config()
        create_systemd_service()
        create_deployment_script()
        
        print("\n🎉 Configuración de producción completada!")
        print("\n📋 PRÓXIMOS PASOS:")
        print("1. Editar .env.production con tus datos reales")
        print("2. Ejecutar database_setup.sql en MySQL")
        print("3. Instalar dependencias: pip install -r requirements.txt")
        print("4. Configurar Nginx con nginx_synapsis_apoyos.conf")
        print("5. Instalar servicio systemd: sudo cp synapsis_apoyos.service /etc/systemd/system/")
        print("6. Habilitar servicio: sudo systemctl enable synapsis_apoyos")
        print("7. Configurar SSL/HTTPS")
        print("8. Ejecutar deploy.sh para deployment")
        
        print("\n⚠️  IMPORTANTE:")
        print("- Cambiar todas las contraseñas por valores seguros")
        print("- Configurar firewall apropiadamente")
        print("- Configurar backup automático")
        print("- Revisar logs regularmente")
        
    except Exception as e:
        print(f"❌ Error durante la configuración: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()