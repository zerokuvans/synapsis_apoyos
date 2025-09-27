#!/usr/bin/env python3
"""
Script para descargar el dataset de localidades de Bogotá desde LabUrbano
"""

import requests
import json
import pymysql
import sys
from datetime import datetime

# Configuración de la base de datos
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '732137A031E4b@',
    'charset': 'utf8mb4',
    'database': 'synapsis_apoyos'
}

# URL del dataset de LabUrbano - Polígonos de Localidades
LABURBANO_API_URL = "https://bogota-laburbano.opendatasoft.com/api/records/1.0/search/"
DATASET_ID = "poligonos-localidades"

def crear_conexion():
    """Crea una conexión a MySQL"""
    try:
        connection = pymysql.connect(**DB_CONFIG)
        return connection
    except Exception as e:
        print(f"Error conectando a MySQL: {e}")
        return None

def descargar_datos_laburbano():
    """Descarga los datos de localidades desde LabUrbano"""
    print("📡 Descargando datos de LabUrbano...")
    
    try:
        # Parámetros para la API
        params = {
            'dataset': DATASET_ID,
            'rows': 25,  # Máximo número de registros
            'format': 'json'
        }
        
        # Realizar la petición
        response = requests.get(LABURBANO_API_URL, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if 'records' not in data:
            print("❌ No se encontraron registros en la respuesta")
            return None
        
        print(f"✓ Descargados {len(data['records'])} registros de localidades")
        return data['records']
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error descargando datos: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Error decodificando JSON: {e}")
        return None

def procesar_geometria(geo_shape):
    """Procesa la geometría GeoJSON y extrae coordenadas del centroide"""
    try:
        if not geo_shape or 'geometry' not in geo_shape:
            return None, None, None
        
        geometry = geo_shape['geometry']
        
        # Calcular centroide aproximado
        if geometry['type'] == 'Polygon' and 'coordinates' in geometry:
            coords = geometry['coordinates'][0]  # Primer anillo del polígono
            if coords:
                # Calcular centroide simple (promedio de coordenadas)
                lats = [coord[1] for coord in coords]
                lons = [coord[0] for coord in coords]
                
                centroide_lat = sum(lats) / len(lats)
                centroide_lon = sum(lons) / len(lons)
                
                return json.dumps(geometry), centroide_lat, centroide_lon
        
        return json.dumps(geometry), None, None
        
    except Exception as e:
        print(f"⚠️  Error procesando geometría: {e}")
        return None, None, None

def actualizar_localidades_con_laburbano(records):
    """Actualiza la tabla localidades con los datos de LabUrbano"""
    connection = crear_conexion()
    if not connection:
        return False
    
    try:
        with connection.cursor() as cursor:
            actualizado = 0
            insertado = 0
            
            for record in records:
                fields = record.get('fields', {})
                
                # Extraer datos del registro
                nombre = fields.get('localidad', '').strip()
                codigo = fields.get('loccodigo', '').strip()
                area = fields.get('shape_area')  # Área en unidades del sistema de coordenadas
                geo_shape = fields.get('geo_shape')
                
                if not nombre or not codigo:
                    print(f"⚠️  Registro incompleto: {fields}")
                    continue
                
                # Procesar geometría
                geometria_json, centroide_lat, centroide_lon = procesar_geometria(geo_shape)
                
                # Verificar si la localidad ya existe
                cursor.execute("SELECT id FROM localidades WHERE codigo = %s", (codigo,))
                existe = cursor.fetchone()
                
                if existe:
                    # Actualizar registro existente
                    cursor.execute("""
                        UPDATE localidades 
                        SET nombre = %s, area = %s, geometria = %s, 
                            latitud_centro = %s, longitud_centro = %s,
                            descripcion = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE codigo = %s
                    """, (
                        nombre,
                        area,
                        geometria_json,
                        centroide_lat,
                        centroide_lon,
                        f"Localidad {nombre} de Bogotá D.C. - Datos de LabUrbano",
                        codigo
                    ))
                    actualizado += 1
                    print(f"✓ Actualizada: {nombre} (código: {codigo})")
                else:
                    # Insertar nuevo registro
                    cursor.execute("""
                        INSERT INTO localidades 
                        (codigo, nombre, area, geometria, latitud_centro, longitud_centro, descripcion)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        codigo,
                        nombre,
                        area,
                        geometria_json,
                        centroide_lat,
                        centroide_lon,
                        f"Localidad {nombre} de Bogotá D.C. - Datos de LabUrbano"
                    ))
                    insertado += 1
                    print(f"✓ Insertada: {nombre} (código: {codigo})")
            
            connection.commit()
            print(f"\n📊 Resumen:")
            print(f"   • Registros insertados: {insertado}")
            print(f"   • Registros actualizados: {actualizado}")
            print(f"   • Total procesados: {insertado + actualizado}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error actualizando localidades: {e}")
        connection.rollback()
        return False
    finally:
        connection.close()

def guardar_datos_json(records, filename="localidades_laburbano.json"):
    """Guarda los datos descargados en un archivo JSON para respaldo"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
        print(f"✓ Datos guardados en {filename}")
        return True
    except Exception as e:
        print(f"❌ Error guardando archivo JSON: {e}")
        return False

def main():
    """Función principal"""
    print("=== Descarga de Dataset LabUrbano - Localidades de Bogotá ===")
    print()
    
    # Descargar datos
    print("1. Descargando datos desde LabUrbano...")
    records = descargar_datos_laburbano()
    
    if not records:
        print("❌ No se pudieron descargar los datos")
        sys.exit(1)
    
    # Guardar respaldo en JSON
    print("\n2. Guardando respaldo en JSON...")
    guardar_datos_json(records)
    
    # Actualizar base de datos
    print("\n3. Actualizando base de datos...")
    if not actualizar_localidades_con_laburbano(records):
        print("❌ Error actualizando base de datos")
        sys.exit(1)
    
    print("\n✅ ¡Integración con LabUrbano completada exitosamente!")
    print("\n📍 Datos actualizados:")
    print("   • Geometrías GeoJSON de localidades")
    print("   • Coordenadas de centroides")
    print("   • Áreas oficiales")
    print("   • Códigos oficiales de localidades")
    print("\n🚀 Listo para usar en APIs y mapas!")

if __name__ == '__main__':
    main()