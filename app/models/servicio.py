from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from app import db
from app.utils.timezone_utils import get_bogota_timestamp

class Servicio(db.Model):
    __tablename__ = 'servicios'
    
    id = db.Column(db.Integer, primary_key=True)
    solicitud_id = db.Column(db.Integer, db.ForeignKey('solicitudes.id'), unique=True, nullable=False)
    movil_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False, index=True)
    aceptado_at = db.Column(db.DateTime, default=get_bogota_timestamp)
    iniciado_at = db.Column(db.DateTime)
    finalizado_at = db.Column(db.DateTime)
    observaciones_finales = db.Column(db.Text)
    estado_servicio = db.Column(
        db.Enum('aceptado', 'en_ruta', 'en_sitio', 'completado', 'cancelado', name='estado_servicio_enum'),
        default='aceptado',
        index=True
    )
    duracion_minutos = db.Column(db.Integer, default=0)
    
    # Relaciones
    observaciones = db.relationship('Observacion', backref='servicio', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, solicitud_id, movil_id):
        self.solicitud_id = solicitud_id
        self.movil_id = movil_id
        self.aceptado_at = get_bogota_timestamp()
        self.estado_servicio = 'aceptado'
    
    def is_aceptado(self):
        """Verifica si el servicio está aceptado"""
        return self.estado_servicio == 'aceptado'
    
    def is_en_ruta(self):
        """Verifica si la móvil está en ruta"""
        return self.estado_servicio == 'en_ruta'
    
    def is_en_sitio(self):
        """Verifica si la móvil está en el sitio"""
        return self.estado_servicio == 'en_sitio'
    
    def is_completado(self):
        """Verifica si el servicio está completado"""
        return self.estado_servicio == 'completado'
    
    def is_cancelado(self):
        """Verifica si el servicio fue cancelado"""
        return self.estado_servicio == 'cancelado'
    
    def iniciar_ruta(self):
        """Marca el servicio como en ruta"""
        if not self.is_aceptado():
            return False, "El servicio debe estar aceptado para iniciar ruta"
        
        self.estado_servicio = 'en_ruta'
        return True, "Ruta iniciada"
    
    def llegar_al_sitio(self):
        """Marca que la móvil llegó al sitio"""
        if not self.is_en_ruta():
            return False, "La móvil debe estar en ruta para llegar al sitio"
        
        self.estado_servicio = 'en_sitio'
        return True, "Llegada al sitio registrada"
    
    def iniciar_servicio(self):
        """Inicia el servicio en el sitio"""
        if not self.is_en_sitio():
            return False, "La móvil debe estar en el sitio para iniciar el servicio"
        
        if self.iniciado_at:
            return False, "El servicio ya fue iniciado"
        
        self.iniciado_at = get_bogota_timestamp()
        return True, "Servicio iniciado"
    
    def finalizar_servicio(self, observaciones_finales=None):
        """Finaliza el servicio"""
        if not self.iniciado_at:
            return False, "El servicio debe estar iniciado para finalizarse"
        
        if self.finalizado_at:
            return False, "El servicio ya fue finalizado"
        
        self.finalizado_at = get_bogota_timestamp()
        self.estado_servicio = 'completado'
        self.observaciones_finales = observaciones_finales
        
        # Calcular duración en minutos
        duracion = self.finalizado_at - self.iniciado_at
        self.duracion_minutos = int(duracion.total_seconds() / 60)
        
        # Marcar solicitud como completada
        self.solicitud.completar()
        
        return True, "Servicio finalizado exitosamente"
    
    def cancelar_servicio(self, observaciones):
        """Cancela el servicio"""
        if self.is_completado():
            return False, "No se puede cancelar un servicio completado"
        
        self.estado_servicio = 'cancelado'
        self.observaciones_finales = observaciones
        
        # Si ya estaba iniciado, calcular duración parcial
        if self.iniciado_at and not self.finalizado_at:
            self.finalizado_at = get_bogota_timestamp()
            duracion = self.finalizado_at - self.iniciado_at
            self.duracion_minutos = int(duracion.total_seconds() / 60)
        
        return True, "Servicio cancelado"
    
    def tiempo_servicio_activo(self):
        """Calcula el tiempo que lleva activo el servicio"""
        if not self.iniciado_at:
            return None
        
        fin = self.finalizado_at if self.finalizado_at else get_bogota_timestamp()
        return fin - self.iniciado_at
    
    def tiempo_limite_excedido(self):
        """Verifica si se excedió el límite de 1 hora de servicio"""
        if not self.iniciado_at or self.finalizado_at:
            return False
        
        tiempo_activo = self.tiempo_servicio_activo()
        return tiempo_activo and tiempo_activo > timedelta(hours=1)
    
    def tiempo_total_desde_aceptacion(self):
        """Calcula el tiempo total desde que se aceptó la solicitud"""
        fin = self.finalizado_at if self.finalizado_at else get_bogota_timestamp()
        return fin - self.aceptado_at
    
    def agregar_observacion(self, contenido, tipo='progreso'):
        """Agrega una observación al servicio"""
        from app.models.observacion import Observacion
        
        observacion = Observacion(
            servicio_id=self.id,
            contenido=contenido,
            tipo=tipo
        )
        db.session.add(observacion)
        return observacion
    
    def get_observaciones_por_tipo(self, tipo):
        """Obtiene observaciones filtradas por tipo"""
        return [obs for obs in self.observaciones if obs.tipo == tipo]
    
    def to_dict(self):
        """Convierte el objeto a diccionario para JSON"""
        return {
            'id': self.id,
            'solicitud_id': self.solicitud_id,
            'movil_id': self.movil_id,
            'movil_nombre': self.movil.get_nombre_completo() if self.movil else None,
            'aceptado_at': self.aceptado_at.isoformat() if self.aceptado_at else None,
            'iniciado_at': self.iniciado_at.isoformat() if self.iniciado_at else None,
            'finalizado_at': self.finalizado_at.isoformat() if self.finalizado_at else None,
            'observaciones_finales': self.observaciones_finales,
            'estado_servicio': self.estado_servicio,
            'duracion_minutos': self.duracion_minutos,
            'tiempo_servicio_activo_segundos': self.tiempo_servicio_activo().total_seconds() if self.tiempo_servicio_activo() else None,
            'tiempo_limite_excedido': self.tiempo_limite_excedido(),
            'observaciones': [obs.to_dict() for obs in self.observaciones]
        }
    
    def __repr__(self):
        return f'<Servicio {self.id} - Solicitud {self.solicitud_id} - {self.estado_servicio}>'

# Importar otros modelos para evitar problemas de importación circular
from app.models.observacion import Observacion