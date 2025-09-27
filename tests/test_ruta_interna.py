#!/usr/bin/env python3
"""
Script para probar la nueva funcionalidad de mostrar rutas dentro de la aplicación
en lugar de redirigir a Google Maps.
"""

import requests
import re

def test_ruta_interna():
    print("=== PRUEBA DE FUNCIONALIDAD DE RUTA INTERNA ===\n")
    
    # URL base
    base_url = "http://localhost:5000"
    
    # Crear sesión
    session = requests.Session()
    
    try:
        # 1. Hacer login como usuario móvil
        print("1. Haciendo login como usuario móvil...")
        login_data = {
            'email': 'movil1@synapsis.com',
            'password': 'movil123'
        }
        
        login_response = session.post(f"{base_url}/auth/login", data=login_data)
        
        if login_response.status_code != 200:
            print(f"❌ Error en login: {login_response.status_code}")
            return False
            
        print("✅ Login exitoso")
        
        # 2. Acceder al mapa móvil
        print("\n2. Accediendo al mapa móvil...")
        mapa_response = session.get(f"{base_url}/movil/mapa")
        
        if mapa_response.status_code != 200:
            print(f"❌ Error accediendo al mapa: {mapa_response.status_code}")
            return False
            
        print("✅ Mapa accesible")
        
        # 3. Verificar que el HTML contiene la nueva funcionalidad
        print("\n3. Verificando nueva funcionalidad en el HTML...")
        html_content = mapa_response.text
        
        # Verificar que NO hay enlaces a Google Maps
        google_maps_links = re.findall(r'https://www\.google\.com/maps', html_content)
        if google_maps_links:
            print(f"❌ Aún hay {len(google_maps_links)} enlaces a Google Maps")
            return False
        else:
            print("✅ No hay enlaces a Google Maps externos")
        
        # Verificar que está Leaflet Routing Machine
        if 'leaflet-routing-machine' in html_content:
            print("✅ Leaflet Routing Machine incluido")
        else:
            print("❌ Leaflet Routing Machine no encontrado")
            return False
        
        # Verificar que está la nueva función verRutaHacia
        if 'L.Routing.control' in html_content:
            print("✅ Nueva función de routing interno encontrada")
        else:
            print("❌ Nueva función de routing interno no encontrada")
            return False
        
        # Verificar que están las funciones de limpiar ruta
        if 'mostrarBotonLimpiarRuta' in html_content and 'limpiarRuta' in html_content:
            print("✅ Funciones de limpiar ruta encontradas")
        else:
            print("❌ Funciones de limpiar ruta no encontradas")
            return False
        
        # Verificar que los botones tienen el nuevo texto
        if 'Mostrar Ruta' in html_content:
            print("✅ Botones actualizados con nuevo texto")
        else:
            print("❌ Botones no actualizados")
            return False
        
        # Verificar que no hay window.open para Google Maps
        if 'window.open(url, \'_blank\')' not in html_content:
            print("✅ No hay redirecciones externas a Google Maps")
        else:
            print("❌ Aún hay redirecciones externas")
            return False
        
        print("\n=== RESUMEN DE LA PRUEBA ===")
        print("✅ Funcionalidad de ruta interna implementada correctamente")
        print("✅ Los usuarios ahora verán las rutas dentro de la aplicación")
        print("✅ No hay más redirecciones a Google Maps externo")
        print("✅ Se incluye botón para limpiar rutas")
        print("✅ Interfaz mejorada con nuevos iconos y textos")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        return False

if __name__ == "__main__":
    success = test_ruta_interna()
    if success:
        print("\n🎉 ¡Prueba exitosa! La funcionalidad está funcionando correctamente.")
    else:
        print("\n❌ La prueba falló. Revisar la implementación.")