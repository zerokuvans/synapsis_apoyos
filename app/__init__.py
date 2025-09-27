from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_cors import CORS
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from config import get_config
import os
import logging
from logging.handlers import RotatingFileHandler

# Inicializar extensiones
db = SQLAlchemy()
login_manager = LoginManager()
socketio = SocketIO()
mail = Mail()
limiter = Limiter(key_func=get_remote_address)
csrf = CSRFProtect()

def create_app(config_name=None):
    app = Flask(__name__)
    
    # Cargar configuración
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    config_class = get_config()
    app.config.from_object(config_class)
    
    # Configurar logging para producción
    if not app.debug and not app.testing:
        configure_logging(app)
    
    # Importar funciones de zona horaria
    from app.utils.timezone_utils import get_bogota_timestamp, format_bogota_time, utc_to_bogota
    
    # Hacer las funciones disponibles globalmente en templates
    app.jinja_env.globals['get_bogota_time'] = get_bogota_timestamp
    app.jinja_env.globals['format_bogota_time'] = format_bogota_time
    app.jinja_env.globals['utc_to_bogota'] = utc_to_bogota
    
    # Inicializar extensiones con la app
    db.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")
    mail.init_app(app)
    limiter.init_app(app)
    
    # Configurar CSRF y CORS según el entorno
    if app.config.get('WTF_CSRF_ENABLED', True):
        csrf.init_app(app)
    
    # CORS más restrictivo en producción
    if app.config.get('ENV') == 'production':
        CORS(app, origins=['https://tudominio.com'])
    else:
        CORS(app)
    
    # Configurar Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.usuario import Usuario
        return Usuario.query.get(int(user_id))
    
    # Registrar blueprints
    from app.blueprints.auth import auth_bp
    from app.blueprints.tecnico import tecnico_bp
    from app.blueprints.movil import movil_bp
    from app.blueprints.lider import lider_bp
    from app.blueprints.api import api_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(tecnico_bp, url_prefix='/tecnico')
    app.register_blueprint(movil_bp, url_prefix='/movil')
    app.register_blueprint(lider_bp, url_prefix='/lider')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Configurar middleware de actividad
    from app.utils.activity_tracker import track_activity_middleware
    track_activity_middleware(app)
    
    # Configurar middleware de seguridad
    from app.utils.security_utils import setup_security_middleware
    setup_security_middleware(app)
    
    # Configurar sistema de monitoreo
    from app.utils.monitoring import setup_monitoring_middleware
    setup_monitoring_middleware(app, db)
    
    # Ruta principal
    @app.route('/')
    def index():
        from flask import redirect, url_for
        from flask_login import current_user
        
        if current_user.is_authenticated:
            if current_user.rol == 'tecnico':
                return redirect(url_for('tecnico.dashboard'))
            elif current_user.rol == 'movil':
                return redirect(url_for('movil.dashboard'))
            elif current_user.rol == 'lider':
                return redirect(url_for('lider.dashboard'))
        
        return redirect(url_for('auth.login'))
    
    # Verificar conexión a base de datos
    with app.app_context():
        try:
            # Crear todas las tablas si no existen
            db.create_all()
        except Exception as e:
            if app.debug:
                raise e
            else:
                app.logger.error(f'Error al crear tablas de base de datos: {str(e)}')
    
    return app

def configure_logging(app):
    """Configurar logging para producción"""
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    # Configurar archivo de log con rotación
    file_handler = RotatingFileHandler(
        'logs/synapsis_apoyos.log', 
        maxBytes=10240000,  # 10MB
        backupCount=10
    )
    
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Synapsis Apoyos startup')