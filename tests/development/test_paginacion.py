import requests
from urllib.parse import urljoin

def test_paginacion():
    session = requests.Session()
    base_url = 'http://localhost:5000'
    
    login_data = {'email': 'lider1@synapsis.com', 'password': 'lider123'}
    login_response = session.post(urljoin(base_url, '/auth/login'), data=login_data, allow_redirects=False)
    
    if login_response.status_code == 302:
        print('=== PRUEBA DE PAGINACIÓN CON FILTROS ===')
        
        # Página 1 con filtro
        print('\n1. Página 1 con filtro buscar=tecnico:')
        resp = session.get(urljoin(base_url, '/lider/usuarios'), params={'buscar': 'tecnico', 'page': 1})
        print(f'   Status: {resp.status_code}')
        no_users_found = 'No se encontraron usuarios' not in resp.text
        print(f'   Contiene resultados: {no_users_found}')
        has_pagination = 'pagination' in resp.text or 'page' in resp.text
        print(f'   Contiene paginación: {has_pagination}')
        
        # Verificar que mantiene filtros en paginación
        print('\n2. Verificando que los filtros se mantienen en la URL:')
        print(f'   URL final: {resp.url}')
        maintains_filter = 'buscar=tecnico' in resp.url
        print(f'   Mantiene parámetro buscar: {maintains_filter}')
        
        # Probar página sin filtros
        print('\n3. Página sin filtros:')
        resp2 = session.get(urljoin(base_url, '/lider/usuarios'), params={'page': 1})
        print(f'   Status: {resp2.status_code}')
        has_users = 'No se encontraron usuarios' not in resp2.text
        print(f'   Contiene usuarios: {has_users}')
        
    else:
        print('Login falló')
        print(f'Status code: {login_response.status_code}')

if __name__ == '__main__':
    test_paginacion()