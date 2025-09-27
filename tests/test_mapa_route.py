#!/usr/bin/env python3
from app import create_app

def test_mapa_route():
    app = create_app()
    
    # Test de la ruta del mapa
    with app.test_client() as client:
        # Intentar acceder sin autenticación
        response = client.get('/movil/mapa')
        print(f'Sin autenticación - Status: {response.status_code}')
        
        # Simular login de móvil
        with client.session_transaction() as sess:
            sess['_user_id'] = '1'  # ID de María González
            sess['_fresh'] = True
        
        response = client.get('/movil/mapa')
        print(f'Con sesión simulada - Status: {response.status_code}')
        
        if response.status_code == 200:
            print('✅ Ruta del mapa accesible')
            
            # Verificar si contiene el div del mapa
            html_content = response.data.decode('utf-8')
            if 'id="mapa"' in html_content:
                print('✅ Div del mapa encontrado en el HTML')
            else:
                print('❌ Div del mapa NO encontrado')
                
            # Verificar si contiene Leaflet
            if 'leaflet' in html_content.lower():
                print('✅ Referencias a Leaflet encontradas')
            else:
                print('❌ Referencias a Leaflet NO encontradas')
                
            # Verificar si contiene MapaMovilGPS
            if 'MapaMovilGPS' in html_content:
                print('✅ Clase MapaMovilGPS encontrada')
            else:
                print('❌ Clase MapaMovilGPS NO encontrada')
                
        else:
            print(f'❌ Error al acceder: {response.status_code}')
            print(f'Respuesta: {response.data.decode("utf-8")[:200]}...')

if __name__ == '__main__':
    test_mapa_route()