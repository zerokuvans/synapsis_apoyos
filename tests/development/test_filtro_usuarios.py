#!/usr/bin/env python3
"""
Script para probar el filtro de usuarios con autenticación
"""

import requests
from urllib.parse import urljoin

def test_filtro_usuarios():
    """Probar el filtro de usuarios con login"""
    # Crear sesión
    session = requests.Session()
    base_url = 'http://localhost:5000'
    
    print("=== PRUEBA DE FILTRO DE USUARIOS ===")
    
    # Login como líder
    print("1. Haciendo login como líder...")
    login_data = {
        'email': 'lider1@synapsis.com',
        'password': 'lider123'
    }
    
    login_response = session.post(
        urljoin(base_url, '/auth/login'),
        data=login_data,
        allow_redirects=False
    )
    
    print(f"   Status Code: {login_response.status_code}")
    
    if login_response.status_code == 302:
        print("   ✅ Login exitoso")
        
        # Probar filtro de usuarios
        print("\n2. Probando filtro de usuarios con '3'...")
        usuarios_response = session.get(
            urljoin(base_url, '/lider/usuarios'),
            params={'buscar': '3'}
        )
        
        print(f"   Status Code: {usuarios_response.status_code}")
        print(f"   URL final: {usuarios_response.url}")
        
        if usuarios_response.status_code == 200:
            print("   ✅ Página de usuarios accesible")
            
            # Verificar si contiene el usuario '3 logs'
            contains_3logs = '3 logs' in usuarios_response.text
            contains_3logs_email = '3logs@test.com' in usuarios_response.text
            
            print(f"   Contiene '3 logs': {contains_3logs}")
            print(f"   Contiene '3logs@test.com': {contains_3logs_email}")
            
            if contains_3logs or contains_3logs_email:
                print("   ✅ Usuario '3 logs' encontrado en la respuesta")
            else:
                print("   ❌ Usuario '3 logs' NO encontrado en la respuesta")
                
                # Verificar si hay mensaje de "No se encontraron usuarios"
                if 'No se encontraron usuarios' in usuarios_response.text:
                    print("   ⚠️  Mensaje 'No se encontraron usuarios' presente")
                
                # Mostrar parte del HTML para debug
                print("\n   Fragmento del HTML (primeros 1000 caracteres):")
                print(usuarios_response.text[:1000])
        else:
            print("   ❌ No se pudo acceder a la página de usuarios")
            print(f"   Contenido: {usuarios_response.text[:500]}")
    else:
        print("   ❌ Login falló")
        print(f"   Contenido: {login_response.text[:200]}")
    
    print("\n=== FIN DE PRUEBA ===")

if __name__ == '__main__':
    test_filtro_usuarios()