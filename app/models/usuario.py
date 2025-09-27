from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from app import db
from app.utils.timezone_utils import get_bogota_timestamp

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20))
    rol = db.Column(db.Enum('tecnico', 'movil', 'lider', name='rol_enum'), nullable=False, index=True)
    activo = db.Column(db.Boolean, default=True, index=True)
    last_activity = db.Column(db.DateTime, nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=get_bogota_timestamp)
    updated_at = db.Column(db.DateTime, default=get_bogota_timestamp, onupdate=get_bogota_timestamp)
    
    # Relaciones
    solicitudes = db.relationship('Solicitud', backref='tecnico', lazy=True, cascade='all, delete-orphan')
    servicios = db.relationship('Servicio', backref='movil', lazy=True, cascade='all, delete-orphan')
    ubicaciones = db.relationship('Ubicacion', backref='usuario', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, email, password, nombre, apellido, rol, telefono=None):
        self.email = email
        self.set_password(password)
        self.nombre = nombre
        self.apellido = apellido
        self.rol = rol
        self.telefono = telefono
        self.activo = True  # Establecer valor por defecto explícitamente
    
    def set_password(self, password):
        """Establece la contraseña hasheada"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verifica la contraseña"""
        return check_password_hash(self.password_hash, password)
    
    def get_nombre_completo(self):
        """Retorna el nombre completo del usuario"""
        return f"{self.nombre} {self.apellido}"
    
    def is_tecnico(self):
        """Verifica si el usuario es técnico"""
        return self.rol == 'tecnico'
    
    def is_movil(self):
        """Verifica si el usuario es móvil de apoyo"""
        return self.rol == 'movil'
    
    def is_lider(self):
        """Verifica si el usuario es líder"""
        return self.rol == 'lider'
    
    def get_ubicacion_actual(self):
        """Obtiene la ubicación más reciente del usuario"""
        from app.models.ubicacion import Ubicacion
        return Ubicacion.query.filter_by(
            usuario_id=self.id,
            activa=True
        ).order_by(Ubicacion.timestamp.desc()).first()
    
    def to_dict(self):
        """Convierte el objeto a diccionario para JSON"""
        return {
            'id': self.id,
            'email': self.email,
            'nombre': self.nombre,
            'apellido': self.apellido,
            'nombre_completo': self.get_nombre_completo(),
            'telefono': self.telefono,
            'rol': self.rol,
            'activo': self.activo,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Usuario {self.email} - {self.rol}>'

# Importar otros modelos para evitar problemas de importación circular
from app.models.solicitud import Solicitud
from app.models.ubicacion import Ubicacion
from app.models.servicio import Servicio