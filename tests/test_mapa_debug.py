#!/usr/bin/env python3
"""
Script para probar y debuggear el mapa de móviles
"""

import requests
import sys
import os

# Agregar el directorio del proyecto al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.usuario import Usuario

def test_mapa_debug():
    """Prueba detallada del mapa de móviles"""
    
    app = create_app()
    
    with app.test_client() as client:
        with app.app_context():
            print("=== PRUEBA DE DEBUG DEL MAPA DE MÓVILES ===\n")
            
            # 1. Verificar usuarios móviles en la base de datos
            print("1. Verificando usuarios móviles...")
            usuarios_moviles = Usuario.query.filter_by(rol='movil', activo=True).all()
            print(f"   Usuarios móviles activos encontrados: {len(usuarios_moviles)}")
            
            if not usuarios_moviles:
                print("   ❌ No hay usuarios móviles activos")
                return
            
            usuario = usuarios_moviles[0]
            print(f"   ✅ Usuario de prueba: {usuario.nombre} ({usuario.email})")
            
            # 2. Intentar login
            print("\n2. Intentando login...")
            login_data = {
                'email': usuario.email,
                'password': 'movil123'  # Contraseña correcta para usuarios móviles
            }
            
            response = client.post('/auth/login', data=login_data, follow_redirects=False)
            print(f"   Status del login: {response.status_code}")
            
            if response.status_code != 302:
                print("   ❌ Login falló")
                return
            
            print("   ✅ Login exitoso")
            
            # 3. Acceder al dashboard móvil
            print("\n3. Accediendo al dashboard móvil...")
            response = client.get('/movil/dashboard')
            print(f"   Status: {response.status_code}")
            
            if response.status_code != 200:
                print("   ❌ No se pudo acceder al dashboard")
                return
            
            print("   ✅ Dashboard accesible")
            
            # 4. Acceder al mapa
            print("\n4. Accediendo al mapa...")
            response = client.get('/movil/mapa')
            print(f"   Status: {response.status_code}")
            
            if response.status_code != 200:
                print("   ❌ No se pudo acceder al mapa")
                return
            
            html_content = response.data.decode('utf-8')
            
            # 5. Verificar elementos críticos del mapa
            print("\n5. Verificando elementos del mapa...")
            
            # Verificar div del mapa
            if 'id="mapa"' in html_content:
                print("   ✅ Div del mapa encontrado")
            else:
                print("   ❌ Div del mapa NO encontrado")
            
            # Verificar Leaflet CSS
            if 'leaflet.css' in html_content:
                print("   ✅ Leaflet CSS incluido")
            else:
                print("   ❌ Leaflet CSS NO incluido")
            
            # Verificar Leaflet JS
            if 'leaflet.js' in html_content:
                print("   ✅ Leaflet JS incluido")
            else:
                print("   ❌ Leaflet JS NO incluido")
            
            # Verificar Leaflet Routing Machine
            if 'leaflet-routing-machine' in html_content:
                print("   ✅ Leaflet Routing Machine incluido")
            else:
                print("   ❌ Leaflet Routing Machine NO incluido")
            
            # Verificar clase MapaMovilGPS
            if 'class MapaMovilGPS' in html_content:
                print("   ✅ Clase MapaMovilGPS encontrada")
            else:
                print("   ❌ Clase MapaMovilGPS NO encontrada")
            
            # Verificar inicialización
            if 'new MapaMovilGPS()' in html_content:
                print("   ✅ Inicialización de MapaMovilGPS encontrada")
            else:
                print("   ❌ Inicialización de MapaMovilGPS NO encontrada")
            
            # Verificar DOMContentLoaded
            if 'DOMContentLoaded' in html_content:
                print("   ✅ Event listener DOMContentLoaded encontrado")
            else:
                print("   ❌ Event listener DOMContentLoaded NO encontrado")
            
            # 6. Verificar estructura HTML básica
            print("\n6. Verificando estructura HTML...")
            
            if '<html' in html_content:
                print("   ✅ Estructura HTML válida")
            else:
                print("   ❌ Estructura HTML inválida")
            
            if 'Mapa de Solicitudes' in html_content:
                print("   ✅ Título del mapa encontrado")
            else:
                print("   ❌ Título del mapa NO encontrado")
            
            # 7. Buscar posibles errores en el HTML
            print("\n7. Buscando posibles problemas...")
            
            if 'error' in html_content.lower():
                print("   ⚠️  Palabra 'error' encontrada en el HTML")
            
            if 'undefined' in html_content.lower():
                print("   ⚠️  Palabra 'undefined' encontrada en el HTML")
            
            if 'null' in html_content.lower():
                print("   ⚠️  Palabra 'null' encontrada en el HTML")
            
            # 8. Verificar tamaño del HTML
            html_size = len(html_content)
            print(f"\n8. Tamaño del HTML: {html_size} caracteres")
            
            if html_size < 1000:
                print("   ⚠️  HTML muy pequeño, posible problema")
            elif html_size > 50000:
                print("   ⚠️  HTML muy grande, posible problema")
            else:
                print("   ✅ Tamaño del HTML normal")
            
            # 9. Guardar HTML para inspección manual
            print("\n9. Guardando HTML para inspección...")
            with open('debug_mapa_output.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            print("   ✅ HTML guardado en 'debug_mapa_output.html'")
            
            print("\n=== FIN DE LA PRUEBA ===")

if __name__ == '__main__':
    test_mapa_debug()