"""
Utilidades de seguridad para Synapsis Apoyos
"""

from flask import request, abort, current_app
from functools import wraps
import re
import ipaddress
from datetime import datetime, timedelta

# Lista de IPs bloqueadas (se puede mover a base de datos en el futuro)
BLOCKED_IPS = set()

# Patrones de ataques comunes
ATTACK_PATTERNS = [
    r'<script[^>]*>.*?</script>',  # XSS básico
    r'javascript:',  # JavaScript en URLs
    r'on\w+\s*=',  # Event handlers
    r'union\s+select',  # SQL injection
    r'drop\s+table',  # SQL injection
    r'insert\s+into',  # SQL injection
    r'delete\s+from',  # SQL injection
    r'\.\./',  # Path traversal
    r'etc/passwd',  # File inclusion
    r'cmd\.exe',  # Command injection
    r'powershell',  # Command injection
]

def is_safe_input(input_string):
    """
    Verifica si una entrada es segura
    """
    if not input_string:
        return True
    
    input_lower = input_string.lower()
    
    for pattern in ATTACK_PATTERNS:
        if re.search(pattern, input_lower, re.IGNORECASE):
            return False
    
    return True

def validate_ip_address(ip_str):
    """
    Valida si una dirección IP es válida
    """
    try:
        ipaddress.ip_address(ip_str)
        return True
    except ValueError:
        return False

def is_ip_blocked(ip):
    """
    Verifica si una IP está bloqueada
    """
    return ip in BLOCKED_IPS

def block_ip(ip, reason="Security violation"):
    """
    Bloquea una dirección IP
    """
    BLOCKED_IPS.add(ip)
    current_app.logger.warning(f"IP {ip} bloqueada: {reason}")

def security_headers(response):
    """
    Agrega headers de seguridad a las respuestas
    """
    # Prevenir clickjacking
    response.headers['X-Frame-Options'] = 'DENY'
    
    # Prevenir MIME type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    # XSS Protection
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Referrer Policy
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Content Security Policy (básico)
    if current_app.config.get('ENV') == 'production':
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' "
            "https://maps.googleapis.com https://maps.gstatic.com; "
            "style-src 'self' 'unsafe-inline' "
            "https://fonts.googleapis.com https://cdn.jsdelivr.net; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https:; "
            "frame-src 'none';"
        )
        response.headers['Content-Security-Policy'] = csp
    
    # HSTS (solo en HTTPS)
    if request.is_secure:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    return response

def validate_request_data():
    """
    Middleware para validar datos de entrada
    """
    # Verificar IP bloqueada
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    if client_ip and is_ip_blocked(client_ip):
        current_app.logger.warning(f"Acceso bloqueado desde IP: {client_ip}")
        abort(403)
    
    # Validar datos de formulario
    if request.form:
        for key, value in request.form.items():
            if not is_safe_input(value):
                current_app.logger.warning(f"Entrada insegura detectada: {key}={value[:100]}")
                abort(400)
    
    # Validar JSON
    if request.is_json:
        try:
            data = request.get_json()
            if data:
                for key, value in data.items():
                    if isinstance(value, str) and not is_safe_input(value):
                        current_app.logger.warning(f"JSON inseguro detectado: {key}={str(value)[:100]}")
                        abort(400)
        except Exception:
            pass

def require_https(f):
    """
    Decorator que requiere HTTPS en producción
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_app.config.get('ENV') == 'production' and not request.is_secure:
            return redirect(request.url.replace('http://', 'https://'))
        return f(*args, **kwargs)
    return decorated_function

def log_security_event(event_type, details, ip=None):
    """
    Registra eventos de seguridad
    """
    if not ip:
        ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    
    current_app.logger.warning(
        f"SECURITY EVENT: {event_type} | IP: {ip} | Details: {details} | "
        f"User-Agent: {request.headers.get('User-Agent', 'Unknown')}"
    )

def setup_security_middleware(app):
    """
    Configura middleware de seguridad
    """
    @app.before_request
    def before_request():
        validate_request_data()
    
    @app.after_request
    def after_request(response):
        return security_headers(response)
    
    # Rate limiting personalizado para rutas específicas
    @app.errorhandler(429)
    def ratelimit_handler(e):
        log_security_event("RATE_LIMIT_EXCEEDED", str(e))
        return jsonify({
            'error': 'Demasiadas solicitudes. Intenta de nuevo más tarde.',
            'retry_after': getattr(e, 'retry_after', 60)
        }), 429
    
    # Handler para errores de seguridad
    @app.errorhandler(403)
    def forbidden_handler(e):
        log_security_event("FORBIDDEN_ACCESS", str(e))
        return jsonify({
            'error': 'Acceso denegado'
        }), 403
    
    @app.errorhandler(400)
    def bad_request_handler(e):
        log_security_event("BAD_REQUEST", str(e))
        return jsonify({
            'error': 'Solicitud inválida'
        }), 400