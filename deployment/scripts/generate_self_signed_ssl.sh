#!/bin/bash
# Script para generar certificados SSL auto-firmados para desarrollo/testing

set -e

# Variables de configuración
DOMAIN="localhost"
COUNTRY="CO"
STATE="Bogota"
CITY="Bogota"
ORGANIZATION="Synapsis Apoyos"
UNIT="IT Department"
EMAIL="admin@synapsis-apoyos.local"
DAYS=365

# Directorio para certificados
SSL_DIR="ssl"
mkdir -p $SSL_DIR

echo "🔒 Generando certificados SSL auto-firmados para desarrollo..."

# Generar clave privada
echo "🔑 Generando clave privada..."
openssl genrsa -out $SSL_DIR/private.key 2048

# Generar solicitud de certificado
echo "📝 Generando solicitud de certificado..."
openssl req -new -key $SSL_DIR/private.key -out $SSL_DIR/certificate.csr -subj "/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORGANIZATION/OU=$UNIT/CN=$DOMAIN/emailAddress=$EMAIL"

# Crear archivo de configuración para extensiones
cat > $SSL_DIR/cert.conf << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = $COUNTRY
ST = $STATE
L = $CITY
O = $ORGANIZATION
OU = $UNIT
CN = $DOMAIN
emailAddress = $EMAIL

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
DNS.2 = 127.0.0.1
DNS.3 = synapsis-apoyos.local
DNS.4 = www.synapsis-apoyos.local
IP.1 = 127.0.0.1
IP.2 = ::1
EOF

# Generar certificado auto-firmado
echo "📜 Generando certificado auto-firmado..."
openssl x509 -req -in $SSL_DIR/certificate.csr -signkey $SSL_DIR/private.key -out $SSL_DIR/certificate.crt -days $DAYS -extensions v3_req -extfile $SSL_DIR/cert.conf

# Generar certificado en formato PEM
echo "📋 Generando certificado en formato PEM..."
cat $SSL_DIR/certificate.crt > $SSL_DIR/fullchain.pem

# Configurar permisos
chmod 600 $SSL_DIR/private.key
chmod 644 $SSL_DIR/certificate.crt
chmod 644 $SSL_DIR/fullchain.pem

# Limpiar archivos temporales
rm $SSL_DIR/certificate.csr
rm $SSL_DIR/cert.conf

echo "✅ Certificados SSL generados exitosamente!"
echo ""
echo "📁 Archivos generados en el directorio '$SSL_DIR':"
echo "   - private.key: Clave privada"
echo "   - certificate.crt: Certificado público"
echo "   - fullchain.pem: Certificado completo"
echo ""
echo "⚙️ Para usar con Nginx, actualiza la configuración:"
echo "   ssl_certificate $PWD/$SSL_DIR/certificate.crt;"
echo "   ssl_certificate_key $PWD/$SSL_DIR/private.key;"
echo ""
echo "⚙️ Para usar con Gunicorn:"
echo "   gunicorn --certfile=$PWD/$SSL_DIR/certificate.crt --keyfile=$PWD/$SSL_DIR/private.key ..."
echo ""
echo "⚠️  IMPORTANTE: Estos son certificados auto-firmados para desarrollo."
echo "   Los navegadores mostrarán una advertencia de seguridad."
echo "   Para producción, usa certificados de una CA confiable como Let's Encrypt."