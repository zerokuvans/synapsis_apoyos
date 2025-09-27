"""
Configuración de Gunicorn para Synapsis Apoyos
Optimizada para producción
"""

import multiprocessing
import os

# Configuración del servidor
bind = "127.0.0.1:5000"
backlog = 2048

# Workers
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gevent"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100

# Timeouts
timeout = 30
keepalive = 2
graceful_timeout = 30

# Logging
accesslog = "logs/gunicorn_access.log"
errorlog = "logs/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "synapsis_apoyos"

# Server mechanics
preload_app = True
daemon = False
pidfile = "/var/run/synapsis_apoyos/gunicorn.pid"
user = None  # Se configurará en el script de inicio
group = None  # Se configurará en el script de inicio
tmp_upload_dir = None

# SSL (si se configura)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# Configuración de memoria
max_requests_jitter = 100
preload_app = True

# Hooks
def on_starting(server):
    """Llamado justo antes de que el master process sea inicializado."""
    server.log.info("Iniciando Synapsis Apoyos...")

def on_reload(server):
    """Llamado para recargar la configuración."""
    server.log.info("Recargando configuración...")

def when_ready(server):
    """Llamado justo después de que el servidor esté listo."""
    server.log.info("Servidor listo para recibir conexiones")

def worker_int(worker):
    """Llamado cuando un worker recibe la señal SIGINT o SIGQUIT."""
    worker.log.info("Worker recibió señal de interrupción")

def pre_fork(server, worker):
    """Llamado justo antes de hacer fork del worker."""
    server.log.info(f"Worker {worker.pid} está siendo creado")

def post_fork(server, worker):
    """Llamado justo después de hacer fork del worker."""
    server.log.info(f"Worker {worker.pid} creado exitosamente")

def post_worker_init(worker):
    """Llamado justo después de que un worker haya inicializado la aplicación."""
    worker.log.info(f"Worker {worker.pid} inicializado")

def worker_abort(worker):
    """Llamado cuando un worker recibe la señal SIGABRT."""
    worker.log.info(f"Worker {worker.pid} abortado")

def pre_exec(server):
    """Llamado justo antes de hacer exec del nuevo master process."""
    server.log.info("Ejecutando nuevo master process")

def pre_request(worker, req):
    """Llamado justo antes de que un worker procese la request."""
    worker.log.debug(f"{req.method} {req.path}")

def post_request(worker, req, environ, resp):
    """Llamado después de que un worker procese la request."""
    pass

def child_exit(server, worker):
    """Llamado cuando un worker sale."""
    server.log.info(f"Worker {worker.pid} salió")

def worker_exit(server, worker):
    """Llamado cuando un worker sale."""
    server.log.info(f"Worker {worker.pid} terminado")

def nworkers_changed(server, new_value, old_value):
    """Llamado cuando el número de workers cambia."""
    server.log.info(f"Número de workers cambió de {old_value} a {new_value}")

def on_exit(server):
    """Llamado justo antes de salir."""
    server.log.info("Cerrando Synapsis Apoyos...")

# Variables de entorno específicas
raw_env = [
    'FLASK_ENV=production',
]