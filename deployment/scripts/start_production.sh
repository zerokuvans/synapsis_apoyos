#!/bin/bash
# Script para iniciar Synapsis Apoyos en producción

set -e

# Variables de configuración
APP_DIR="/path/to/synapsis_apoyos"
VENV_DIR="$APP_DIR/venv"
USER="www-data"
GROUP="www-data"
WORKERS=4
BIND="127.0.0.1:5000"

echo "🚀 Iniciando Synapsis Apoyos en modo producción..."

# Verificar que estamos en el directorio correcto
cd $APP_DIR

# Activar entorno virtual
source $VENV_DIR/bin/activate

# Verificar variables de entorno
if [ ! -f ".env.production" ]; then
    echo "❌ Error: Archivo .env.production no encontrado"
    exit 1
fi

# Cargar variables de entorno
export $(cat .env.production | grep -v '^#' | xargs)

# Verificar configuración de base de datos
echo "🔍 Verificando conexión a base de datos..."
python -c "
from app import create_app, db
app = create_app('production')
with app.app_context():
    try:
        db.engine.execute('SELECT 1')
        print('✅ Conexión a base de datos exitosa')
    except Exception as e:
        print(f'❌ Error de conexión a base de datos: {e}')
        exit(1)
"

# Crear directorios necesarios
mkdir -p logs
mkdir -p /var/log/synapsis_apoyos
mkdir -p /var/run/synapsis_apoyos

# Configurar permisos
chown -R $USER:$GROUP logs
chown -R $USER:$GROUP /var/log/synapsis_apoyos
chown -R $USER:$GROUP /var/run/synapsis_apoyos

# Iniciar con Gunicorn
echo "🔧 Iniciando servidor Gunicorn..."
exec gunicorn \
    --config gunicorn.conf.py \
    --bind $BIND \
    --workers $WORKERS \
    --user $USER \
    --group $GROUP \
    --access-logfile /var/log/synapsis_apoyos/gunicorn_access.log \
    --error-logfile /var/log/synapsis_apoyos/gunicorn_error.log \
    --log-level info \
    --preload \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --timeout 30 \
    --keep-alive 2 \
    --worker-class gevent \
    --worker-connections 1000 \
    wsgi:app