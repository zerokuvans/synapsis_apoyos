#!/usr/bin/env python3
"""
Script para hacer login y probar el mapa del técnico
"""

import requests
import json
from urllib.parse import urljoin

def test_login_and_map():
    """Hacer login y probar el mapa"""
    base_url = "http://localhost:5000"
    session = requests.Session()
    
    print("=== PRUEBA DE LOGIN Y MAPA ===\n")
    
    # 1. Hacer login
    print("1. Haciendo login...")
    login_data = {
        'email': 'tecnico1@synapsis.com',
        'password': 'tecnico123'
    }
    
    login_response = session.post(
        urljoin(base_url, '/auth/login'),
        data=login_data,
        allow_redirects=False
    )
    
    print(f"   Status Code: {login_response.status_code}")
    print(f"   Headers: {dict(login_response.headers)}")
    
    if login_response.status_code == 302:
        print("   ✅ Login exitoso (redirección detectada)")
        redirect_url = login_response.headers.get('Location', '')
        print(f"   Redirigiendo a: {redirect_url}")
    else:
        print("   ❌ Login falló")
        print(f"   Contenido: {login_response.text[:500]}")
        return
    
    # 2. Acceder al mapa
    print("\n2. Accediendo al mapa...")
    mapa_response = session.get(urljoin(base_url, '/tecnico/mapa'))
    
    print(f"   Status Code: {mapa_response.status_code}")
    
    if mapa_response.status_code == 200:
        print("   ✅ Mapa accesible")
        # Verificar si contiene el div del mapa
        if 'id="mapa"' in mapa_response.text:
            print("   ✅ Div del mapa encontrado")
        else:
            print("   ❌ Div del mapa NO encontrado")
            
        # Verificar si contiene Leaflet
        if 'leaflet' in mapa_response.text.lower():
            print("   ✅ Referencias a Leaflet encontradas")
        else:
            print("   ❌ Referencias a Leaflet NO encontradas")
    else:
        print("   ❌ No se pudo acceder al mapa")
        print(f"   Contenido: {mapa_response.text[:500]}")
        return
    
    # 3. Probar API de móviles asignadas
    print("\n3. Probando API de móviles asignadas...")
    api_response = session.get(
        urljoin(base_url, '/tecnico/api/moviles-asignadas'),
        params={'lat': 4.6097, 'lng': -74.0817}
    )
    
    print(f"   Status Code: {api_response.status_code}")
    
    if api_response.status_code == 200:
        print("   ✅ API accesible")
        try:
            data = api_response.json()
            print(f"   Datos recibidos: {json.dumps(data, indent=2, ensure_ascii=False)}")
        except json.JSONDecodeError:
            print("   ❌ Respuesta no es JSON válido")
            print(f"   Contenido: {api_response.text[:500]}")
    else:
        print("   ❌ API no accesible")
        print(f"   Contenido: {api_response.text[:500]}")
    
    print("\n=== FIN DE PRUEBA ===")

if __name__ == '__main__':
    test_login_and_map()