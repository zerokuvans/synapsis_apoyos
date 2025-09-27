#!/bin/bash
# Script para configurar SSL/HTTPS con Let's Encrypt para Synapsis Apoyos

set -e

# Variables de configuración
DOMAIN="tu-dominio.com"
EMAIL="admin@tu-dominio.com"
WEBROOT="/var/www/html"
NGINX_CONF="/etc/nginx/sites-available/synapsis_apoyos"

echo "🔒 Configurando SSL/HTTPS para Synapsis Apoyos..."

# Verificar que estamos ejecutando como root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Este script debe ejecutarse como root"
    exit 1
fi

# Actualizar sistema
echo "📦 Actualizando sistema..."
apt update && apt upgrade -y

# Instalar Certbot
echo "🔧 Instalando Certbot..."
apt install -y certbot python3-certbot-nginx

# Verificar configuración de Nginx
echo "🔍 Verificando configuración de Nginx..."
nginx -t
if [ $? -ne 0 ]; then
    echo "❌ Error en la configuración de Nginx"
    exit 1
fi

# Crear directorio webroot si no existe
mkdir -p $WEBROOT

# Configuración temporal de Nginx para validación
echo "⚙️ Configurando Nginx temporal para validación..."
cat > /etc/nginx/sites-available/temp_ssl << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    location /.well-known/acme-challenge/ {
        root $WEBROOT;
    }
    
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}
EOF

# Habilitar configuración temporal
ln -sf /etc/nginx/sites-available/temp_ssl /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
systemctl reload nginx

# Obtener certificado SSL
echo "🔐 Obteniendo certificado SSL de Let's Encrypt..."
certbot certonly \
    --webroot \
    --webroot-path=$WEBROOT \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    --domains $DOMAIN,www.$DOMAIN

if [ $? -eq 0 ]; then
    echo "✅ Certificado SSL obtenido exitosamente"
else
    echo "❌ Error al obtener certificado SSL"
    exit 1
fi

# Configurar renovación automática
echo "🔄 Configurando renovación automática..."
cat > /etc/cron.d/certbot << EOF
# Renovar certificados SSL automáticamente
0 12 * * * root test -x /usr/bin/certbot -a \! -d /run/systemd/system && perl -e 'sleep int(rand(43200))' && certbot -q renew --nginx
EOF

# Generar parámetros DH fuertes
echo "🔐 Generando parámetros Diffie-Hellman..."
if [ ! -f /etc/ssl/certs/dhparam.pem ]; then
    openssl dhparam -out /etc/ssl/certs/dhparam.pem 2048
fi

# Actualizar configuración de Nginx con SSL
echo "⚙️ Actualizando configuración de Nginx con SSL..."
sed -i "s|/path/to/ssl/certificate.crt|/etc/letsencrypt/live/$DOMAIN/fullchain.pem|g" $NGINX_CONF
sed -i "s|/path/to/ssl/private.key|/etc/letsencrypt/live/$DOMAIN/privkey.pem|g" $NGINX_CONF

# Agregar configuración DH
sed -i "/ssl_session_timeout/a\\    ssl_dhparam /etc/ssl/certs/dhparam.pem;" $NGINX_CONF

# Habilitar configuración final
rm -f /etc/nginx/sites-enabled/temp_ssl
ln -sf $NGINX_CONF /etc/nginx/sites-enabled/

# Verificar configuración final
echo "🔍 Verificando configuración final de Nginx..."
nginx -t
if [ $? -eq 0 ]; then
    systemctl reload nginx
    echo "✅ Nginx recargado exitosamente"
else
    echo "❌ Error en la configuración final de Nginx"
    exit 1
fi

# Verificar SSL
echo "🔍 Verificando configuración SSL..."
sleep 5
curl -I https://$DOMAIN/ | head -1

# Configurar firewall
echo "🔥 Configurando firewall..."
ufw allow 'Nginx Full'
ufw delete allow 'Nginx HTTP'

echo "🎉 SSL/HTTPS configurado exitosamente!"
echo "📋 Resumen:"
echo "   - Dominio: $DOMAIN"
echo "   - Certificado: /etc/letsencrypt/live/$DOMAIN/"
echo "   - Renovación automática: Configurada"
echo "   - Firewall: Actualizado"
echo ""
echo "🔗 Puedes acceder a tu aplicación en: https://$DOMAIN"
echo ""
echo "📝 Notas importantes:"
echo "   - Los certificados se renovarán automáticamente"
echo "   - Verifica que tu DNS apunte correctamente al servidor"
echo "   - Considera configurar HSTS en tu aplicación"