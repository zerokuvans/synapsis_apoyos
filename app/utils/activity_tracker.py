#!/usr/bin/env python3
"""
Utilidad para trackear la actividad de usuarios y mantener sesiones activas
"""

from datetime import datetime
from flask import request
from flask_login import current_user
from app import db
from sqlalchemy import text

def update_user_activity():
    """Actualizar la última actividad del usuario actual"""
    if current_user.is_authenticated:
        try:
            # Actualizar last_activity del usuario actual
            db.session.execute(
                text("UPDATE usuarios SET last_activity = :activity WHERE id = :user_id"),
                {'activity': datetime.utcnow(), 'user_id': current_user.id}
            )
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            # Error silently handled in production

def track_activity_middleware(app):
    """Middleware para trackear actividad de usuarios"""
    
    @app.before_request
    def before_request():
        # Solo trackear para usuarios móviles autenticados
        if (current_user.is_authenticated and 
            current_user.rol == 'movil' and
            request.endpoint and
            not request.endpoint.startswith('static')):
            update_user_activity()

def get_active_moviles(minutes=30):
    """Obtener móviles con actividad reciente"""
    from datetime import timedelta
    from app.models.usuario import Usuario
    
    tiempo_limite = datetime.utcnow() - timedelta(minutes=minutes)
    
    # Consultar móviles con actividad reciente
    moviles_activos = db.session.execute(
        text("SELECT id, nombre, apellido, email, last_activity "
             "FROM usuarios "
             "WHERE rol = 'movil' AND activo = 1 AND last_activity >= :tiempo_limite"),
        {'tiempo_limite': tiempo_limite}
    ).fetchall()
    
    return moviles_activos