import requests
import json

def test_api_real():
    """Probar la API real del servidor"""
    print("=== PROBANDO API REAL DE MÓVILES ASIGNADAS ===")
    
    # URL del servidor
    base_url = "http://localhost:5000"
    
    # Primero hacer login usando la API
    login_url = f"{base_url}/auth/api/login"
    login_data = {
        'email': 'tecnico1@synapsis.com',
        'password': 'tecnico123'
    }
    
    session = requests.Session()
    
    try:
        # Login
        print("🔐 Intentando login...")
        login_response = session.post(login_url, json=login_data, headers={'Content-Type': 'application/json'})
        
        if login_response.status_code == 200:
            print("✅ Login exitoso")
        else:
            print(f"❌ Error en login: {login_response.status_code}")
            print(f"Respuesta: {login_response.text[:200]}")
            return
        
        # Probar API de móviles asignadas
        api_url = f"{base_url}/tecnico/api/moviles-asignadas"
        params = {
            'lat': 4.6097,
            'lng': -74.0817
        }
        
        print(f"\n📡 Llamando a API: {api_url}")
        print(f"📍 Parámetros: {params}")
        
        api_response = session.get(api_url, params=params)
        
        print(f"\n📊 Status Code: {api_response.status_code}")
        print(f"📊 Headers: {dict(api_response.headers)}")
        
        if api_response.status_code == 200:
            try:
                data = api_response.json()
                print(f"\n✅ API ejecutada exitosamente")
                print(f"📊 Datos recibidos:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                
                moviles_asignadas = data.get('moviles_asignadas', [])
                total = data.get('total', 0)
                
                print(f"\n📱 Total móviles asignadas: {total}")
                
                if moviles_asignadas:
                    for i, movil in enumerate(moviles_asignadas, 1):
                        print(f"\n🚗 Móvil {i}:")
                        print(f"   Nombre: {movil.get('nombre', 'N/A')}")
                        print(f"   Estado: {movil.get('estado_texto', 'N/A')} ({movil.get('estado', 'N/A')})")
                        print(f"   Distancia: {movil.get('distancia_km', 'N/A')} km")
                        print(f"   Tiempo estimado: {movil.get('tiempo_estimado_min', 'N/A')} min")
                        print(f"   Tipo apoyo: {movil.get('tipo_apoyo', 'N/A')}")
                        print(f"   Teléfono: {movil.get('telefono', 'N/A')}")
                        coordenadas = movil.get('coordenadas', {})
                        if coordenadas:
                            print(f"   📍 Coordenadas: {coordenadas.get('lat', 'N/A')}, {coordenadas.get('lng', 'N/A')}")
                        print(f"   🕒 Aceptado: {movil.get('aceptado_at', 'N/A')}")
                        if movil.get('observaciones'):
                            print(f"   📝 Observaciones: {movil.get('observaciones')}")
                else:
                    print("\n❌ No se encontraron móviles asignadas")
                    print("\n🔍 Esto significa que:")
                    print("   ✅ La API funciona correctamente")
                    print("   ✅ El técnico tiene ubicación")
                    print("   ❌ Pero no hay móviles asignadas a servicios activos")
                    print("\n💡 Para que aparezcan móviles:")
                    print("   1. Debe haber una solicitud del técnico")
                    print("   2. Una móvil debe haber aceptado esa solicitud")
                    print("   3. El servicio debe estar en estado 'aceptado', 'en_ruta' o 'en_sitio'")
                    print("   4. La móvil debe tener ubicación actualizada")
                    
            except json.JSONDecodeError as e:
                print(f"❌ Error decodificando JSON: {e}")
                print(f"Respuesta raw: {api_response.text}")
        else:
            print(f"❌ Error en API: {api_response.status_code}")
            print(f"Respuesta: {api_response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Error de conexión. ¿Está el servidor corriendo en localhost:5000?")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_api_real()