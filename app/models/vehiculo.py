from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from app import db
from app.utils.timezone_utils import get_bogota_timestamp

class Vehiculo(db.Model):
    __tablename__ = 'vehiculos'
    
    id = db.Column(db.Integer, primary_key=True)
    placa = db.Column(db.String(10), unique=True, nullable=False, index=True)
    marca = db.Column(db.String(50), nullable=False)
    modelo = db.Column(db.String(50), nullable=False)
    año = db.Column(db.Integer, nullable=False)
    color = db.Column(db.String(30), nullable=False)
    tipo_vehiculo = db.Column(db.Enum('moto', 'carro', 'camioneta', 'furgon', name='tipo_vehiculo_enum'), nullable=False)
    numero_motor = db.Column(db.String(50))
    numero_chasis = db.Column(db.String(50))
    cilindraje = db.Column(db.String(20))
    combustible = db.Column(db.Enum('gasolina', 'diesel', 'electrico', 'hibrido', name='combustible_enum'), nullable=False)
    activo = db.Column(db.Boolean, default=True, index=True)
    observaciones = db.Column(db.Text)
    
    # Relación con usuario móvil (uno a uno)
    movil_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True, index=True)
    movil = db.relationship('Usuario', backref=db.backref('vehiculo', uselist=False), foreign_keys=[movil_id])
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=get_bogota_timestamp)
    updated_at = db.Column(db.DateTime, default=get_bogota_timestamp, onupdate=get_bogota_timestamp)
    
    def __init__(self, placa, marca, modelo, año, color, tipo_vehiculo, combustible, 
                 numero_motor=None, numero_chasis=None, cilindraje=None, observaciones=None, movil_id=None):
        self.placa = placa.upper()  # Siempre en mayúsculas
        self.marca = marca
        self.modelo = modelo
        self.año = año
        self.color = color
        self.tipo_vehiculo = tipo_vehiculo
        self.combustible = combustible
        self.numero_motor = numero_motor
        self.numero_chasis = numero_chasis
        self.cilindraje = cilindraje
        self.observaciones = observaciones
        self.movil_id = movil_id
        self.activo = True
    
    def get_info_completa(self):
        """Retorna información completa del vehículo"""
        return f"{self.marca} {self.modelo} {self.año} - {self.placa}"
    
    def get_movil_asignado(self):
        """Retorna el nombre del móvil asignado o 'Sin asignar'"""
        if self.movil:
            return self.movil.get_nombre_completo()
        return "Sin asignar"
    
    def is_asignado(self):
        """Verifica si el vehículo está asignado a un móvil"""
        return self.movil_id is not None
    
    def asignar_movil(self, movil_id):
        """Asigna un móvil al vehículo"""
        # Verificar que el móvil no tenga otro vehículo asignado
        from app.models.usuario import Usuario
        movil = Usuario.query.get(movil_id)
        if movil and movil.rol == 'movil':
            # Desasignar vehículo anterior del móvil si existe
            vehiculo_anterior = Vehiculo.query.filter_by(movil_id=movil_id).first()
            if vehiculo_anterior and vehiculo_anterior.id != self.id:
                vehiculo_anterior.movil_id = None
            
            self.movil_id = movil_id
            return True
        return False
    
    def desasignar_movil(self):
        """Desasigna el móvil del vehículo"""
        self.movil_id = None
    
    def to_dict(self):
        """Convierte el objeto a diccionario"""
        return {
            'id': self.id,
            'placa': self.placa,
            'marca': self.marca,
            'modelo': self.modelo,
            'año': self.año,
            'color': self.color,
            'tipo_vehiculo': self.tipo_vehiculo,
            'numero_motor': self.numero_motor,
            'numero_chasis': self.numero_chasis,
            'cilindraje': self.cilindraje,
            'combustible': self.combustible,
            'activo': self.activo,
            'observaciones': self.observaciones,
            'movil_id': self.movil_id,
            'movil_asignado': self.get_movil_asignado(),
            'info_completa': self.get_info_completa(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Vehiculo {self.placa} - {self.marca} {self.modelo}>'

# Importar Usuario para evitar problemas de importación circular
from app.models.usuario import Usuario