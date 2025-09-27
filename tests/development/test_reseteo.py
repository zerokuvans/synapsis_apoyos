import requests
from urllib.parse import urljoin

def test_reseteo():
    session = requests.Session()
    base_url = 'http://localhost:5000'
    
    login_data = {'email': 'lider1@synapsis.com', 'password': 'lider123'}
    login_response = session.post(urljoin(base_url, '/auth/login'), data=login_data, allow_redirects=False)
    
    if login_response.status_code == 302:
        print('=== PRUEBA DE RESETEO DE FILTROS ===')
        
        # Aplicar filtros
        print('\n1. Aplicando filtros:')
        resp = session.get(urljoin(base_url, '/lider/usuarios'), params={'rol': 'tecnico', 'buscar': 'tecnico1'})
        print(f'   Status: {resp.status_code}')
        print(f'   URL con filtros: {resp.url}')
        
        # Resetear filtros (ir a la página sin parámetros)
        print('\n2. Reseteando filtros:')
        resp2 = session.get(urljoin(base_url, '/lider/usuarios'))
        print(f'   Status: {resp2.status_code}')
        print(f'   URL sin filtros: {resp2.url}')
        shows_all = 'No se encontraron usuarios' not in resp2.text
        print(f'   Muestra todos los usuarios: {shows_all}')
        
    else:
        print('Login falló')
        print(f'Status code: {login_response.status_code}')

if __name__ == '__main__':
    test_reseteo()