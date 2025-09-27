#!/usr/bin/env python3
"""
Script para verificar qué usuarios están actualmente logueados en el sistema
"""

import os
import sys
from datetime import datetime, timedelta

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.usuario import Usuario
from flask import session
from flask_login import current_user

def check_active_sessions():
    """Verificar sesiones activas"""
    app = create_app()
    
    with app.app_context():
        print("=== VERIFICACIÓN DE SESIONES ACTIVAS ===")
        print(f"Fecha/Hora: {datetime.now()}")
        print()
        
        # Obtener todos los usuarios móviles
        moviles = Usuario.query.filter_by(rol='movil', activo=True).all()
        
        print(f"Total de móviles activos en BD: {len(moviles)}")
        print()
        
        for movil in moviles:
            print(f"- {movil.nombre} {movil.apellido} ({movil.email})")
            print(f"  ID: {movil.id}")
            print(f"  Activo: {movil.activo}")
            print(f"  Creado: {movil.created_at}")
            print()
        
        print("NOTA: Flask-Login no mantiene un registro persistente de sesiones activas.")
        print("Las sesiones se manejan en memoria y cookies del navegador.")
        print("Para verificar sesiones reales, necesitamos implementar un sistema de tracking.")
        print()
        
        # Verificar ubicaciones recientes como proxy de actividad
        from app.models.ubicacion import Ubicacion
        tiempo_limite = datetime.utcnow() - timedelta(minutes=30)
        
        ubicaciones_recientes = db.session.query(Usuario, Ubicacion).join(
            Ubicacion, Usuario.id == Ubicacion.usuario_id
        ).filter(
            Usuario.rol == 'movil',
            Usuario.activo == True,
            Ubicacion.activa == True,
            Ubicacion.timestamp >= tiempo_limite
        ).all()
        
        print(f"Móviles con ubicaciones recientes (últimos 30 min): {len(ubicaciones_recientes)}")
        for usuario, ubicacion in ubicaciones_recientes:
            tiempo_transcurrido = datetime.utcnow() - ubicacion.timestamp
            minutos = int(tiempo_transcurrido.total_seconds() / 60)
            print(f"- {usuario.nombre} {usuario.apellido}: hace {minutos} minutos")
        
if __name__ == '__main__':
    check_active_sessions()