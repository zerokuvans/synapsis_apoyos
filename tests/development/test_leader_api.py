#!/usr/bin/env python3
"""
Script para probar la API del líder y verificar móviles activas
"""

import requests
import json
from datetime import datetime

def test_leader_api():
    """Probar la API del líder"""
    print("=== PROBANDO API DEL LÍDER ===")
    print(f"Fecha/Hora: {datetime.now()}")
    print()
    
    # URL base del servidor
    base_url = "http://localhost:5000"
    
    # Crear sesión para mantener cookies
    session = requests.Session()
    
    try:
        # 1. Login como líder
        print("1. Intentando login como líder...")
        login_data = {
            'email': 'lider@synapsis.com',
            'password': 'lider123'
        }
        
        login_response = session.post(f"{base_url}/auth/login", data=login_data)
        
        if login_response.status_code == 200:
            print("✅ Login exitoso")
        else:
            print(f"❌ Error en login: {login_response.status_code}")
            return
        
        # 2. Probar API de móviles en tiempo real
        print("\n2. Probando API de móviles en tiempo real...")
        moviles_response = session.get(f"{base_url}/lider/api/moviles-tiempo-real")
        
        print(f"Status code: {moviles_response.status_code}")
        print(f"Respuesta raw: {moviles_response.text}")
        
        if moviles_response.status_code == 200:
            try:
                moviles_data = moviles_response.json()
                print("✅ API de móviles ejecutada exitosamente")
                print(f"📊 Datos recibidos:")
                print(json.dumps(moviles_data, indent=2, ensure_ascii=False))
                
                moviles = moviles_data.get('moviles', [])
                print(f"\n📱 Total móviles activas: {len(moviles)}")
                
                for movil in moviles:
                    print(f"- {movil['nombre']}: {movil['estado_texto']} ({movil['coordenadas']['lat']}, {movil['coordenadas']['lng']})")
            except json.JSONDecodeError as e:
                print(f"❌ Error decodificando JSON: {e}")
                print(f"Respuesta: {moviles_response.text}")
        else:
            print(f"❌ Error en API de móviles: {moviles_response.status_code}")
            print(f"Respuesta: {moviles_response.text}")
        
        # 3. Probar API de solicitudes en tiempo real
        print("\n3. Probando API de solicitudes en tiempo real...")
        solicitudes_response = session.get(f"{base_url}/lider/api/solicitudes-tiempo-real")
        
        if solicitudes_response.status_code == 200:
            solicitudes_data = solicitudes_response.json()
            print("✅ API de solicitudes ejecutada exitosamente")
            solicitudes = solicitudes_data.get('solicitudes', [])
            print(f"📋 Total solicitudes activas: {len(solicitudes)}")
        else:
            print(f"❌ Error en API de solicitudes: {solicitudes_response.status_code}")
        
        # 4. Probar API de servicios en tiempo real
        print("\n4. Probando API de servicios en tiempo real...")
        servicios_response = session.get(f"{base_url}/lider/api/servicios-tiempo-real")
        
        if servicios_response.status_code == 200:
            servicios_data = servicios_response.json()
            print("✅ API de servicios ejecutada exitosamente")
            servicios = servicios_data.get('servicios', [])
            print(f"🔧 Total servicios activos: {len(servicios)}")
        else:
            print(f"❌ Error en API de servicios: {servicios_response.status_code}")
            
    except Exception as e:
        print(f"❌ Error general: {e}")

if __name__ == '__main__':
    test_leader_api()