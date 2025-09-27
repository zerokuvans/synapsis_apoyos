#!/bin/bash
# Script para configurar herramientas de monitoreo para Synapsis Apoyos

set -e

echo "📊 Configurando herramientas de monitoreo para Synapsis Apoyos..."

# Variables de configuración
APP_DIR="/path/to/synapsis_apoyos"
MONITORING_DIR="/opt/monitoring"
GRAFANA_PORT=3000
PROMETHEUS_PORT=9090

# Verificar que estamos ejecutando como root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Este script debe ejecutarse como root"
    exit 1
fi

# Crear directorios
mkdir -p $MONITORING_DIR/{prometheus,grafana,alertmanager}
mkdir -p /var/log/monitoring

echo "🔧 Instalando Prometheus..."

# Descargar e instalar Prometheus
cd /tmp
wget https://github.com/prometheus/prometheus/releases/download/v2.40.0/prometheus-2.40.0.linux-amd64.tar.gz
tar xvf prometheus-2.40.0.linux-amd64.tar.gz
cp prometheus-2.40.0.linux-amd64/prometheus /usr/local/bin/
cp prometheus-2.40.0.linux-amd64/promtool /usr/local/bin/
cp -r prometheus-2.40.0.linux-amd64/consoles /etc/prometheus/
cp -r prometheus-2.40.0.linux-amd64/console_libraries /etc/prometheus/

# Crear usuario prometheus
useradd --no-create-home --shell /bin/false prometheus
chown prometheus:prometheus /usr/local/bin/prometheus
chown prometheus:prometheus /usr/local/bin/promtool
chown -R prometheus:prometheus /etc/prometheus/

# Configuración de Prometheus
cat > /etc/prometheus/prometheus.yml << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "synapsis_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - localhost:9093

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'synapsis-apoyos'
    static_configs:
      - targets: ['localhost:5000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['localhost:9100']

  - job_name: 'nginx'
    static_configs:
      - targets: ['localhost:9113']
EOF

# Reglas de alertas
cat > /etc/prometheus/synapsis_rules.yml << EOF
groups:
- name: synapsis_apoyos
  rules:
  - alert: HighErrorRate
    expr: rate(flask_http_request_exceptions_total[5m]) > 0.05
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High error rate detected"
      description: "Error rate is {{ \$value }} errors per second"

  - alert: HighResponseTime
    expr: flask_http_request_duration_seconds{quantile="0.95"} > 2
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High response time detected"
      description: "95th percentile response time is {{ \$value }} seconds"

  - alert: HighMemoryUsage
    expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes > 0.85
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High memory usage"
      description: "Memory usage is {{ \$value | humanizePercentage }}"

  - alert: HighDiskUsage
    expr: (node_filesystem_size_bytes - node_filesystem_free_bytes) / node_filesystem_size_bytes > 0.90
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High disk usage"
      description: "Disk usage is {{ \$value | humanizePercentage }}"
EOF

chown -R prometheus:prometheus /etc/prometheus/

# Servicio systemd para Prometheus
cat > /etc/systemd/system/prometheus.service << EOF
[Unit]
Description=Prometheus
Wants=network-online.target
After=network-online.target

[Service]
User=prometheus
Group=prometheus
Type=simple
ExecStart=/usr/local/bin/prometheus \\
    --config.file /etc/prometheus/prometheus.yml \\
    --storage.tsdb.path /var/lib/prometheus/ \\
    --web.console.templates=/etc/prometheus/consoles \\
    --web.console.libraries=/etc/prometheus/console_libraries \\
    --web.listen-address=0.0.0.0:9090 \\
    --web.enable-lifecycle

[Install]
WantedBy=multi-user.target
EOF

echo "📊 Instalando Grafana..."

# Instalar Grafana
wget -q -O - https://packages.grafana.com/gpg.key | apt-key add -
echo "deb https://packages.grafana.com/oss/deb stable main" | tee -a /etc/apt/sources.list.d/grafana.list
apt update
apt install -y grafana

# Configurar Grafana
cat > /etc/grafana/grafana.ini << EOF
[server]
http_port = $GRAFANA_PORT
domain = localhost

[security]
admin_user = admin
admin_password = synapsis_admin_2024

[database]
type = sqlite3
path = grafana.db

[session]
provider = file

[analytics]
reporting_enabled = false
check_for_updates = false

[log]
mode = file
level = info
EOF

echo "🔔 Instalando Node Exporter..."

# Descargar e instalar Node Exporter
cd /tmp
wget https://github.com/prometheus/node_exporter/releases/download/v1.5.0/node_exporter-1.5.0.linux-amd64.tar.gz
tar xvf node_exporter-1.5.0.linux-amd64.tar.gz
cp node_exporter-1.5.0.linux-amd64/node_exporter /usr/local/bin/

# Crear usuario node_exporter
useradd --no-create-home --shell /bin/false node_exporter
chown node_exporter:node_exporter /usr/local/bin/node_exporter

# Servicio systemd para Node Exporter
cat > /etc/systemd/system/node_exporter.service << EOF
[Unit]
Description=Node Exporter
Wants=network-online.target
After=network-online.target

[Service]
User=node_exporter
Group=node_exporter
Type=simple
ExecStart=/usr/local/bin/node_exporter

[Install]
WantedBy=multi-user.target
EOF

echo "🌐 Configurando Nginx Exporter..."

# Instalar Nginx Prometheus Exporter
cd /tmp
wget https://github.com/nginxinc/nginx-prometheus-exporter/releases/download/v0.10.0/nginx-prometheus-exporter_0.10.0_linux_amd64.tar.gz
tar xvf nginx-prometheus-exporter_0.10.0_linux_amd64.tar.gz
cp nginx-prometheus-exporter /usr/local/bin/

# Configurar stub_status en Nginx
cat >> /etc/nginx/sites-available/synapsis_apoyos << EOF

# Métricas para Prometheus
server {
    listen 127.0.0.1:8080;
    location /nginx_status {
        stub_status on;
        access_log off;
        allow 127.0.0.1;
        deny all;
    }
}
EOF

# Servicio systemd para Nginx Exporter
cat > /etc/systemd/system/nginx_exporter.service << EOF
[Unit]
Description=Nginx Prometheus Exporter
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
ExecStart=/usr/local/bin/nginx-prometheus-exporter -nginx.scrape-uri=http://127.0.0.1:8080/nginx_status
Restart=always

[Install]
WantedBy=multi-user.target
EOF

echo "🔄 Habilitando y iniciando servicios..."

# Recargar systemd y habilitar servicios
systemctl daemon-reload
systemctl enable prometheus
systemctl enable grafana-server
systemctl enable node_exporter
systemctl enable nginx_exporter

# Iniciar servicios
systemctl start prometheus
systemctl start grafana-server
systemctl start node_exporter
systemctl start nginx_exporter

# Recargar Nginx
nginx -t && systemctl reload nginx

echo "✅ Configuración de monitoreo completada!"
echo ""
echo "📋 Servicios configurados:"
echo "   - Prometheus: http://localhost:$PROMETHEUS_PORT"
echo "   - Grafana: http://localhost:$GRAFANA_PORT (admin/synapsis_admin_2024)"
echo "   - Node Exporter: http://localhost:9100/metrics"
echo "   - Nginx Exporter: http://localhost:9113/metrics"
echo ""
echo "📊 Dashboard de Grafana:"
echo "   1. Accede a Grafana en http://localhost:$GRAFANA_PORT"
echo "   2. Configura Prometheus como datasource: http://localhost:$PROMETHEUS_PORT"
echo "   3. Importa dashboards para Flask, Nginx y Node Exporter"
echo ""
echo "🔔 Configuración de alertas:"
echo "   - Las reglas están configuradas en /etc/prometheus/synapsis_rules.yml"
echo "   - Configura Alertmanager para notificaciones por email/Slack"