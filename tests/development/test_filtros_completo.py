import requests
from urllib.parse import urljoin

def test_filtros():
    # Crear sesión y hacer login
    session = requests.Session()
    base_url = 'http://localhost:5000'
    
    login_data = {'email': 'lider1@synapsis.com', 'password': 'lider123'}
    login_response = session.post(urljoin(base_url, '/auth/login'), data=login_data, allow_redirects=False)
    
    if login_response.status_code == 302:
        print('=== PRUEBAS DE FILTROS ===')
        
        # Filtro por rol técnico
        print('\n1. Filtro por rol técnico:')
        resp = session.get(urljoin(base_url, '/lider/usuarios'), params={'rol': 'tecnico'})
        print(f'   Status: {resp.status_code}')
        tecnico_found = 'Técnico' in resp.text or 'tecnico' in resp.text
        print(f'   Contiene técnicos: {tecnico_found}')
        
        # Filtro por estado activo
        print('\n2. Filtro por estado activo:')
        resp = session.get(urljoin(base_url, '/lider/usuarios'), params={'estado': 'activo'})
        print(f'   Status: {resp.status_code}')
        no_users_msg = 'No se encontraron usuarios' not in resp.text
        print(f'   Contiene usuarios: {no_users_msg}')
        
        # Filtro por email
        print('\n3. Filtro por email (tecnico1):')
        resp = session.get(urljoin(base_url, '/lider/usuarios'), params={'buscar': 'tecnico1'})
        print(f'   Status: {resp.status_code}')
        tecnico1_found = 'tecnico1' in resp.text
        print(f'   Contiene tecnico1: {tecnico1_found}')
        
        # Filtros combinados
        print('\n4. Filtros combinados (rol=tecnico, buscar=1):')
        resp = session.get(urljoin(base_url, '/lider/usuarios'), params={'rol': 'tecnico', 'buscar': '1'})
        print(f'   Status: {resp.status_code}')
        has_results = 'No se encontraron usuarios' not in resp.text
        print(f'   Contiene resultados: {has_results}')
        
        # Filtro sin resultados
        print('\n5. Filtro sin resultados (buscar=xyz123):')
        resp = session.get(urljoin(base_url, '/lider/usuarios'), params={'buscar': 'xyz123'})
        print(f'   Status: {resp.status_code}')
        no_results = 'No se encontraron usuarios' in resp.text
        print(f'   Muestra mensaje sin resultados: {no_results}')
        
    else:
        print('Login falló')
        print(f'Status code: {login_response.status_code}')

if __name__ == '__main__':
    test_filtros()