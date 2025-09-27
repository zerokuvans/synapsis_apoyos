#!/usr/bin/env python3
"""
Script para agregar campo de última actividad a la tabla usuarios
para trackear sesiones activas
"""

import os
import sys
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.usuario import Usuario
from sqlalchemy import text

def add_last_activity_field():
    """Agregar campo last_activity a la tabla usuarios"""
    app = create_app()
    
    with app.app_context():
        try:
            # Verificar si la columna ya existe
            result = db.session.execute(
                text("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
                     "WHERE TABLE_NAME = 'usuarios' AND COLUMN_NAME = 'last_activity'")
            ).fetchone()
            
            if result:
                print("✅ La columna 'last_activity' ya existe en la tabla usuarios")
            else:
                # Agregar la columna
                db.session.execute(
                    text("ALTER TABLE usuarios ADD COLUMN last_activity DATETIME NULL")
                )
                db.session.commit()
                print("✅ Columna 'last_activity' agregada exitosamente")
            
            # Actualizar la actividad de María González como ejemplo
            maria = Usuario.query.filter_by(email='movil1@synapsis.com').first()
            if maria:
                db.session.execute(
                    text("UPDATE usuarios SET last_activity = :activity WHERE id = :user_id"),
                    {'activity': datetime.utcnow(), 'user_id': maria.id}
                )
                db.session.commit()
                print(f"✅ Actividad actualizada para {maria.nombre} {maria.apellido}")
            
            print("\n=== ESTADO ACTUAL DE MÓVILES ===")
            moviles = db.session.execute(
                text("SELECT id, nombre, apellido, email, last_activity FROM usuarios WHERE rol = 'movil'")
            ).fetchall()
            
            for movil in moviles:
                actividad = movil[4] if movil[4] else "Nunca"
                print(f"- {movil[1]} {movil[2]} ({movil[3]}): {actividad}")
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error: {e}")

if __name__ == '__main__':
    add_last_activity_field()