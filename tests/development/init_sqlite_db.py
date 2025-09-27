#!/usr/bin/env python3
"""
Script para inicializar la base de datos SQLite con datos de prueba
"""

from app import create_app, db
from app.models.usuario import Usuario
from werkzeug.security import generate_password_hash
from datetime import datetime

def init_database():
    """Inicializar base de datos con datos de prueba"""
    app = create_app()
    
    with app.app_context():
        # Crear todas las tablas
        db.create_all()
        print("📊 Tablas creadas exitosamente")
        
        # Verificar si ya existen usuarios
        if Usuario.query.first():
            print("⚠️ La base de datos ya contiene datos")
            return
        
        # Crear usuarios de prueba
        usuarios_prueba = [
            {
                'email': 'tecnico1@synapsis.com',
                'password': 'tecnico123',
                'nombre': 'Juan',
                'apellido': 'Pérez',
                'telefono': '3001234567',
                'rol': 'tecnico'
            },
            {
                'email': 'movil1@synapsis.com',
                'password': 'movil123',
                'nombre': 'María',
                'apellido': 'González',
                'telefono': '3007654321',
                'rol': 'movil'
            },
            {
                'email': 'lider1@synapsis.com',
                'password': 'lider123',
                'nombre': 'Carlos',
                'apellido': 'Rodríguez',
                'telefono': '3009876543',
                'rol': 'lider'
            }
        ]
        
        for user_data in usuarios_prueba:
            usuario = Usuario(
                email=user_data['email'],
                password=user_data['password'],
                nombre=user_data['nombre'],
                apellido=user_data['apellido'],
                rol=user_data['rol'],
                telefono=user_data['telefono']
            )
            db.session.add(usuario)
        
        # Guardar cambios
        db.session.commit()
        print("✅ Usuarios de prueba creados exitosamente:")
        print("   - Técnico: tecnico1@synapsis.com / tecnico123")
        print("   - Móvil: movil1@synapsis.com / movil123")
        print("   - Líder: lider1@synapsis.com / lider123")
        
if __name__ == '__main__':
    init_database()