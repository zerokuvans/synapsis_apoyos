from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from app import db
from app.utils.timezone_utils import get_bogota_timestamp

class Observacion(db.Model):
    __tablename__ = 'observaciones'
    
    id = db.Column(db.Integer, primary_key=True)
    servicio_id = db.Column(db.Integer, db.ForeignKey('servicios.id'), nullable=False, index=True)
    contenido = db.Column(db.Text, nullable=False)
    tipo = db.Column(
        db.Enum('rechazo', 'progreso', 'finalizacion', name='tipo_observacion_enum'),
        nullable=False,
        index=True
    )
    created_at = db.Column(db.DateTime, default=get_bogota_timestamp)
    
    def __init__(self, servicio_id, contenido, tipo):
        self.servicio_id = servicio_id
        self.contenido = contenido
        self.tipo = tipo
        self.created_at = get_bogota_timestamp()
    
    def is_rechazo(self):
        """Verifica si es una observación de rechazo"""
        return self.tipo == 'rechazo'
    
    def is_progreso(self):
        """Verifica si es una observación de progreso"""
        return self.tipo == 'progreso'
    
    def is_finalizacion(self):
        """Verifica si es una observación de finalización"""
        return self.tipo == 'finalizacion'
    
    def tiempo_transcurrido(self):
        """Calcula el tiempo transcurrido desde la creación"""
        return get_bogota_timestamp() - self.created_at
    
    def to_dict(self):
        """Convierte el objeto a diccionario para JSON"""
        return {
            'id': self.id,
            'servicio_id': self.servicio_id,
            'contenido': self.contenido,
            'tipo': self.tipo,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'tiempo_transcurrido_segundos': self.tiempo_transcurrido().total_seconds()
        }
    
    def __repr__(self):
        return f'<Observacion {self.id} - Servicio {self.servicio_id} - {self.tipo}>'