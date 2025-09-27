#!/usr/bin/env python3
from app import create_app
from app.models.usuario import Usuario

def test_movil_login():
    app = create_app()
    
    with app.test_client() as client:
        # Intentar login con usuario móvil
        login_data = {
            'email': 'movil1@synapsis.com',
            'password': 'movil123'
        }
        
        print("🔐 Intentando login con usuario móvil...")
        response = client.post('/auth/login', data=login_data, follow_redirects=False)
        print(f"Status del login: {response.status_code}")
        
        if response.status_code == 302:
            location = response.headers.get('Location', '')
            print(f"Redirigiendo a: {location}")
            
            # Seguir la redirección
            response = client.get(location, follow_redirects=False)
            print(f"Status después de redirección: {response.status_code}")
            
            # Ahora intentar acceder al mapa
            print("\n🗺️ Intentando acceder al mapa...")
            response = client.get('/movil/mapa', follow_redirects=False)
            print(f"Status del mapa: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Acceso al mapa exitoso")
                html_content = response.data.decode('utf-8')
                
                # Verificar elementos clave
                checks = [
                    ('id="mapa"', 'Div del mapa'),
                    ('leaflet', 'Referencias a Leaflet'),
                    ('MapaMovilGPS', 'Clase MapaMovilGPS'),
                    ('openstreetmap', 'Tiles de OpenStreetMap')
                ]
                
                for check, description in checks:
                    if check.lower() in html_content.lower():
                        print(f"✅ {description} encontrado")
                    else:
                        print(f"❌ {description} NO encontrado")
                        
            elif response.status_code == 302:
                location = response.headers.get('Location', '')
                print(f"❌ Redirigido nuevamente a: {location}")
            else:
                print(f"❌ Error al acceder al mapa: {response.status_code}")
                
        else:
            print(f"❌ Error en login: {response.status_code}")
            print(response.data.decode('utf-8')[:200])

    # Verificar usuario en base de datos
    print("\n👤 Verificando usuario en base de datos...")
    with app.app_context():
        usuario = Usuario.query.filter_by(email='movil1@synapsis.com').first()
        if usuario:
            print(f"Usuario encontrado: {usuario.nombre} {usuario.apellido}")
            print(f"Rol: {usuario.rol}")
            print(f"Activo: {usuario.activo}")
            print(f"Password válido: {usuario.check_password('movil123')}")
        else:
            print("❌ Usuario no encontrado en base de datos")

if __name__ == '__main__':
    test_movil_login()