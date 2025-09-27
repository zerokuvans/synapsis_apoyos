#!/usr/bin/env python3
"""
Script para hacer login y obtener el HTML del mapa para debug
"""

import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import re

def test_mapa_html():
    """Hacer login y analizar el HTML del mapa"""
    base_url = "http://localhost:5000"
    session = requests.Session()
    
    print("=== ANÁLISIS DEL MAPA HTML ===\n")
    
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
    
    if login_response.status_code != 302:
        print("   ❌ Login falló")
        return
    
    print("   ✅ Login exitoso")
    
    # 2. Obtener HTML del mapa
    print("\n2. Obteniendo HTML del mapa...")
    mapa_response = session.get(urljoin(base_url, '/tecnico/mapa'))
    
    if mapa_response.status_code != 200:
        print("   ❌ No se pudo obtener el mapa")
        return
    
    print("   ✅ HTML del mapa obtenido")
    
    # 3. Analizar el HTML
    soup = BeautifulSoup(mapa_response.text, 'html.parser')
    
    # Verificar div del mapa
    mapa_div = soup.find('div', {'id': 'mapa'})
    if mapa_div:
        print("   ✅ Div #mapa encontrado")
        print(f"   Estilo: {mapa_div.get('style', 'No style')}")
    else:
        print("   ❌ Div #mapa NO encontrado")
    
    # Verificar Leaflet CSS
    leaflet_css = soup.find('link', href=re.compile(r'leaflet.*\.css'))
    if leaflet_css:
        print("   ✅ Leaflet CSS encontrado")
        print(f"   URL: {leaflet_css.get('href')}")
    else:
        print("   ❌ Leaflet CSS NO encontrado")
    
    # Verificar Leaflet JS
    leaflet_js = soup.find('script', src=re.compile(r'leaflet.*\.js'))
    if leaflet_js:
        print("   ✅ Leaflet JS encontrado")
        print(f"   URL: {leaflet_js.get('src')}")
    else:
        print("   ❌ Leaflet JS NO encontrado")
    
    # Verificar clase MapaTecnico
    html_content = mapa_response.text
    if 'class MapaTecnico' in html_content:
        print("   ✅ Clase MapaTecnico encontrada")
    else:
        print("   ❌ Clase MapaTecnico NO encontrada")
    
    # Verificar inicialización
    if 'mapaTecnico = new MapaTecnico()' in html_content:
        print("   ✅ Inicialización de MapaTecnico encontrada")
    else:
        print("   ❌ Inicialización de MapaTecnico NO encontrada")
    
    # Verificar verificación de Leaflet
    if 'typeof L !== \'undefined\'' in html_content:
        print("   ✅ Verificación de Leaflet encontrada")
    else:
        print("   ❌ Verificación de Leaflet NO encontrada")
    
    # 4. Verificar recursos externos
    print("\n3. Verificando recursos externos...")
    
    # Verificar Leaflet CSS
    try:
        css_response = requests.get('https://unpkg.com/leaflet@1.9.4/dist/leaflet.css', timeout=5)
        if css_response.status_code == 200:
            print("   ✅ Leaflet CSS accesible")
        else:
            print(f"   ❌ Leaflet CSS no accesible (status: {css_response.status_code})")
    except Exception as e:
        print(f"   ❌ Error accediendo Leaflet CSS: {e}")
    
    # Verificar Leaflet JS
    try:
        js_response = requests.get('https://unpkg.com/leaflet@1.9.4/dist/leaflet.js', timeout=5)
        if js_response.status_code == 200:
            print("   ✅ Leaflet JS accesible")
        else:
            print(f"   ❌ Leaflet JS no accesible (status: {js_response.status_code})")
    except Exception as e:
        print(f"   ❌ Error accediendo Leaflet JS: {e}")
    
    # 5. Buscar posibles errores en el HTML
    print("\n4. Buscando posibles problemas...")
    
    # Verificar si hay errores de sintaxis JavaScript
    script_tags = soup.find_all('script')
    for i, script in enumerate(script_tags):
        if script.string and 'MapaTecnico' in script.string:
            print(f"   📄 Script #{i+1} con MapaTecnico encontrado")
            # Buscar posibles errores comunes
            script_content = script.string
            if 'console.error' in script_content:
                print("   ⚠️  Script contiene console.error")
            if 'throw' in script_content:
                print("   ⚠️  Script contiene throw")
    
    # Verificar elementos requeridos
    required_elements = ['miUbicacion', 'contadorMoviles', 'ultimaActualizacion', 'listaMoviles']
    for element_id in required_elements:
        element = soup.find(id=element_id)
        if element:
            print(f"   ✅ Elemento #{element_id} encontrado")
        else:
            print(f"   ❌ Elemento #{element_id} NO encontrado")
    
    print("\n=== FIN DEL ANÁLISIS ===")

if __name__ == '__main__':
    test_mapa_html()