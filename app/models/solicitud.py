from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from app import db
from app.utils.timezone_utils import get_bogota_timestamp

class Solicitud(db.Model):
    __tablename__ = 'solicitudes'
    
    id = db.Column(db.Integer, primary_key=True)
    tecnico_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False, index=True)
    localidad_id = db.Column(db.Integer, db.ForeignKey('localidades.id'), nullable=True, index=True)
    tipo_apoyo = db.Column(db.Enum('escalera', 'equipos', name='tipo_apoyo_enum'), nullable=False)
    latitud = db.Column(db.Numeric(10, 8), nullable=False)
    longitud = db.Column(db.Numeric(11, 8), nullable=False)
    direccion = db.Column(db.String(500))
    observaciones = db.Column(db.Text)
    estado = db.Column(
        db.Enum('pendiente', 'aceptada', 'rechazada', 'completada', 'cancelada', 'expirada', name='estado_solicitud_enum'),
        default='pendiente',
        index=True
    )
    created_at = db.Column(db.DateTime, default=get_bogota_timestamp, index=True)
    limite_tiempo = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, default=get_bogota_timestamp, onupdate=get_bogota_timestamp)
    
    # Relaciones
    servicio = db.relationship('Servicio', backref='solicitud', uselist=False, cascade='all, delete-orphan')
    localidad = db.relationship('Localidad', backref='solicitudes')
    
    def __init__(self, tecnico_id, tipo_apoyo, latitud, longitud, observaciones=None, direccion=None):
        self.tecnico_id = tecnico_id
        self.tipo_apoyo = tipo_apoyo
        self.latitud = latitud
        self.longitud = longitud
        self.observaciones = observaciones
        self.direccion = direccion
        # Establecer límite de tiempo a 2 horas desde la creación
        self.limite_tiempo = get_bogota_timestamp() + timedelta(hours=2)
    
    def is_pendiente(self):
        """Verifica si la solicitud está pendiente"""
        return self.estado == 'pendiente'
    
    def is_aceptada(self):
        """Verifica si la solicitud fue aceptada"""
        return self.estado == 'aceptada'
    
    def is_completada(self):
        """Verifica si la solicitud fue completada"""
        return self.estado == 'completada'
    
    def is_expirada(self):
        """Verifica si la solicitud ha expirado"""
        return get_bogota_timestamp() > self.limite_tiempo and self.estado == 'pendiente'
    
    def tiempo_restante(self):
        """Calcula el tiempo restante antes de que expire"""
        if self.estado != 'pendiente':
            return None
        
        tiempo_restante = self.limite_tiempo - get_bogota_timestamp()
        if tiempo_restante.total_seconds() <= 0:
            return timedelta(0)
        return tiempo_restante
    
    def tiempo_transcurrido(self):
        """Calcula el tiempo transcurrido desde la creación"""
        return get_bogota_timestamp() - self.created_at
    
    def marcar_como_expirada(self):
        """Marca la solicitud como expirada"""
        if self.is_pendiente() and self.is_expirada():
            self.estado = 'expirada'
            self.updated_at = get_bogota_timestamp()
            return True
        return False
    
    def aceptar(self, movil_id):
        """Acepta la solicitud y crea el servicio asociado"""
        if not self.is_pendiente():
            return False, "La solicitud no está pendiente"
        
        if self.is_expirada():
            self.marcar_como_expirada()
            return False, "La solicitud ha expirado"
        
        self.estado = 'aceptada'
        self.updated_at = get_bogota_timestamp()
        
        # Crear servicio asociado
        from app.models.servicio import Servicio
        servicio = Servicio(
            solicitud_id=self.id,
            movil_id=movil_id
        )
        db.session.add(servicio)
        
        return True, "Solicitud aceptada exitosamente"
    
    def rechazar(self, observaciones):
        """Rechaza la solicitud con observaciones"""
        if not self.is_pendiente():
            return False, "La solicitud no está pendiente"
        
        self.estado = 'rechazada'
        self.observaciones = observaciones
        self.updated_at = get_bogota_timestamp()
        
        return True, "Solicitud rechazada"
    
    def cancelar(self, observaciones):
        """Cancela la solicitud"""
        if self.estado in ['completada', 'cancelada', 'expirada']:
            return False, "No se puede cancelar la solicitud en su estado actual"
        
        self.estado = 'cancelada'
        self.observaciones = observaciones
        self.updated_at = get_bogota_timestamp()
        
        return True, "Solicitud cancelada"
    
    def completar(self):
        """Marca la solicitud como completada"""
        if not self.is_aceptada():
            return False, "La solicitud debe estar aceptada para completarse"
        
        self.estado = 'completada'
        self.updated_at = get_bogota_timestamp()
        
        return True, "Solicitud completada"
    
    def get_coordenadas(self):
        """Retorna las coordenadas como tupla"""
        return (float(self.latitud), float(self.longitud))
    
    def to_dict(self):
        """Convierte el objeto a diccionario para JSON"""
        return {
            'id': self.id,
            'tecnico_id': self.tecnico_id,
            'tecnico_nombre': self.tecnico.get_nombre_completo() if self.tecnico else None,
            'localidad_id': self.localidad_id,
            'localidad_nombre': self.localidad.nombre if self.localidad else None,
            'localidad_codigo': self.localidad.codigo if self.localidad else None,
            'tipo_apoyo': self.tipo_apoyo,
            'latitud': float(self.latitud),
            'longitud': float(self.longitud),
            'direccion': self.direccion,
            'observaciones': self.observaciones,
            'estado': self.estado,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'limite_tiempo': self.limite_tiempo.isoformat() if self.limite_tiempo else None,
            'tiempo_restante_segundos': self.tiempo_restante().total_seconds() if self.tiempo_restante() else None,
            'tiempo_transcurrido_segundos': self.tiempo_transcurrido().total_seconds(),
            'servicio': self.servicio.to_dict() if self.servicio else None
        }
    
    def __repr__(self):
        return f'<Solicitud {self.id} - {self.tipo_apoyo} - {self.estado}>'

# Importar otros modelos para evitar problemas de importación circular
from app.models.servicio import Servicio