# Guía de Deployment - Synapsis Apoyos

## Tabla de Contenidos
1. [Requisitos del Sistema](#requisitos-del-sistema)
2. [Preparación del Entorno](#preparación-del-entorno)
3. [Configuración de Base de Datos](#configuración-de-base-de-datos)
4. [Configuración del Servidor Web](#configuración-del-servidor-web)
5. [Configuración de SSL/HTTPS](#configuración-de-sslhttps)
6. [Deployment Automatizado](#deployment-automatizado)
7. [Monitoreo y Logging](#monitoreo-y-logging)
8. [Backup y Restauración](#backup-y-restauración)
9. [Troubleshooting](#troubleshooting)
10. [Mantenimiento](#mantenimiento)

## Requisitos del Sistema

### Servidor de Producción
- **OS**: Ubuntu 20.04 LTS o superior / CentOS 8+ / RHEL 8+
- **RAM**: Mínimo 4GB, recomendado 8GB+
- **CPU**: Mínimo 2 cores, recomendado 4+ cores
- **Almacenamiento**: Mínimo 50GB SSD
- **Red**: Conexión estable a internet

### Software Requerido
```bash
# Python 3.8+
python3 --version

# Base de datos (MySQL/PostgreSQL)
mysql --version
# o
psql --version

# Nginx
nginx -v

# Git
git --version

# Node.js (para optimización de assets)
node --version
npm --version
```

## Preparación del Entorno

### 1. Crear Usuario del Sistema
```bash
# Crear usuario dedicado para la aplicación
sudo adduser synapsis
sudo usermod -aG sudo synapsis
sudo su - synapsis
```

### 2. Clonar el Repositorio
```bash
cd /home/synapsis
git clone https://github.com/tu-usuario/synapsis_apoyos.git
cd synapsis_apoyos
```

### 3. Configurar Entorno Virtual
```bash
# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno
```bash
# Copiar archivo de configuración
cp .env.example .env.production

# Editar configuración de producción
nano .env.production
```

**Configuración mínima requerida:**
```env
# Entorno
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=tu_clave_secreta_muy_segura_aqui

# Base de datos
DATABASE_URL=mysql://usuario:password@localhost/synapsis_apoyos
# o para PostgreSQL
# DATABASE_URL=postgresql://usuario:password@localhost/synapsis_apoyos

# Email
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=tu_email@gmail.com
MAIL_PASSWORD=tu_password_de_aplicacion

# Seguridad
WTF_CSRF_ENABLED=True
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/synapsis_apoyos/app.log

# Uploads
UPLOAD_FOLDER=/var/uploads/synapsis_apoyos
MAX_CONTENT_LENGTH=16777216

# CDN (opcional)
CDN_DOMAIN=cdn.tudominio.com
CDN_HTTPS=True
```

## Configuración de Base de Datos

### MySQL
```bash
# Instalar MySQL
sudo apt update
sudo apt install mysql-server

# Configurar MySQL
sudo mysql_secure_installation

# Crear base de datos y usuario
sudo mysql -u root -p
```

```sql
CREATE DATABASE synapsis_apoyos CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'synapsis_user'@'localhost' IDENTIFIED BY 'password_seguro';
GRANT ALL PRIVILEGES ON synapsis_apoyos.* TO 'synapsis_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### PostgreSQL
```bash
# Instalar PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Crear base de datos y usuario
sudo -u postgres psql
```

```sql
CREATE DATABASE synapsis_apoyos;
CREATE USER synapsis_user WITH PASSWORD 'password_seguro';
GRANT ALL PRIVILEGES ON DATABASE synapsis_apoyos TO synapsis_user;
\q
```

### Ejecutar Migraciones
```bash
# Activar entorno virtual
source venv/bin/activate

# Ejecutar migraciones
flask db upgrade

# Crear datos iniciales (opcional)
flask seed-db
```

## Configuración del Servidor Web

### 1. Instalar y Configurar Gunicorn
```bash
# Gunicorn ya está incluido en requirements.txt
# Crear archivo de configuración
cp gunicorn.conf.py /home/synapsis/synapsis_apoyos/
```

### 2. Crear Servicio Systemd
```bash
sudo nano /etc/systemd/system/synapsis-apoyos.service
```

```ini
[Unit]
Description=Synapsis Apoyos WSGI Server
After=network.target

[Service]
User=synapsis
Group=synapsis
WorkingDirectory=/home/synapsis/synapsis_apoyos
Environment="PATH=/home/synapsis/synapsis_apoyos/venv/bin"
ExecStart=/home/synapsis/synapsis_apoyos/venv/bin/gunicorn --config gunicorn.conf.py wsgi:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

```bash
# Habilitar y iniciar el servicio
sudo systemctl daemon-reload
sudo systemctl enable synapsis-apoyos
sudo systemctl start synapsis-apoyos
sudo systemctl status synapsis-apoyos
```

### 3. Instalar y Configurar Nginx
```bash
# Instalar Nginx
sudo apt install nginx

# Copiar configuración
sudo cp nginx/synapsis_apoyos.conf /etc/nginx/sites-available/
sudo cp nginx/proxy_params /etc/nginx/

# Habilitar sitio
sudo ln -s /etc/nginx/sites-available/synapsis_apoyos.conf /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default

# Verificar configuración
sudo nginx -t

# Reiniciar Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

## Configuración de SSL/HTTPS

### Opción 1: Let's Encrypt (Recomendado)
```bash
# Ejecutar script de configuración SSL
chmod +x scripts/setup_ssl.sh
sudo ./scripts/setup_ssl.sh tudominio.com
```

### Opción 2: Certificado Auto-firmado (Solo para desarrollo)
```bash
# Generar certificado auto-firmado
chmod +x scripts/generate_self_signed_ssl.sh
sudo ./scripts/generate_self_signed_ssl.sh tudominio.com
```

### Verificar SSL
```bash
# Verificar certificado
openssl x509 -in /etc/ssl/certs/synapsis_apoyos.crt -text -noout

# Probar conexión SSL
curl -I https://tudominio.com
```

## Deployment Automatizado

### Usar Script de Deployment
```bash
# Hacer ejecutable el script
chmod +x scripts/deploy.sh

# Ejecutar deployment
sudo ./scripts/deploy.sh
```

### Deployment Manual
```bash
# 1. Detener servicios
sudo systemctl stop synapsis-apoyos
sudo systemctl stop nginx

# 2. Backup actual
./scripts/backup.sh

# 3. Actualizar código
git pull origin main

# 4. Instalar dependencias
source venv/bin/activate
pip install -r requirements.txt

# 5. Ejecutar migraciones
flask db upgrade

# 6. Compilar assets (si aplica)
npm install
npm run build

# 7. Reiniciar servicios
sudo systemctl start synapsis-apoyos
sudo systemctl start nginx

# 8. Verificar deployment
curl -I https://tudominio.com/health
```

## Monitoreo y Logging

### 1. Configurar Logging
```bash
# Crear directorios de logs
sudo mkdir -p /var/log/synapsis_apoyos
sudo chown synapsis:synapsis /var/log/synapsis_apoyos

# Configurar rotación de logs
sudo nano /etc/logrotate.d/synapsis_apoyos
```

```
/var/log/synapsis_apoyos/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 synapsis synapsis
    postrotate
        systemctl reload synapsis-apoyos
    endscript
}
```

### 2. Configurar Monitoreo (Opcional)
```bash
# Instalar herramientas de monitoreo
chmod +x scripts/setup_monitoring.sh
sudo ./scripts/setup_monitoring.sh
```

### 3. Verificar Logs
```bash
# Ver logs de la aplicación
tail -f /var/log/synapsis_apoyos/app.log

# Ver logs de Gunicorn
sudo journalctl -u synapsis-apoyos -f

# Ver logs de Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## Backup y Restauración

### Configurar Backups Automáticos
```bash
# Hacer ejecutable el script de backup
chmod +x scripts/backup.sh

# Configurar cron para backups automáticos
crontab -e
```

```cron
# Backup diario a las 2:00 AM
0 2 * * * /home/synapsis/synapsis_apoyos/scripts/backup.sh daily

# Backup semanal los domingos a las 3:00 AM
0 3 * * 0 /home/synapsis/synapsis_apoyos/scripts/backup.sh weekly

# Backup mensual el primer día del mes a las 4:00 AM
0 4 1 * * /home/synapsis/synapsis_apoyos/scripts/backup.sh monthly
```

### Realizar Backup Manual
```bash
# Backup completo
./scripts/backup.sh

# Backup específico
./scripts/backup.sh daily
```

### Restaurar desde Backup
```bash
# Listar backups disponibles
./scripts/restore.sh list

# Restaurar backup específico
./scripts/restore.sh /path/to/backup/file.tar.gz
```

## Troubleshooting

### Problemas Comunes

#### 1. Error 502 Bad Gateway
```bash
# Verificar estado de Gunicorn
sudo systemctl status synapsis-apoyos

# Verificar logs
sudo journalctl -u synapsis-apoyos --no-pager

# Verificar configuración de Nginx
sudo nginx -t
```

#### 2. Error de Base de Datos
```bash
# Verificar conexión a la base de datos
mysql -u synapsis_user -p synapsis_apoyos
# o
psql -U synapsis_user -d synapsis_apoyos

# Verificar migraciones
flask db current
flask db upgrade
```

#### 3. Problemas de Permisos
```bash
# Verificar permisos de archivos
ls -la /home/synapsis/synapsis_apoyos/

# Corregir permisos
sudo chown -R synapsis:synapsis /home/synapsis/synapsis_apoyos/
sudo chmod -R 755 /home/synapsis/synapsis_apoyos/
```

#### 4. Error de SSL
```bash
# Verificar certificados
sudo certbot certificates

# Renovar certificados
sudo certbot renew --dry-run
```

### Comandos de Diagnóstico
```bash
# Verificar servicios
sudo systemctl status synapsis-apoyos nginx mysql

# Verificar puertos
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :443
sudo netstat -tlnp | grep :8000

# Verificar espacio en disco
df -h

# Verificar memoria
free -h

# Verificar procesos
ps aux | grep gunicorn
ps aux | grep nginx
```

## Mantenimiento

### Tareas Regulares

#### Diarias
- Verificar logs de errores
- Monitorear uso de recursos
- Verificar backups automáticos

#### Semanales
- Actualizar dependencias de seguridad
- Revisar métricas de rendimiento
- Limpiar logs antiguos

#### Mensuales
- Actualizar sistema operativo
- Revisar y optimizar base de datos
- Actualizar certificados SSL
- Revisar configuración de seguridad

### Scripts de Mantenimiento
```bash
# Actualizar dependencias
pip list --outdated
pip install --upgrade package_name

# Limpiar archivos temporales
find /tmp -name "*.tmp" -mtime +7 -delete

# Optimizar base de datos MySQL
mysqlcheck -u root -p --optimize --all-databases

# Verificar integridad de backups
./scripts/backup.sh verify
```

### Actualizaciones de Seguridad
```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade

# CentOS/RHEL
sudo yum update

# Reiniciar servicios si es necesario
sudo systemctl restart synapsis-apoyos
```

## Contacto y Soporte

Para soporte técnico o consultas sobre el deployment:
- **Email**: soporte@synapsis.com
- **Documentación**: https://docs.synapsis.com
- **Issues**: https://github.com/tu-usuario/synapsis_apoyos/issues

---

**Nota**: Esta documentación debe mantenerse actualizada con cada cambio en el proceso de deployment. Siempre probar los procedimientos en un entorno de desarrollo antes de aplicarlos en producción.