#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para descargar dataset completo de LabUrbano con coordenadas de polígonos
de las 20 localidades de Bogotá desde la API oficial.

Este script descarga los datos geométricos precisos incluyendo:
- Coordenadas completas de polígonos territoriales
- Información administrativa de cada localidad
- Geometrías en formato GeoJSON
"""

import requests
import json
import os
from datetime import datetime

def download_laburbano_polygons():
    """
    Descarga el dataset completo de polígonos de localidades desde LabUrbano
    """
    print("🌍 Iniciando descarga del dataset LabUrbano - Polígonos de Localidades")
    
    # URL de la API de LabUrbano para polígonos de localidades
    base_url = "https://bogota-laburbano.opendatasoft.com/api/explore/v2.1/catalog/datasets/poligonos-localidades/records"
    
    # Parámetros para obtener todas las localidades (20 en total)
    params = {
        'limit': 20,  # Todas las localidades de Bogotá
        'offset': 0,
        'timezone': 'UTC'
    }
    
    try:
        print(f"📡 Conectando a: {base_url}")
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ Descarga exitosa. Total de localidades: {data.get('total_count', 0)}")
        
        # Procesar y validar datos
        localidades_procesadas = []
        
        for record in data.get('results', []):
            localidad = {
                'nombre': record.get('Nombre de la localidad', '').strip(),
                'codigo': record.get('Identificador unico de la localidad', '').strip(),
                'acto_administrativo': record.get('Acto administrativo de la localidad', '').strip(),
                'area': record.get('Area de la localidad', '0').replace(',', '.'),
                'geometry': record.get('geometry', {})
            }
            
            # Validar que tenga geometría
            if localidad['geometry'] and 'geometry' in localidad['geometry']:
                coordinates = localidad['geometry']['geometry'].get('coordinates', [])
                if coordinates:
                    print(f"📍 Procesada: {localidad['nombre']} (Código: {localidad['codigo']})")
                    print(f"   📐 Coordenadas: {len(coordinates[0][0]) if coordinates and coordinates[0] else 0} puntos")
                    localidades_procesadas.append(localidad)
                else:
                    print(f"⚠️  Sin coordenadas: {localidad['nombre']}")
            else:
                print(f"❌ Sin geometría: {localidad['nombre']}")
        
        # Guardar datos procesados
        output_file = 'localidades_polygons_laburbano.json'
        output_data = {
            'metadata': {
                'source': 'LabUrbano Bogotá',
                'url': base_url,
                'download_date': datetime.now().isoformat(),
                'total_localidades': len(localidades_procesadas),
                'description': 'Polígonos territoriales de localidades de Bogotá con coordenadas precisas'
            },
            'localidades': localidades_procesadas
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Datos guardados en: {output_file}")
        print(f"📊 Estadísticas:")
        print(f"   • Total localidades procesadas: {len(localidades_procesadas)}")
        print(f"   • Archivo generado: {os.path.getsize(output_file) / 1024:.1f} KB")
        
        # Mostrar resumen de localidades
        print(f"\n📋 Localidades descargadas:")
        for i, loc in enumerate(localidades_procesadas, 1):
            coords_count = 0
            if loc['geometry'] and 'geometry' in loc['geometry']:
                coordinates = loc['geometry']['geometry'].get('coordinates', [])
                if coordinates and coordinates[0]:
                    coords_count = len(coordinates[0][0])
            
            print(f"   {i:2d}. {loc['nombre']} (Código: {loc['codigo']}) - {coords_count} puntos")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Error al procesar JSON: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def validate_polygon_data(file_path='localidades_polygons_laburbano.json'):
    """
    Valida la integridad de los datos de polígonos descargados
    """
    print(f"\n🔍 Validando datos de polígonos en: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        localidades = data.get('localidades', [])
        print(f"📊 Validación de {len(localidades)} localidades:")
        
        valid_count = 0
        for loc in localidades:
            nombre = loc.get('nombre', 'Sin nombre')
            geometry = loc.get('geometry', {})
            
            if geometry and 'geometry' in geometry:
                coordinates = geometry['geometry'].get('coordinates', [])
                if coordinates and len(coordinates) > 0 and len(coordinates[0]) > 0:
                    points_count = len(coordinates[0][0])
                    if points_count >= 3:  # Mínimo para un polígono
                        valid_count += 1
                        print(f"   ✅ {nombre}: {points_count} puntos")
                    else:
                        print(f"   ⚠️  {nombre}: Insuficientes puntos ({points_count})")
                else:
                    print(f"   ❌ {nombre}: Sin coordenadas válidas")
            else:
                print(f"   ❌ {nombre}: Sin geometría")
        
        print(f"\n📈 Resumen de validación:")
        print(f"   • Localidades válidas: {valid_count}/{len(localidades)}")
        print(f"   • Porcentaje de éxito: {(valid_count/len(localidades)*100):.1f}%")
        
        return valid_count == len(localidades)
        
    except FileNotFoundError:
        print(f"❌ Archivo no encontrado: {file_path}")
        return False
    except Exception as e:
        print(f"❌ Error en validación: {e}")
        return False

if __name__ == "__main__":
    print("🚀 LabUrbano Polygon Downloader - Synapsis Apoyos")
    print("=" * 50)
    
    # Descargar datos
    if download_laburbano_polygons():
        print("\n" + "=" * 50)
        # Validar datos descargados
        if validate_polygon_data():
            print("\n🎉 ¡Descarga y validación completadas exitosamente!")
            print("📁 Los datos están listos para integración en la base de datos.")
        else:
            print("\n⚠️  Descarga completada pero con problemas de validación.")
    else:
        print("\n❌ Error en la descarga. Verifique la conexión e intente nuevamente.")