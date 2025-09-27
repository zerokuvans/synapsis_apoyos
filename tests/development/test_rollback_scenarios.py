#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import requests
import random
import string
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.usuario import Usuario

def generate_random_email():
    """Generar email aleatorio para pruebas"""
    random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"test_{random_string}@example.com"

def test_rollback_scenarios():
    """Probar escenarios que podrían causar rollbacks"""
    base_url = "http://127.0.0.1:5000"
    
    print("=== Prueba de Escenarios de Rollback ===")
    
    # Crear sesión para mantener cookies
    session = requests.Session()
    
    try:
        # Login como líder
        login_data = {
            'email': 'lider1@synapsis.com',
            'password': 'lider123',
            'role': 'lider'
        }
        
        print("🔐 Haciendo login como líder...")
        login_response = session.post(
            f"{base_url}/auth/api/login",
            json=login_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if login_response.status_code != 200:
            print(f"❌ Error en login: {login_response.status_code}")
            return
        
        print("✅ Login exitoso")
        
        # Escenario 1: Email duplicado
        print("\n📋 Escenario 1: Intentar crear usuario con email duplicado")
        duplicate_data = {
            'nombre': 'Test',
            'apellido': 'Duplicate',
            'email': 'lider1@synapsis.com',  # Email que ya existe
            'telefono': '3001234567',
            'rol': 'tecnico',
            'password': 'password123'
        }
        
        response = session.post(
            f"{base_url}/lider/usuario/crear",
            json=duplicate_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"   - Status Code: {response.status_code}")
        if response.status_code == 400:
            result = response.json()
            print(f"   ✅ Error manejado correctamente: {result.get('message')}")
        else:
            print(f"   ❌ Respuesta inesperada: {response.text[:200]}")
        
        # Escenario 2: Datos faltantes
        print("\n📋 Escenario 2: Intentar crear usuario con datos faltantes")
        incomplete_data = {
            'nombre': 'Test',
            'apellido': 'Incomplete',
            'email': generate_random_email(),
            # Falta telefono, rol y password
        }
        
        response = session.post(
            f"{base_url}/lider/usuario/crear",
            json=incomplete_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"   - Status Code: {response.status_code}")
        if response.status_code == 400:
            result = response.json()
            print(f"   ✅ Error manejado correctamente: {result.get('message')}")
        else:
            print(f"   ❌ Respuesta inesperada: {response.text[:200]}")
        
        # Escenario 3: Rol inválido
        print("\n📋 Escenario 3: Intentar crear usuario con rol inválido")
        invalid_role_data = {
            'nombre': 'Test',
            'apellido': 'InvalidRole',
            'email': generate_random_email(),
            'telefono': '3001234567',
            'rol': 'admin_supremo',  # Rol que no existe
            'password': 'password123'
        }
        
        response = session.post(
            f"{base_url}/lider/usuario/crear",
            json=invalid_role_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"   - Status Code: {response.status_code}")
        if response.status_code in [400, 500]:
            result = response.json()
            print(f"   ✅ Error manejado: {result.get('message')}")
        else:
            print(f"   ⚠️ Usuario creado con rol inválido: {response.text[:200]}")
        
        # Verificar que no se crearon usuarios inválidos
        print("\n🔍 Verificando integridad de la base de datos...")
        app = create_app()
        with app.app_context():
            # Verificar que no hay usuarios con emails duplicados
            emails = [user.email for user in Usuario.query.all()]
            if len(emails) != len(set(emails)):
                print("❌ Se encontraron emails duplicados en la base de datos")
            else:
                print("✅ No hay emails duplicados")
            
            # Verificar que no hay usuarios con roles inválidos
            valid_roles = ['tecnico', 'movil', 'lider']
            invalid_users = Usuario.query.filter(~Usuario.rol.in_(valid_roles)).all()
            if invalid_users:
                print(f"❌ Se encontraron {len(invalid_users)} usuarios con roles inválidos")
                for user in invalid_users:
                    print(f"   - {user.email}: {user.rol}")
            else:
                print("✅ Todos los usuarios tienen roles válidos")
        
        print("\n🎉 Prueba de rollbacks completada")
        
    except Exception as e:
        print(f"❌ Error durante la prueba: {str(e)}")

if __name__ == '__main__':
    test_rollback_scenarios()