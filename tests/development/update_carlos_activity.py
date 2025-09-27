#!/usr/bin/env python3
"""
Script para actualizar la actividad de Carlos Martínez
"""

import os
import sys
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.usuario import Usuario
from sqlalchemy import text

def update_carlos_activity():
    """Actualizar actividad de Carlos Martínez"""
    app = create_app()
    
    with app.app_context():
        try:
            # Buscar a Carlos
            carlos = Usuario.query.filter_by(email='movil2@synapsis.com').first()
            
            if carlos:
                # Actualizar su actividad
                db.session.execute(
                    text("UPDATE usuarios SET last_activity = :activity WHERE id = :user_id"),
                    {'activity': datetime.utcnow(), 'user_id': carlos.id}
                )
                db.session.commit()
                print(f"✅ Actividad actualizada para {carlos.nombre} {carlos.apellido}")
            else:
                print("❌ No se encontró a Carlos Martínez")
                
            # Verificar estado actual
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
    update_carlos_activity()