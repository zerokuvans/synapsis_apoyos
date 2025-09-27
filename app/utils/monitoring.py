"""
Sistema de monitoreo y métricas para Synapsis Apoyos
Incluye logging avanzado, métricas de rendimiento y alertas
"""

import os
import time
import psutil
import logging
from datetime import datetime, timedelta
from functools import wraps
from flask import request, g, current_app
from sqlalchemy import text
import json

# Configuración de logging estructurado
class StructuredLogger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        
    def log_event(self, level, event_type, message, **kwargs):
        """Log estructurado con metadatos"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'message': message,
            'request_id': getattr(g, 'request_id', None),
            'user_id': getattr(g, 'user_id', None),
            'ip_address': request.remote_addr if request else None,
            'user_agent': request.headers.get('User-Agent') if request else None,
            **kwargs
        }
        
        if level == 'info':
            self.logger.info(json.dumps(log_data))
        elif level == 'warning':
            self.logger.warning(json.dumps(log_data))
        elif level == 'error':
            self.logger.error(json.dumps(log_data))
        elif level == 'critical':
            self.logger.critical(json.dumps(log_data))

# Logger global
app_logger = StructuredLogger('synapsis_apoyos')

class PerformanceMonitor:
    """Monitor de rendimiento de la aplicación"""
    
    def __init__(self):
        self.metrics = {
            'requests_total': 0,
            'requests_by_endpoint': {},
            'response_times': [],
            'errors_total': 0,
            'active_users': set(),
            'database_queries': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
    def record_request(self, endpoint, response_time, status_code, user_id=None):
        """Registrar métricas de request"""
        self.metrics['requests_total'] += 1
        
        if endpoint not in self.metrics['requests_by_endpoint']:
            self.metrics['requests_by_endpoint'][endpoint] = {
                'count': 0,
                'total_time': 0,
                'errors': 0
            }
        
        self.metrics['requests_by_endpoint'][endpoint]['count'] += 1
        self.metrics['requests_by_endpoint'][endpoint]['total_time'] += response_time
        
        if status_code >= 400:
            self.metrics['errors_total'] += 1
            self.metrics['requests_by_endpoint'][endpoint]['errors'] += 1
        
        self.metrics['response_times'].append(response_time)
        
        # Mantener solo las últimas 1000 mediciones
        if len(self.metrics['response_times']) > 1000:
            self.metrics['response_times'] = self.metrics['response_times'][-1000:]
        
        if user_id:
            self.metrics['active_users'].add(user_id)
    
    def get_system_metrics(self):
        """Obtener métricas del sistema"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0],
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_app_metrics(self):
        """Obtener métricas de la aplicación"""
        avg_response_time = (
            sum(self.metrics['response_times']) / len(self.metrics['response_times'])
            if self.metrics['response_times'] else 0
        )
        
        return {
            'requests_total': self.metrics['requests_total'],
            'errors_total': self.metrics['errors_total'],
            'error_rate': (
                self.metrics['errors_total'] / self.metrics['requests_total']
                if self.metrics['requests_total'] > 0 else 0
            ),
            'avg_response_time': avg_response_time,
            'active_users_count': len(self.metrics['active_users']),
            'database_queries': self.metrics['database_queries'],
            'cache_hit_rate': (
                self.metrics['cache_hits'] / (self.metrics['cache_hits'] + self.metrics['cache_misses'])
                if (self.metrics['cache_hits'] + self.metrics['cache_misses']) > 0 else 0
            ),
            'endpoints': self.metrics['requests_by_endpoint'],
            'timestamp': datetime.utcnow().isoformat()
        }

# Monitor global
performance_monitor = PerformanceMonitor()

def monitor_performance(f):
    """Decorator para monitorear rendimiento de funciones"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = f(*args, **kwargs)
            execution_time = time.time() - start_time
            
            app_logger.log_event(
                'info',
                'function_execution',
                f'Function {f.__name__} executed successfully',
                function_name=f.__name__,
                execution_time=execution_time,
                args_count=len(args),
                kwargs_count=len(kwargs)
            )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            app_logger.log_event(
                'error',
                'function_error',
                f'Function {f.__name__} failed',
                function_name=f.__name__,
                execution_time=execution_time,
                error_type=type(e).__name__,
                error_message=str(e)
            )
            
            raise
    
    return decorated_function

def monitor_database_query(f):
    """Decorator para monitorear queries de base de datos"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        performance_monitor.metrics['database_queries'] += 1
        
        try:
            result = f(*args, **kwargs)
            execution_time = time.time() - start_time
            
            if execution_time > 1.0:  # Query lenta (>1 segundo)
                app_logger.log_event(
                    'warning',
                    'slow_query',
                    f'Slow database query detected',
                    function_name=f.__name__,
                    execution_time=execution_time
                )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            app_logger.log_event(
                'error',
                'database_error',
                f'Database query failed',
                function_name=f.__name__,
                execution_time=execution_time,
                error_type=type(e).__name__,
                error_message=str(e)
            )
            
            raise
    
    return decorated_function

class HealthChecker:
    """Verificador de salud de la aplicación"""
    
    def __init__(self, app=None, db=None):
        self.app = app
        self.db = db
        
    def check_database(self):
        """Verificar conexión a base de datos"""
        try:
            if self.db:
                self.db.engine.execute(text('SELECT 1'))
                return {'status': 'healthy', 'message': 'Database connection OK'}
            else:
                return {'status': 'unknown', 'message': 'Database not configured'}
        except Exception as e:
            return {'status': 'unhealthy', 'message': f'Database error: {str(e)}'}
    
    def check_disk_space(self):
        """Verificar espacio en disco"""
        try:
            disk_usage = psutil.disk_usage('/')
            free_percent = (disk_usage.free / disk_usage.total) * 100
            
            if free_percent < 10:
                return {'status': 'critical', 'message': f'Low disk space: {free_percent:.1f}% free'}
            elif free_percent < 20:
                return {'status': 'warning', 'message': f'Disk space low: {free_percent:.1f}% free'}
            else:
                return {'status': 'healthy', 'message': f'Disk space OK: {free_percent:.1f}% free'}
        except Exception as e:
            return {'status': 'unknown', 'message': f'Disk check error: {str(e)}'}
    
    def check_memory(self):
        """Verificar uso de memoria"""
        try:
            memory = psutil.virtual_memory()
            
            if memory.percent > 90:
                return {'status': 'critical', 'message': f'High memory usage: {memory.percent:.1f}%'}
            elif memory.percent > 80:
                return {'status': 'warning', 'message': f'Memory usage high: {memory.percent:.1f}%'}
            else:
                return {'status': 'healthy', 'message': f'Memory usage OK: {memory.percent:.1f}%'}
        except Exception as e:
            return {'status': 'unknown', 'message': f'Memory check error: {str(e)}'}
    
    def get_health_status(self):
        """Obtener estado general de salud"""
        checks = {
            'database': self.check_database(),
            'disk_space': self.check_disk_space(),
            'memory': self.check_memory(),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Determinar estado general
        statuses = [check['status'] for check in checks.values() if isinstance(check, dict)]
        
        if 'critical' in statuses:
            overall_status = 'critical'
        elif 'unhealthy' in statuses:
            overall_status = 'unhealthy'
        elif 'warning' in statuses:
            overall_status = 'warning'
        else:
            overall_status = 'healthy'
        
        return {
            'overall_status': overall_status,
            'checks': checks
        }

def setup_monitoring_middleware(app, db=None):
    """Configurar middleware de monitoreo"""
    health_checker = HealthChecker(app, db)
    
    @app.before_request
    def before_request():
        g.start_time = time.time()
        g.request_id = f"{int(time.time())}-{os.urandom(4).hex()}"
        
        # Log de request entrante
        app_logger.log_event(
            'info',
            'request_start',
            f'{request.method} {request.path}',
            method=request.method,
            path=request.path,
            query_string=request.query_string.decode(),
            content_length=request.content_length
        )
    
    @app.after_request
    def after_request(response):
        if hasattr(g, 'start_time'):
            response_time = time.time() - g.start_time
            
            # Registrar métricas
            performance_monitor.record_request(
                request.endpoint,
                response_time,
                response.status_code,
                getattr(g, 'user_id', None)
            )
            
            # Log de response
            app_logger.log_event(
                'info',
                'request_complete',
                f'{request.method} {request.path} - {response.status_code}',
                method=request.method,
                path=request.path,
                status_code=response.status_code,
                response_time=response_time,
                content_length=response.content_length
            )
        
        return response
    
    # Endpoint de métricas
    @app.route('/health')
    def health_check():
        return health_checker.get_health_status()
    
    @app.route('/metrics')
    def metrics():
        return {
            'system': performance_monitor.get_system_metrics(),
            'application': performance_monitor.get_app_metrics()
        }
    
    return health_checker

class AlertManager:
    """Gestor de alertas"""
    
    def __init__(self):
        self.alert_thresholds = {
            'error_rate': 0.05,  # 5%
            'response_time': 2.0,  # 2 segundos
            'memory_usage': 85,    # 85%
            'disk_usage': 90,      # 90%
            'cpu_usage': 90        # 90%
        }
        
    def check_alerts(self, metrics):
        """Verificar si se deben enviar alertas"""
        alerts = []
        
        # Verificar tasa de errores
        if metrics['application']['error_rate'] > self.alert_thresholds['error_rate']:
            alerts.append({
                'type': 'error_rate',
                'severity': 'warning',
                'message': f"High error rate: {metrics['application']['error_rate']:.2%}",
                'value': metrics['application']['error_rate']
            })
        
        # Verificar tiempo de respuesta
        if metrics['application']['avg_response_time'] > self.alert_thresholds['response_time']:
            alerts.append({
                'type': 'response_time',
                'severity': 'warning',
                'message': f"High response time: {metrics['application']['avg_response_time']:.2f}s",
                'value': metrics['application']['avg_response_time']
            })
        
        # Verificar uso de memoria
        if metrics['system']['memory_percent'] > self.alert_thresholds['memory_usage']:
            alerts.append({
                'type': 'memory_usage',
                'severity': 'critical' if metrics['system']['memory_percent'] > 95 else 'warning',
                'message': f"High memory usage: {metrics['system']['memory_percent']:.1f}%",
                'value': metrics['system']['memory_percent']
            })
        
        return alerts
    
    def send_alert(self, alert):
        """Enviar alerta (implementar según necesidades)"""
        app_logger.log_event(
            'critical' if alert['severity'] == 'critical' else 'warning',
            'alert',
            alert['message'],
            alert_type=alert['type'],
            severity=alert['severity'],
            value=alert['value']
        )

# Instancia global del gestor de alertas
alert_manager = AlertManager()