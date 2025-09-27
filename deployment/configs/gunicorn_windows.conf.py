"""
Configuración de Gunicorn para Synapsis Apoyos - Windows
"""

import multiprocessing
import os

# Configuración del servidor
bind = "127.0.0.1:5000"
backlog = 2048

# Workers (ajustado para Windows)
workers = min(multiprocessing.cpu_count() * 2 + 1, 8)  # Máximo 8 workers
worker_class = "sync"  # sync es más estable en Windows que gevent
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
daemon = False  # No daemon en Windows

# Configuración de memoria
max_requests_jitter = 100

# Hooks para logging
def on_starting(server):
    server.log.info("Iniciando Synapsis Apoyos en modo producción")

def on_reload(server):
    server.log.info("Recargando configuración")

def worker_int(worker):
    worker.log.info("Worker interrumpido")

def pre_fork(server, worker):
    server.log.info(f"Worker {worker.pid} iniciando")

def post_fork(server, worker):
    server.log.info(f"Worker {worker.pid} iniciado")

def worker_abort(worker):
    worker.log.info(f"Worker {worker.pid} abortado")
