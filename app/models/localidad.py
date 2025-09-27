from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from app import db
from app.utils.timezone_utils import get_bogota_timestamp
from app.utils.polygon_utils import (
    point_in_polygon, 
    validate_polygon_coordinates,
    calculate_polygon_centroid,
    get_polygon_bounds,
    convert_to_geojson
)

class Localidad(db.Model):
    __tablename__ = 'localidades'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, index=True)
    codigo = db.Column(db.String(10), unique=True, nullable=False, index=True)
    area = db.Column(db.Numeric(12, 4), nullable=True, comment='Área en hectáreas')
    geometria = db.Column(db.JSON, nullable=True, comment='Coordenadas del polígono en formato GeoJSON')
    latitud_centro = db.Column(db.Numeric(10, 8), nullable=True, comment='Latitud del centroide')
    longitud_centro = db.Column(db.Numeric(11, 8), nullable=True, comment='Longitud del centroide')
    descripcion = db.Column(db.Text, nullable=True)
    activa = db.Column(db.Boolean, default=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=get_bogota_timestamp, nullable=False)
    updated_at = db.Column(db.DateTime, default=get_bogota_timestamp, onupdate=get_bogota_timestamp, nullable=False)
    
    # Índices compuestos
    __table_args__ = (
        db.Index('idx_localidades_centro', 'latitud_centro', 'longitud_centro'),
    )
    
    def __repr__(self):
        return f'<Localidad {self.codigo}: {self.nombre}>'
    
    def to_dict(self, include_geometry=False):
        """Convierte el objeto a diccionario para JSON"""
        data = {
            'id': self.id,
            'codigo': self.codigo,
            'nombre': self.nombre,
            'area': float(self.area) if self.area else None,
            'latitud_centro': float(self.latitud_centro) if self.latitud_centro else None,
            'longitud_centro': float(self.longitud_centro) if self.longitud_centro else None,
            'descripcion': self.descripcion,
            'activa': self.activa,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_geometry and self.geometria:
            data['geometria'] = self.geometria
        
        return data
    
    def get_centroide(self):
        """Retorna las coordenadas del centroide"""
        if self.latitud_centro and self.longitud_centro:
            return {
                'lat': float(self.latitud_centro),
                'lng': float(self.longitud_centro)
            }
        return None
    
    @classmethod
    def get_by_codigo(cls, codigo):
        """Busca una localidad por su código"""
        return cls.query.filter_by(codigo=codigo, activa=True).first()
    
    @classmethod
    def get_all_active(cls):
        """Retorna todas las localidades activas"""
        return cls.query.filter_by(activa=True).order_by(cls.codigo).all()
    
    @classmethod
    def buscar_por_nombre(cls, nombre):
        """Busca localidades por nombre (búsqueda parcial)"""
        return cls.query.filter(
            cls.nombre.ilike(f'%{nombre}%'),
            cls.activa == True
        ).order_by(cls.nombre).all()
    
    @classmethod
    def get_localidad_por_coordenadas(cls, latitud, longitud, radio_km=1.0):
        """Encuentra la localidad más cercana a unas coordenadas dadas"""
        # Cálculo simple de distancia usando diferencias de coordenadas
        # Para mayor precisión se podría usar la fórmula de Haversine
        radio_grados = radio_km / 111.0  # Aproximación: 1 grado ≈ 111 km
        
        return cls.query.filter(
            cls.latitud_centro.between(latitud - radio_grados, latitud + radio_grados),
            cls.longitud_centro.between(longitud - radio_grados, longitud + radio_grados),
            cls.activa == True
        ).first()
    
    @classmethod
    def find_localidad_by_point(cls, latitud, longitud):
        """Encuentra la localidad que contiene un punto específico usando polígonos precisos"""
        localidades = cls.query.filter(
            cls.geometria.isnot(None),
            cls.activa == True
        ).all()
        
        for localidad in localidades:
            if localidad.contains_point(latitud, longitud):
                return localidad
        
        return None
    
    def contains_point(self, latitud, longitud):
        """Verifica si un punto está dentro de esta localidad usando el polígono preciso"""
        if not self.geometria or 'geometry' not in self.geometria:
            return False
        
        coordinates = self.geometria['geometry'].get('coordinates', [])
        return point_in_polygon(latitud, longitud, coordinates)
    
    def get_polygon_coordinates(self):
        """Retorna las coordenadas del polígono en formato simplificado"""
        if not self.geometria or 'geometry' not in self.geometria:
            return None
        
        coordinates = self.geometria['geometry'].get('coordinates', [])
        if not validate_polygon_coordinates(coordinates):
            return None
        
        return coordinates
    
    def get_geojson(self, include_properties=True):
        """Retorna la geometría en formato GeoJSON"""
        if not self.geometria:
            return None
        
        if include_properties:
            properties = {
                'codigo': self.codigo,
                'nombre': self.nombre,
                'area': float(self.area) if self.area else None
            }
            return convert_to_geojson(
                self.geometria['geometry'].get('coordinates', []),
                properties
            )
        
        return self.geometria
    
    def get_bounds(self):
        """Retorna los límites del polígono (bounding box)"""
        coordinates = self.get_polygon_coordinates()
        if not coordinates:
            return None
        
        return get_polygon_bounds(coordinates)
    
    def validate_geometry(self):
        """Valida que la geometría de la localidad sea correcta"""
        if not self.geometria or 'geometry' not in self.geometria:
            return False
        
        coordinates = self.geometria['geometry'].get('coordinates', [])
        return validate_polygon_coordinates(coordinates)