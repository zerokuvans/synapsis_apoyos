#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para migrar datos de polígonos de LabUrbano a la base de datos MySQL

Este script:
1. Lee el archivo JSON con coordenadas de polígonos descargado
2. Actualiza la tabla 'localidades' con las geometrías completas
3. Calcula y actualiza los centroides de cada localidad
4. Valida la integridad de los datos migrados
"""

import json
import sys
import os
from decimal import Decimal
from statistics import mean

# Agregar el directorio raíz al path para importar módulos de la app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.localidad import Localidad

def calculate_polygon_centroid(coordinates):
    """
    Calcula el centroide de un polígono usando las coordenadas
    """
    if not coordinates or not coordinates[0]:
        return None, None
    
    # Tomar el primer anillo del polígono (exterior)
    polygon_coords = coordinates[0][0] if isinstance(coordinates[0][0], list) else coordinates[0]
    
    if len(polygon_coords) < 3:
        return None, None
    
    # Calcular centroide simple (promedio de coordenadas)
    lats = [coord[1] for coord in polygon_coords if len(coord) >= 2]
    lngs = [coord[0] for coord in polygon_coords if len(coord) >= 2]
    
    if not lats or not lngs:
        return None, None
    
    centroid_lat = mean(lats)
    centroid_lng = mean(lngs)
    
    return centroid_lat, centroid_lng

def migrate_polygon_data(json_file='localidades_polygons_laburbano.json'):
    """
    Migra los datos de polígonos desde el archivo JSON a la base de datos
    """
    print("🔄 Iniciando migración de datos de polígonos a MySQL")
    print("=" * 60)
    
    # Verificar que existe el archivo
    if not os.path.exists(json_file):
        print(f"❌ Error: No se encontró el archivo {json_file}")
        print("   Ejecute primero: python download_laburbano_polygons.py")
        return False
    
    try:
        # Cargar datos del archivo JSON
        print(f"📂 Cargando datos desde: {json_file}")
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        localidades_data = data.get('localidades', [])
        print(f"📊 Localidades a procesar: {len(localidades_data)}")
        
        # Crear contexto de aplicación
        app = create_app()
        with app.app_context():
            updated_count = 0
            created_count = 0
            error_count = 0
            
            for loc_data in localidades_data:
                try:
                    nombre = loc_data.get('nombre', '').strip()
                    codigo = loc_data.get('codigo', '').strip()
                    area_str = loc_data.get('area', '0').replace(',', '.')
                    geometry = loc_data.get('geometry', {})
                    
                    # Convertir área de metros cuadrados a hectáreas (dividir por 10,000)
                    area_value = None
                    if area_str and area_str != '0':
                        try:
                            area_m2 = float(area_str)
                            area_hectares = area_m2 / 10000.0  # Convertir a hectáreas
                            area_value = Decimal(str(round(area_hectares, 4)))
                        except (ValueError, TypeError):
                            area_value = None
                    
                    if not nombre or not codigo:
                        print(f"⚠️  Saltando localidad sin nombre o código")
                        error_count += 1
                        continue
                    
                    # Calcular centroide
                    coordinates = geometry.get('geometry', {}).get('coordinates', [])
                    centroid_lat, centroid_lng = calculate_polygon_centroid(coordinates)
                    
                    # Buscar localidad existente
                    localidad = Localidad.query.filter_by(codigo=codigo).first()
                    
                    if localidad:
                        # Actualizar localidad existente
                        print(f"🔄 Actualizando: {nombre} (Código: {codigo})")
                        localidad.nombre = nombre
                        localidad.area = area_value
                        localidad.geometria = geometry
                        
                        if centroid_lat and centroid_lng:
                            localidad.latitud_centro = Decimal(str(centroid_lat))
                            localidad.longitud_centro = Decimal(str(centroid_lng))
                            print(f"   📍 Centroide: ({centroid_lat:.6f}, {centroid_lng:.6f})")
                        
                        updated_count += 1
                    else:
                        # Crear nueva localidad
                        print(f"➕ Creando: {nombre} (Código: {codigo})")
                        localidad = Localidad(
                            nombre=nombre,
                            codigo=codigo,
                            area=area_value,
                            geometria=geometry,
                            latitud_centro=Decimal(str(centroid_lat)) if centroid_lat else None,
                            longitud_centro=Decimal(str(centroid_lng)) if centroid_lng else None,
                            activa=True
                        )
                        
                        db.session.add(localidad)
                        
                        if centroid_lat and centroid_lng:
                            print(f"   📍 Centroide: ({centroid_lat:.6f}, {centroid_lng:.6f})")
                        
                        created_count += 1
                    
                    # Mostrar información de coordenadas
                    if coordinates:
                        points_count = len(coordinates[0][0]) if coordinates and coordinates[0] else 0
                        print(f"   📐 Polígono: {points_count} puntos")
                    
                except Exception as e:
                    print(f"❌ Error procesando {nombre}: {e}")
                    error_count += 1
                    continue
            
            # Confirmar cambios
            try:
                db.session.commit()
                print(f"\n✅ Migración completada exitosamente")
                print(f"📊 Estadísticas:")
                print(f"   • Localidades actualizadas: {updated_count}")
                print(f"   • Localidades creadas: {created_count}")
                print(f"   • Errores: {error_count}")
                print(f"   • Total procesadas: {updated_count + created_count}")
                
                return True
                
            except Exception as e:
                db.session.rollback()
                print(f"❌ Error al confirmar cambios: {e}")
                return False
    
    except Exception as e:
        print(f"❌ Error general en migración: {e}")
        return False

def validate_migration():
    """
    Valida que la migración se haya realizado correctamente
    """
    print(f"\n🔍 Validando migración de datos...")
    
    app = create_app()
    with app.app_context():
        try:
            # Contar localidades con geometría
            total_localidades = Localidad.query.count()
            con_geometria = Localidad.query.filter(Localidad.geometria.isnot(None)).count()
            con_centroide = Localidad.query.filter(
                Localidad.latitud_centro.isnot(None),
                Localidad.longitud_centro.isnot(None)
            ).count()
            
            print(f"📊 Resultados de validación:")
            print(f"   • Total localidades: {total_localidades}")
            print(f"   • Con geometría: {con_geometria}")
            print(f"   • Con centroide: {con_centroide}")
            print(f"   • Porcentaje con geometría: {(con_geometria/total_localidades*100):.1f}%")
            
            # Mostrar algunas localidades como ejemplo
            print(f"\n📋 Muestra de localidades migradas:")
            localidades = Localidad.query.filter(
                Localidad.geometria.isnot(None)
            ).limit(5).all()
            
            for loc in localidades:
                centroide = loc.get_centroide()
                coords_count = 0
                if loc.geometria and 'geometry' in loc.geometria:
                    coordinates = loc.geometria['geometry'].get('coordinates', [])
                    if coordinates and coordinates[0]:
                        coords_count = len(coordinates[0][0]) if isinstance(coordinates[0][0], list) else len(coordinates[0])
                
                print(f"   • {loc.nombre} ({loc.codigo}): {coords_count} puntos")
                if centroide:
                    print(f"     Centroide: ({centroide['lat']:.6f}, {centroide['lng']:.6f})")
            
            return con_geometria == total_localidades
            
        except Exception as e:
            print(f"❌ Error en validación: {e}")
            return False

if __name__ == "__main__":
    print("🚀 Migrador de Polígonos LabUrbano - Synapsis Apoyos")
    print("=" * 60)
    
    # Ejecutar migración
    if migrate_polygon_data():
        # Validar migración
        if validate_migration():
            print("\n🎉 ¡Migración y validación completadas exitosamente!")
            print("📁 Los datos de polígonos están listos en la base de datos.")
        else:
            print("\n⚠️  Migración completada pero con problemas de validación.")
    else:
        print("\n❌ Error en la migración. Verifique los logs e intente nuevamente.")