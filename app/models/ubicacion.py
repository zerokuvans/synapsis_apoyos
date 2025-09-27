from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from app import db
from app.utils.timezone_utils import get_bogota_timestamp
import math

class Ubicacion(db.Model):
    __tablename__ = 'ubicaciones'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False, index=True)
    latitud = db.Column(db.Numeric(10, 8), nullable=False)
    longitud = db.Column(db.Numeric(11, 8), nullable=False)
    timestamp = db.Column(db.DateTime, default=get_bogota_timestamp, index=True)
    activa = db.Column(db.Boolean, default=True, index=True)
    
    def __init__(self, usuario_id, latitud, longitud):
        self.usuario_id = usuario_id
        self.latitud = latitud
        self.longitud = longitud
        self.timestamp = get_bogota_timestamp()
        self.activa = True
    
    def get_coordenadas(self):
        """Retorna las coordenadas como tupla"""
        return (float(self.latitud), float(self.longitud))
    
    def calcular_distancia(self, otra_ubicacion):
        """Calcula la distancia en kilómetros a otra ubicación usando la fórmula de Haversine"""
        if isinstance(otra_ubicacion, Ubicacion):
            lat2, lon2 = otra_ubicacion.get_coordenadas()
        elif isinstance(otra_ubicacion, (tuple, list)) and len(otra_ubicacion) == 2:
            lat2, lon2 = otra_ubicacion
        else:
            raise ValueError("otra_ubicacion debe ser una instancia de Ubicacion o una tupla (lat, lon)")
        
        lat1, lon1 = self.get_coordenadas()
        
        # Convertir grados a radianes
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Diferencias
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        # Fórmula de Haversine
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radio de la Tierra en kilómetros
        radio_tierra = 6371
        
        return radio_tierra * c
    
    def esta_cerca_de(self, otra_ubicacion, radio_km=10):
        """Verifica si está dentro del radio especificado de otra ubicación"""
        distancia = self.calcular_distancia(otra_ubicacion)
        return distancia <= radio_km
    
    def es_reciente(self, minutos=5):
        """Verifica si la ubicación es reciente (por defecto últimos 5 minutos)"""
        tiempo_limite = get_bogota_timestamp() - timedelta(minutes=minutos)
        return self.timestamp >= tiempo_limite
    
    def desactivar(self):
        """Desactiva la ubicación"""
        self.activa = False
    
    def actualizar_coordenadas(self, latitud, longitud):
        """Actualiza las coordenadas y el timestamp"""
        self.latitud = latitud
        self.longitud = longitud
        self.timestamp = get_bogota_timestamp()
        self.activa = True
    
    @staticmethod
    def obtener_ubicaciones_cercanas(latitud, longitud, radio_km=10, solo_activas=True, solo_recientes=True):
        """Obtiene ubicaciones cercanas a las coordenadas especificadas"""
        query = Ubicacion.query
        
        if solo_activas:
            query = query.filter_by(activa=True)
        
        if solo_recientes:
            tiempo_limite = get_bogota_timestamp() - timedelta(minutes=5)
            query = query.filter(Ubicacion.timestamp >= tiempo_limite)
        
        ubicaciones = query.all()
        ubicaciones_cercanas = []
        
        for ubicacion in ubicaciones:
            distancia = ubicacion.calcular_distancia((latitud, longitud))
            if distancia <= radio_km:
                ubicaciones_cercanas.append({
                    'ubicacion': ubicacion,
                    'distancia_km': round(distancia, 2)
                })
        
        # Ordenar por distancia
        ubicaciones_cercanas.sort(key=lambda x: x['distancia_km'])
        
        return ubicaciones_cercanas
    
    @staticmethod
    def obtener_moviles_cercanas(latitud, longitud, radio_km=10):
        """Obtiene móviles de apoyo cercanas a las coordenadas especificadas"""
        from app.models.usuario import Usuario
        
        # Subconsulta para obtener la ubicación más reciente de cada móvil
        subquery = db.session.query(
            Ubicacion.usuario_id,
            db.func.max(Ubicacion.timestamp).label('max_timestamp')
        ).filter(
            Ubicacion.activa == True
        ).group_by(Ubicacion.usuario_id).subquery()
        
        # Consulta principal
        query = db.session.query(Ubicacion, Usuario).join(
            Usuario, Ubicacion.usuario_id == Usuario.id
        ).join(
            subquery, 
            db.and_(
                Ubicacion.usuario_id == subquery.c.usuario_id,
                Ubicacion.timestamp == subquery.c.max_timestamp
            )
        ).filter(
            Usuario.rol == 'movil',
            Usuario.activo == True
        )
        
        resultados = query.all()
        moviles_cercanas = []
        
        for ubicacion, usuario in resultados:
            if ubicacion.es_reciente():
                distancia = ubicacion.calcular_distancia((latitud, longitud))
                if distancia <= radio_km:
                    moviles_cercanas.append({
                        'usuario': usuario,
                        'ubicacion': ubicacion,
                        'distancia_km': round(distancia, 2)
                    })
        
        # Ordenar por distancia
        moviles_cercanas.sort(key=lambda x: x['distancia_km'])
        
        return moviles_cercanas
    
    def to_dict(self):
        """Convierte el objeto a diccionario para JSON"""
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'usuario_nombre': self.usuario.get_nombre_completo() if self.usuario else None,
            'latitud': float(self.latitud),
            'longitud': float(self.longitud),
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'activa': self.activa,
            'es_reciente': self.es_reciente()
        }
    
    def __repr__(self):
        return f'<Ubicacion {self.id} - Usuario {self.usuario_id} - ({self.latitud}, {self.longitud})>'