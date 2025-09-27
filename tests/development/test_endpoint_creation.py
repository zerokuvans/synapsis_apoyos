#!/usr/bin/env python3
"""
Script para probar el endpoint de creación de usuarios
"""

import requests
import json
from app import create_app

def test_user_creation_endpoint():
    """Probar el endpoint de creación de usuarios"""
    app = create_app()
    
    with app.test_client() as client:
        # Datos de prueba para crear un usuario
        user_data = {
            'email': 'endpoint_test@example.com',
            'password': 'test123',
            'nombre': 'Endpoint',
            'apellido': 'Test',
            'rol': 'tecnico',
            'telefono': '3009876543'
        }
        
        try:
            # Simular una petición POST al endpoint de creación
            response = client.post('/lider/usuario/crear', 
                                 data=json.dumps(user_data),
                                 content_type='application/json')
            
            print(f"📡 Respuesta del endpoint: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.get_json()
                print("✅ Usuario creado exitosamente a través del endpoint:")
                print(f"   - Respuesta: {response_data}")
                return True
            else:
                print(f"❌ Error en el endpoint: {response.status_code}")
                print(f"   - Respuesta: {response.get_data(as_text=True)}")
                return False
                
        except Exception as e:
            print(f"❌ Error al probar el endpoint: {str(e)}")
            return False

if __name__ == '__main__':
    test_user_creation_endpoint()