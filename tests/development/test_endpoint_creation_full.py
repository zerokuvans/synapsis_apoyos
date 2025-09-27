#!/usr/bin/env python3
"""
Script para probar el endpoint de creación de usuarios completo
"""

import requests
import json
import random
import string
from app import create_app, db
from app.models.usuario import Usuario

def generate_random_email():
    """Generar un email aleatorio para evitar conflictos"""
    random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"test_{random_string}@example.com"

def test_endpoint_creation():
    """Probar el endpoint de creación de usuarios"""
    base_url = "http://127.0.0.1:5000"
    
    # Datos de prueba
    email = generate_random_email()
    test_data = {
        'email': email,
        'password': 'test123',
        'nombre': 'Test',
        'apellido': 'Endpoint',
        'rol': 'tecnico',
        'telefono': '3001234567'
    }
    
    print(f"🔄 Probando endpoint de creación con email: {email}")
    
    try:
        # Hacer la petición POST al endpoint
        response = requests.post(
            f"{base_url}/lider/usuario/crear",
            data=test_data,
            timeout=10
        )
        
        print(f"📡 Respuesta del servidor:")
        print(f"   - Status Code: {response.status_code}")
        print(f"   - Headers: {dict(response.headers)}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            try:
                response_data = response.json()
                print(f"   - JSON Response: {json.dumps(response_data, indent=2)}")
            except:
                print(f"   - Response Text: {response.text}")
        else:
            print(f"   - Response Text (first 500 chars): {response.text[:500]}")
        
        # Verificar si el usuario se guardó en la base de datos
        app = create_app()
        with app.app_context():
            found_user = Usuario.query.filter_by(email=email).first()
            
            if found_user:
                print("\n✅ ¡ÉXITO! Usuario encontrado en la base de datos:")
                print(f"   - ID: {found_user.id}")
                print(f"   - Email: {found_user.email}")
                print(f"   - Nombre: {found_user.get_nombre_completo()}")
                print(f"   - Rol: {found_user.rol}")
                print(f"   - Activo: {found_user.activo}")
                print(f"   - Fecha creación: {found_user.created_at}")
                
                # Limpiar - eliminar el usuario de prueba
                db.session.delete(found_user)
                db.session.commit()
                print("🧹 Usuario de prueba eliminado")
                
                return True
            else:
                print("\n❌ ERROR: Usuario NO encontrado en la base de datos")
                print("   El endpoint respondió pero el usuario no se guardó")
                return False
                
    except requests.exceptions.ConnectionError:
        print("❌ Error de conexión: No se pudo conectar al servidor")
        print("   Asegúrate de que la aplicación Flask esté ejecutándose en http://127.0.0.1:5000")
        return False
    except requests.exceptions.Timeout:
        print("❌ Error de timeout: El servidor tardó demasiado en responder")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        print(f"   Tipo de error: {type(e).__name__}")
        return False

def test_with_login():
    """Probar el endpoint con autenticación de líder"""
    base_url = "http://127.0.0.1:5000"
    
    # Crear sesión para mantener cookies
    session = requests.Session()
    
    try:
        # Primero intentar hacer login como líder
        login_data = {
            'email': 'lider1@synapsis.com',
            'password': 'lider123',
            'role': 'lider'
        }
        
        print("🔐 Intentando hacer login como líder...")
        login_response = session.post(
            f"{base_url}/auth/api/login",
            json=login_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"   - Login Status Code: {login_response.status_code}")
        
        if login_response.status_code == 200:
            print("✅ Login exitoso")
            
            # Ahora probar la creación de usuario
            email = generate_random_email()
            test_data = {
                'email': email,
                'password': 'test123',
                'nombre': 'Test',
                'apellido': 'Authenticated',
                'rol': 'tecnico',
                'telefono': '3001234567'
            }
            
            print(f"🔄 Creando usuario autenticado con email: {email}")
            
            response = session.post(
                f"{base_url}/lider/usuario/crear",
                json=test_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            print(f"📡 Respuesta del endpoint autenticado:")
            print(f"   - Status Code: {response.status_code}")
            
            if response.headers.get('content-type', '').startswith('application/json'):
                try:
                    response_data = response.json()
                    print(f"   - JSON Response: {json.dumps(response_data, indent=2)}")
                except:
                    print(f"   - Response Text: {response.text}")
            else:
                print(f"   - Response Text (first 500 chars): {response.text[:500]}")
            
            # Verificar en base de datos
            app = create_app()
            with app.app_context():
                found_user = Usuario.query.filter_by(email=email).first()
                
                if found_user:
                    print("\n✅ ¡ÉXITO! Usuario autenticado encontrado en la base de datos")
                    
                    # Limpiar
                    db.session.delete(found_user)
                    db.session.commit()
                    print("🧹 Usuario de prueba eliminado")
                    
                    return True
                else:
                    print("\n❌ ERROR: Usuario autenticado NO encontrado en la base de datos")
                    return False
        else:
            print("❌ Error en login, probando sin autenticación...")
            return test_endpoint_creation()
            
    except Exception as e:
        print(f"❌ Error en prueba autenticada: {str(e)}")
        print("🔄 Intentando sin autenticación...")
        return test_endpoint_creation()

if __name__ == '__main__':
    print("=== Prueba de Endpoint de Creación de Usuarios ===")
    print()
    
    # Probar con autenticación primero
    success = test_with_login()
    
    if success:
        print("\n🎉 ¡ÉXITO! El endpoint de creación funciona correctamente")
    else:
        print("\n❌ FALLO: El endpoint de creación tiene problemas")
        exit(1)