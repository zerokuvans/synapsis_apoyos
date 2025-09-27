#!/usr/bin/env python3
"""
Script para simular el login de María y verificar que solo ella aparezca en el mapa
"""

import os
import sys
import requests
from datetime import datetime, timedelta

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.usuario import Usuario
from sqlalchemy import text

def test_maria_activity():
    """Simular actividad de María y verificar API"""
    app = create_app()
    
    with app.app_context():
        print("=== SIMULANDO LOGIN DE MARÍA ===")
        print(f"Fecha/Hora: {datetime.now()}")
        print()
        
        # Actualizar actividad de María (simular login)
        maria = Usuario.query.filter_by(email='movil1@synapsis.com').first()
        if maria:
            db.session.execute(
                text("UPDATE usuarios SET last_activity = :activity WHERE id = :user_id"),
                {'activity': datetime.utcnow(), 'user_id': maria.id}
            )
            db.session.commit()
            print(f"✅ Actividad actualizada para {maria.nombre} {maria.apellido}")
        
        # Limpiar actividad de Carlos (simular logout)
        carlos = Usuario.query.filter_by(email='movil2@synapsis.com').first()
        if carlos:
            db.session.execute(
                text("UPDATE usuarios SET last_activity = NULL WHERE id = :user_id"),
                {'user_id': carlos.id}
            )
            db.session.commit()
            print(f"✅ Actividad limpiada para {carlos.nombre} {carlos.apellido} (logout simulado)")
        
        print()
        
        # Verificar estado actual
        print("=== ESTADO ACTUAL DE MÓVILES ===")
        moviles = db.session.execute(
            text("SELECT id, nombre, apellido, email, last_activity FROM usuarios WHERE rol = 'movil'")
        ).fetchall()
        
        for movil in moviles:
            actividad = movil[4] if movil[4] else "Nunca"
            print(f"- {movil[1]} {movil[2]} ({movil[3]}): {actividad}")
        
        print()
        
        # Verificar móviles activas según la nueva lógica
        tiempo_limite = datetime.utcnow() - timedelta(minutes=30)
        moviles_activos = db.session.execute(
            text("SELECT id, nombre, apellido, email, last_activity "
                 "FROM usuarios "
                 "WHERE rol = 'movil' AND activo = 1 AND last_activity >= :tiempo_limite"),
            {'tiempo_limite': tiempo_limite}
        ).fetchall()
        
        print(f"=== MÓVILES ACTIVAS (últimos 30 min): {len(moviles_activos)} ===")
        for movil in moviles_activos:
            print(f"- {movil[1]} {movil[2]} ({movil[3]})")
        
        print()
        print("✅ Ahora solo María debería aparecer en el mapa del líder")
        print("🔗 Accede a http://localhost:5000 como líder para verificar")
        print("👤 Usuario: lider1@synapsis.com | Contraseña: lider123")

def test_api_call():
    """Probar la API directamente"""
    print("\n=== PROBANDO API DIRECTAMENTE ===")
    try:
        # Hacer una petición a la API (sin autenticación para prueba)
        response = requests.get('http://localhost:5000/api/lider/moviles-activas')
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API responde correctamente")
            print(f"📊 Móviles activas encontradas: {data.get('total', 0)}")
            for movil in data.get('moviles', []):
                print(f"- {movil['nombre']}")
        else:
            print(f"❌ Error en API: {response.status_code}")
    except Exception as e:
        print(f"❌ Error conectando a API: {e}")
        print("💡 Asegúrate de que el servidor esté ejecutándose")

if __name__ == '__main__':
    test_maria_activity()
    test_api_call()