#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utilidades para procesamiento de polígonos territoriales

Este módulo contiene funciones para:
- Validación de coordenadas de polígonos
- Algoritmos de punto-en-polígono
- Cálculo de centroides y áreas
- Simplificación de polígonos
- Conversión entre formatos geográficos
"""

import math
from typing import List, Tuple, Optional, Dict, Any
from decimal import Decimal

def validate_polygon_coordinates(coordinates: List) -> bool:
    """
    Valida que las coordenadas formen un polígono válido
    
    Args:
        coordinates: Lista de coordenadas del polígono
    
    Returns:
        bool: True si el polígono es válido
    """
    if not coordinates or not isinstance(coordinates, list):
        return False
    
    # Verificar estructura básica
    if len(coordinates) == 0:
        return False
    
    # Para MultiPolygon, tomar el primer polígono
    polygon_coords = coordinates[0] if coordinates else []
    
    # Verificar que sea una lista de anillos
    if not isinstance(polygon_coords, list) or len(polygon_coords) == 0:
        return False
    
    # Tomar el anillo exterior (primer elemento)
    exterior_ring = polygon_coords[0] if polygon_coords else []
    
    if not isinstance(exterior_ring, list) or len(exterior_ring) < 3:
        return False
    
    # Verificar que cada punto tenga al menos 2 coordenadas (lat, lng)
    for point in exterior_ring:
        if not isinstance(point, list) or len(point) < 2:
            return False
        
        # Verificar que las coordenadas sean números válidos
        try:
            float(point[0])  # longitud
            float(point[1])  # latitud
        except (ValueError, TypeError):
            return False
    
    return True

def point_in_polygon(point_lat: float, point_lng: float, polygon_coords: List) -> bool:
    """
    Determina si un punto está dentro de un polígono usando el algoritmo Ray Casting
    
    Args:
        point_lat: Latitud del punto
        point_lng: Longitud del punto
        polygon_coords: Coordenadas del polígono
    
    Returns:
        bool: True si el punto está dentro del polígono
    """
    if not validate_polygon_coordinates(polygon_coords):
        return False
    
    # Extraer el anillo exterior del polígono
    exterior_ring = polygon_coords[0][0] if polygon_coords and polygon_coords[0] else []
    
    if len(exterior_ring) < 3:
        return False
    
    # Algoritmo Ray Casting
    inside = False
    j = len(exterior_ring) - 1
    
    for i in range(len(exterior_ring)):
        xi, yi = exterior_ring[i][0], exterior_ring[i][1]  # lng, lat
        xj, yj = exterior_ring[j][0], exterior_ring[j][1]  # lng, lat
        
        if ((yi > point_lat) != (yj > point_lat)) and \
           (point_lng < (xj - xi) * (point_lat - yi) / (yj - yi) + xi):
            inside = not inside
        
        j = i
    
    return inside

def calculate_polygon_centroid(coordinates: List) -> Tuple[Optional[float], Optional[float]]:
    """
    Calcula el centroide de un polígono
    
    Args:
        coordinates: Coordenadas del polígono
    
    Returns:
        Tuple[float, float]: (latitud, longitud) del centroide o (None, None)
    """
    if not validate_polygon_coordinates(coordinates):
        return None, None
    
    # Extraer el anillo exterior
    exterior_ring = coordinates[0][0] if coordinates and coordinates[0] else []
    
    if len(exterior_ring) < 3:
        return None, None
    
    # Calcular centroide simple (promedio de coordenadas)
    total_lat = 0.0
    total_lng = 0.0
    count = 0
    
    for point in exterior_ring:
        if len(point) >= 2:
            total_lng += float(point[0])  # longitud
            total_lat += float(point[1])  # latitud
            count += 1
    
    if count == 0:
        return None, None
    
    centroid_lat = total_lat / count
    centroid_lng = total_lng / count
    
    return centroid_lat, centroid_lng

def calculate_polygon_area(coordinates: List) -> Optional[float]:
    """
    Calcula el área aproximada de un polígono en metros cuadrados
    usando la fórmula del shoelace
    
    Args:
        coordinates: Coordenadas del polígono
    
    Returns:
        float: Área en metros cuadrados o None si es inválido
    """
    if not validate_polygon_coordinates(coordinates):
        return None
    
    # Extraer el anillo exterior
    exterior_ring = coordinates[0][0] if coordinates and coordinates[0] else []
    
    if len(exterior_ring) < 3:
        return None
    
    # Convertir coordenadas geográficas a metros (aproximación)
    # Factor de conversión aproximado para Bogotá (4.6°N)
    lat_to_m = 111320.0  # metros por grado de latitud
    lng_to_m = 111320.0 * math.cos(math.radians(4.6))  # metros por grado de longitud
    
    # Convertir coordenadas a metros
    points_m = []
    for point in exterior_ring:
        if len(point) >= 2:
            x_m = float(point[0]) * lng_to_m  # longitud a metros
            y_m = float(point[1]) * lat_to_m  # latitud a metros
            points_m.append((x_m, y_m))
    
    if len(points_m) < 3:
        return None
    
    # Fórmula del shoelace para calcular área
    area = 0.0
    n = len(points_m)
    
    for i in range(n):
        j = (i + 1) % n
        area += points_m[i][0] * points_m[j][1]
        area -= points_m[j][0] * points_m[i][1]
    
    area = abs(area) / 2.0
    return area

def simplify_polygon(coordinates: List, tolerance: float = 0.001) -> List:
    """
    Simplifica un polígono reduciendo el número de puntos
    usando el algoritmo Douglas-Peucker simplificado
    
    Args:
        coordinates: Coordenadas del polígono original
        tolerance: Tolerancia para la simplificación (en grados)
    
    Returns:
        List: Coordenadas del polígono simplificado
    """
    if not validate_polygon_coordinates(coordinates):
        return coordinates
    
    # Extraer el anillo exterior
    exterior_ring = coordinates[0][0] if coordinates and coordinates[0] else []
    
    if len(exterior_ring) <= 3:
        return coordinates  # No simplificar polígonos muy pequeños
    
    # Simplificación básica: eliminar puntos muy cercanos
    simplified = [exterior_ring[0]]  # Siempre mantener el primer punto
    
    for i in range(1, len(exterior_ring)):
        current_point = exterior_ring[i]
        last_point = simplified[-1]
        
        # Calcular distancia euclidiana
        dist = math.sqrt(
            (float(current_point[0]) - float(last_point[0])) ** 2 +
            (float(current_point[1]) - float(last_point[1])) ** 2
        )
        
        # Solo agregar si la distancia es mayor que la tolerancia
        if dist > tolerance:
            simplified.append(current_point)
    
    # Asegurar que el polígono esté cerrado
    if simplified[0] != simplified[-1]:
        simplified.append(simplified[0])
    
    # Reconstruir la estructura original
    return [[[point for point in simplified]]]

def get_polygon_bounds(coordinates: List) -> Optional[Dict[str, float]]:
    """
    Calcula los límites (bounding box) de un polígono
    
    Args:
        coordinates: Coordenadas del polígono
    
    Returns:
        Dict: {'min_lat', 'max_lat', 'min_lng', 'max_lng'} o None
    """
    if not validate_polygon_coordinates(coordinates):
        return None
    
    # Extraer el anillo exterior
    exterior_ring = coordinates[0][0] if coordinates and coordinates[0] else []
    
    if len(exterior_ring) == 0:
        return None
    
    # Inicializar con el primer punto
    first_point = exterior_ring[0]
    min_lng = max_lng = float(first_point[0])
    min_lat = max_lat = float(first_point[1])
    
    # Encontrar límites
    for point in exterior_ring[1:]:
        if len(point) >= 2:
            lng = float(point[0])
            lat = float(point[1])
            
            min_lng = min(min_lng, lng)
            max_lng = max(max_lng, lng)
            min_lat = min(min_lat, lat)
            max_lat = max(max_lat, lat)
    
    return {
        'min_lat': min_lat,
        'max_lat': max_lat,
        'min_lng': min_lng,
        'max_lng': max_lng
    }

def convert_to_geojson(coordinates: List, properties: Dict = None) -> Dict:
    """
    Convierte coordenadas de polígono a formato GeoJSON
    
    Args:
        coordinates: Coordenadas del polígono
        properties: Propiedades adicionales para el GeoJSON
    
    Returns:
        Dict: Objeto GeoJSON
    """
    if properties is None:
        properties = {}
    
    return {
        "type": "Feature",
        "geometry": {
            "type": "MultiPolygon",
            "coordinates": coordinates
        },
        "properties": properties
    }

def distance_between_points(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calcula la distancia entre dos puntos usando la fórmula de Haversine
    
    Args:
        lat1, lng1: Coordenadas del primer punto
        lat2, lng2: Coordenadas del segundo punto
    
    Returns:
        float: Distancia en metros
    """
    # Radio de la Tierra en metros
    R = 6371000
    
    # Convertir grados a radianes
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)
    
    # Fórmula de Haversine
    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lng / 2) ** 2)
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    
    return distance

def find_closest_point_on_polygon(point_lat: float, point_lng: float, coordinates: List) -> Optional[Tuple[float, float]]:
    """
    Encuentra el punto más cercano en el perímetro de un polígono
    
    Args:
        point_lat, point_lng: Coordenadas del punto de referencia
        coordinates: Coordenadas del polígono
    
    Returns:
        Tuple[float, float]: (lat, lng) del punto más cercano o None
    """
    if not validate_polygon_coordinates(coordinates):
        return None
    
    # Extraer el anillo exterior
    exterior_ring = coordinates[0][0] if coordinates and coordinates[0] else []
    
    if len(exterior_ring) < 2:
        return None
    
    min_distance = float('inf')
    closest_point = None
    
    # Verificar cada punto del polígono
    for point in exterior_ring:
        if len(point) >= 2:
            poly_lng = float(point[0])
            poly_lat = float(point[1])
            
            distance = distance_between_points(point_lat, point_lng, poly_lat, poly_lng)
            
            if distance < min_distance:
                min_distance = distance
                closest_point = (poly_lat, poly_lng)
    
    return closest_point