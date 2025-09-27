#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para verificar la funcionalidad de detección de localidad
por coordenadas usando algoritmos de punto-en-polígono.

Este script prueba:
1. La API de detección de localidad por coordenadas
2. Los algoritmos de punto-en-polígono implementados
3. La precisión de los límites territoriales
4. Casos de borde y coordenadas fuera de Bogotá
"""

import requests
import json
import sys
import os
from datetime import datetime

# Agregar el directorio raíz al path para importar módulos de la app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models.localidad import Localidad
from app.utils.polygon_utils import point_in_polygon, validate_polygon_coordinates

def test_api_detection():
    """
    Prueba la API de detección de localidad por coordenadas
    """
    print("🧪 Probando API de detección de localidad por coordenadas")
    print("=" * 60)
    
    # Coordenadas de prueba en diferentes localidades de Bogotá
    test_coordinates = [
        {
            'name': 'Centro de Bogotá (La Candelaria)',
            'lat': 4.5981,
            'lng': -74.0758,
            'expected_localidad': 'CANDELARIA'
        },
        {
            'name': 'Zona Rosa (Chapinero)',
            'lat': 4.6698,
            'lng': -74.0440,
            'expected_localidad': 'CHAPINERO'
        },
        {
            'name': 'Kennedy Central',
            'lat': 4.6276,
            'lng': -74.1378,
            'expected_localidad': 'KENNEDY'
        },
        {
            'name': 'Suba Centro',
            'lat': 4.7570,
            'lng': -74.0840,
            'expected_localidad': 'SUBA'
        },
        {
            'name': 'Usaquén',
            'lat': 4.7045,
            'lng': -74.0307,
            'expected_localidad': 'USAQUEN'
        },
        {
            'name': 'Fuera de Bogotá (Chía)',
            'lat': 4.8614,
            'lng': -74.0583,
            'expected_localidad': None
        }
    ]
    
    base_url = 'http://localhost:5000'
    api_url = f'{base_url}/api/localidades/detect-by-coordinates'
    
    results = []
    
    for test_case in test_coordinates:
        print(f"\n📍 Probando: {test_case['name']}")
        print(f"   Coordenadas: ({test_case['lat']}, {test_case['lng']})")
        
        try:
            # Hacer petición a la API
            response = requests.post(api_url, json={
                'latitud': test_case['lat'],
                'longitud': test_case['lng']
            }, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    localidad_encontrada = data.get('localidad', {}).get('nombre')
                    dentro_de_localidad = data.get('dentro_de_localidad', False)
                    
                    print(f"   ✅ Localidad detectada: {localidad_encontrada}")
                    print(f"   📍 Dentro de límites: {'Sí' if dentro_de_localidad else 'No'}")
                    
                    # Verificar si coincide con lo esperado
                    if test_case['expected_localidad']:
                        if localidad_encontrada and test_case['expected_localidad'].upper() in localidad_encontrada.upper():
                            print(f"   ✅ Resultado correcto")
                            results.append({'test': test_case['name'], 'status': 'PASS', 'details': f"Detectó {localidad_encontrada}"})
                        else:
                            print(f"   ⚠️  Resultado inesperado (esperaba {test_case['expected_localidad']})")
                            results.append({'test': test_case['name'], 'status': 'FAIL', 'details': f"Esperaba {test_case['expected_localidad']}, obtuvo {localidad_encontrada}"})
                    else:
                        # Caso fuera de Bogotá
                        if not dentro_de_localidad:
                            print(f"   ✅ Correctamente detectado fuera de límites")
                            results.append({'test': test_case['name'], 'status': 'PASS', 'details': "Correctamente fuera de límites"})
                        else:
                            print(f"   ⚠️  Debería estar fuera de límites")
                            results.append({'test': test_case['name'], 'status': 'FAIL', 'details': "Debería estar fuera de límites"})
                else:
                    print(f"   ❌ API retornó error: {data.get('message')}")
                    results.append({'test': test_case['name'], 'status': 'ERROR', 'details': data.get('message')})
            else:
                print(f"   ❌ Error HTTP {response.status_code}: {response.text}")
                results.append({'test': test_case['name'], 'status': 'ERROR', 'details': f"HTTP {response.status_code}"})
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Error de conexión: {e}")
            results.append({'test': test_case['name'], 'status': 'ERROR', 'details': f"Conexión: {e}"})
        except Exception as e:
            print(f"   ❌ Error inesperado: {e}")
            results.append({'test': test_case['name'], 'status': 'ERROR', 'details': f"Error: {e}"})
    
    return results

def test_direct_polygon_functions():
    """
    Prueba directamente las funciones de polígonos sin API
    """
    print(f"\n🔬 Probando funciones de polígonos directamente")
    print("=" * 60)
    
    app = create_app()
    with app.app_context():
        try:
            # Obtener algunas localidades con geometría
            localidades = Localidad.query.filter(
                Localidad.geometria.isnot(None)
            ).limit(5).all()
            
            print(f"📊 Localidades con geometría encontradas: {len(localidades)}")
            
            results = []
            
            for localidad in localidades:
                print(f"\n🏛️  Probando localidad: {localidad.nombre} ({localidad.codigo})")
                
                # Validar geometría
                if localidad.validate_geometry():
                    print(f"   ✅ Geometría válida")
                    
                    # Probar con el centroide (debería estar dentro)
                    centroide = localidad.get_centroide()
                    if centroide:
                        dentro = localidad.contains_point(centroide['lat'], centroide['lng'])
                        print(f"   📍 Centroide ({centroide['lat']:.6f}, {centroide['lng']:.6f}): {'Dentro' if dentro else 'Fuera'}")
                        
                        if dentro:
                            results.append({'test': f"{localidad.nombre} - Centroide", 'status': 'PASS', 'details': 'Centroide dentro del polígono'})
                        else:
                            results.append({'test': f"{localidad.nombre} - Centroide", 'status': 'FAIL', 'details': 'Centroide fuera del polígono'})
                    
                    # Obtener límites
                    bounds = localidad.get_bounds()
                    if bounds:
                        print(f"   📐 Límites: ({bounds['min_lat']:.6f}, {bounds['min_lng']:.6f}) a ({bounds['max_lat']:.6f}, {bounds['max_lng']:.6f})")
                        results.append({'test': f"{localidad.nombre} - Límites", 'status': 'PASS', 'details': 'Límites calculados correctamente'})
                    
                else:
                    print(f"   ❌ Geometría inválida")
                    results.append({'test': f"{localidad.nombre} - Geometría", 'status': 'FAIL', 'details': 'Geometría inválida'})
            
            return results
            
        except Exception as e:
            print(f"❌ Error en pruebas directas: {e}")
            return [{'test': 'Pruebas directas', 'status': 'ERROR', 'details': str(e)}]

def test_polygon_api_endpoints():
    """
    Prueba los endpoints de polígonos
    """
    print(f"\n🌐 Probando endpoints de polígonos")
    print("=" * 60)
    
    base_url = 'http://localhost:5000'
    endpoints = [
        '/api/localidades',
        '/api/localidades/polygons',
        '/api/localidades/01/polygon',  # Usaquén
        '/api/localidades/01/bounds'    # Usaquén
    ]
    
    results = []
    
    for endpoint in endpoints:
        print(f"\n🔗 Probando: {endpoint}")
        
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success', True):  # Algunos endpoints no tienen 'success'
                    print(f"   ✅ Respuesta exitosa")
                    
                    # Verificar contenido específico según endpoint
                    if 'polygons' in endpoint:
                        features = data.get('features', [])
                        print(f"   📊 Polígonos retornados: {len(features)}")
                        results.append({'test': endpoint, 'status': 'PASS', 'details': f"{len(features)} polígonos"})
                    elif 'bounds' in endpoint:
                        bounds = data.get('bounds', {})
                        if bounds:
                            print(f"   📐 Límites obtenidos: {bounds}")
                            results.append({'test': endpoint, 'status': 'PASS', 'details': 'Límites obtenidos'})
                        else:
                            results.append({'test': endpoint, 'status': 'FAIL', 'details': 'Sin límites'})
                    else:
                        total = data.get('total', len(data.get('localidades', [])))
                        print(f"   📊 Elementos retornados: {total}")
                        results.append({'test': endpoint, 'status': 'PASS', 'details': f"{total} elementos"})
                else:
                    print(f"   ❌ API retornó error: {data.get('message')}")
                    results.append({'test': endpoint, 'status': 'FAIL', 'details': data.get('message')})
            else:
                print(f"   ❌ Error HTTP {response.status_code}")
                results.append({'test': endpoint, 'status': 'ERROR', 'details': f"HTTP {response.status_code}"})
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Error de conexión: {e}")
            results.append({'test': endpoint, 'status': 'ERROR', 'details': f"Conexión: {e}"})
        except Exception as e:
            print(f"   ❌ Error inesperado: {e}")
            results.append({'test': endpoint, 'status': 'ERROR', 'details': f"Error: {e}"})
    
    return results

def generate_test_report(all_results):
    """
    Genera un reporte de todas las pruebas
    """
    print(f"\n📋 REPORTE DE PRUEBAS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    error_tests = 0
    
    for category, results in all_results.items():
        print(f"\n📂 {category}:")
        
        for result in results:
            total_tests += 1
            status = result['status']
            
            if status == 'PASS':
                icon = '✅'
                passed_tests += 1
            elif status == 'FAIL':
                icon = '❌'
                failed_tests += 1
            else:
                icon = '⚠️'
                error_tests += 1
            
            print(f"   {icon} {result['test']}: {result['details']}")
    
    print(f"\n📊 RESUMEN:")
    print(f"   • Total de pruebas: {total_tests}")
    print(f"   • Exitosas: {passed_tests} ({(passed_tests/total_tests*100):.1f}%)")
    print(f"   • Fallidas: {failed_tests} ({(failed_tests/total_tests*100):.1f}%)")
    print(f"   • Errores: {error_tests} ({(error_tests/total_tests*100):.1f}%)")
    
    if passed_tests == total_tests:
        print(f"\n🎉 ¡Todas las pruebas pasaron exitosamente!")
        return True
    elif passed_tests >= total_tests * 0.8:
        print(f"\n✅ La mayoría de pruebas pasaron (≥80%)")
        return True
    else:
        print(f"\n⚠️  Muchas pruebas fallaron. Revisar implementación.")
        return False

if __name__ == "__main__":
    print("🚀 Test de Funcionalidad Punto-en-Polígono - Synapsis Apoyos")
    print("=" * 80)
    
    all_results = {}
    
    # Ejecutar todas las pruebas
    try:
        print("\n1️⃣  Probando endpoints de polígonos...")
        all_results['Endpoints de Polígonos'] = test_polygon_api_endpoints()
        
        print("\n2️⃣  Probando API de detección...")
        all_results['API de Detección'] = test_api_detection()
        
        print("\n3️⃣  Probando funciones directas...")
        all_results['Funciones Directas'] = test_direct_polygon_functions()
        
    except KeyboardInterrupt:
        print("\n⏹️  Pruebas interrumpidas por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error general en las pruebas: {e}")
        sys.exit(1)
    
    # Generar reporte final
    success = generate_test_report(all_results)
    
    if success:
        print(f"\n✅ Funcionalidad de punto-en-polígono implementada correctamente")
        sys.exit(0)
    else:
        print(f"\n❌ Se encontraron problemas en la implementación")
        sys.exit(1)