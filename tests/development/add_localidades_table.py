#!/usr/bin/env python3
"""
Script para agregar la tabla de localidades a la base de datos MySQL de Synapsis Apoyos
"""

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

def crear_conexion():
    """Crea una conexión a MySQL"""
    try:
        connection = pymysql.connect(**DB_CONFIG)
        return connection
    except Exception as e:
        print(f"Error conectando a MySQL: {e}")
        return None

def crear_tabla_localidades():
    """Crea la tabla de localidades en la base de datos"""
    connection = crear_conexion()
    if not connection:
        return False
    
    try:
        with connection.cursor() as cursor:
            # Crear tabla localidades
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS localidades (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nombre VARCHAR(100) NOT NULL,
                    codigo VARCHAR(10) UNIQUE NOT NULL,
                    area DECIMAL(12, 4) DEFAULT NULL COMMENT 'Área en hectáreas',
                    geometria JSON DEFAULT NULL COMMENT 'Coordenadas del polígono en formato GeoJSON',
                    latitud_centro DECIMAL(10, 8) DEFAULT NULL COMMENT 'Latitud del centroide',
                    longitud_centro DECIMAL(11, 8) DEFAULT NULL COMMENT 'Longitud del centroide',
                    descripcion TEXT DEFAULT NULL,
                    activa BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_localidades_codigo (codigo),
                    INDEX idx_localidades_nombre (nombre),
                    INDEX idx_localidades_centro (latitud_centro, longitud_centro),
                    INDEX idx_localidades_activa (activa)
                )
            """)
            print("✓ Tabla 'localidades' creada exitosamente")
            
            # Agregar campo localidad_id a la tabla solicitudes (opcional)
            try:
                cursor.execute("""
                    ALTER TABLE solicitudes 
                    ADD COLUMN localidad_id INT DEFAULT NULL,
                    ADD INDEX idx_solicitudes_localidad (localidad_id),
                    ADD FOREIGN KEY (localidad_id) REFERENCES localidades(id) ON DELETE SET NULL
                """)
                print("✓ Campo 'localidad_id' agregado a tabla 'solicitudes'")
            except pymysql.err.OperationalError as e:
                if "Duplicate column name" in str(e):
                    print("✓ Campo 'localidad_id' ya existe en tabla 'solicitudes'")
                else:
                    print(f"⚠️  Advertencia al agregar campo localidad_id: {e}")
            
            # Agregar campo localidad_id a la tabla ubicaciones (opcional)
            try:
                cursor.execute("""
                    ALTER TABLE ubicaciones 
                    ADD COLUMN localidad_id INT DEFAULT NULL,
                    ADD INDEX idx_ubicaciones_localidad (localidad_id),
                    ADD FOREIGN KEY (localidad_id) REFERENCES localidades(id) ON DELETE SET NULL
                """)
                print("✓ Campo 'localidad_id' agregado a tabla 'ubicaciones'")
            except pymysql.err.OperationalError as e:
                if "Duplicate column name" in str(e):
                    print("✓ Campo 'localidad_id' ya existe en tabla 'ubicaciones'")
                else:
                    print(f"⚠️  Advertencia al agregar campo localidad_id: {e}")
        
        connection.commit()
        return True
    except Exception as e:
        print(f"Error creando tabla localidades: {e}")
        return False
    finally:
        connection.close()

def insertar_localidades_bogota():
    """Inserta las 20 localidades de Bogotá como datos iniciales"""
    connection = crear_conexion()
    if not connection:
        return False
    
    try:
        with connection.cursor() as cursor:
            # Verificar si ya existen localidades
            cursor.execute("SELECT COUNT(*) FROM localidades")
            count = cursor.fetchone()[0]
            
            if count > 0:
                print("✓ Ya existen localidades en la base de datos")
                return True
            
            # Localidades de Bogotá D.C.
            localidades_bogota = [
                {'codigo': '01', 'nombre': 'Usaquén', 'latitud': 4.6947, 'longitud': -74.0306},
                {'codigo': '02', 'nombre': 'Chapinero', 'latitud': 4.6304, 'longitud': -74.0583},
                {'codigo': '03', 'nombre': 'Santa Fe', 'latitud': 4.6097, 'longitud': -74.0817},
                {'codigo': '04', 'nombre': 'San Cristóbal', 'latitud': 4.5694, 'longitud': -74.0861},
                {'codigo': '05', 'nombre': 'Usme', 'latitud': 4.4806, 'longitud': -74.1361},
                {'codigo': '06', 'nombre': 'Tunjuelito', 'latitud': 4.5722, 'longitud': -74.1333},
                {'codigo': '07', 'nombre': 'Bosa', 'latitud': 4.6139, 'longitud': -74.1917},
                {'codigo': '08', 'nombre': 'Kennedy', 'latitud': 4.6278, 'longitud': -74.1556},
                {'codigo': '09', 'nombre': 'Fontibón', 'latitud': 4.6667, 'longitud': -74.1417},
                {'codigo': '10', 'nombre': 'Engativá', 'latitud': 4.6889, 'longitud': -74.1139},
                {'codigo': '11', 'nombre': 'Suba', 'latitud': 4.7556, 'longitud': -74.0889},
                {'codigo': '12', 'nombre': 'Barrios Unidos', 'latitud': 4.6611, 'longitud': -74.0806},
                {'codigo': '13', 'nombre': 'Teusaquillo', 'latitud': 4.6361, 'longitud': -74.0889},
                {'codigo': '14', 'nombre': 'Los Mártires', 'latitud': 4.6056, 'longitud': -74.0944},
                {'codigo': '15', 'nombre': 'Antonio Nariño', 'latitud': 4.5889, 'longitud': -74.0944},
                {'codigo': '16', 'nombre': 'Puente Aranda', 'latitud': 4.6167, 'longitud': -74.1167},
                {'codigo': '17', 'nombre': 'La Candelaria', 'latitud': 4.5972, 'longitud': -74.0750},
                {'codigo': '18', 'nombre': 'Rafael Uribe Uribe', 'latitud': 4.5556, 'longitud': -74.1056},
                {'codigo': '19', 'nombre': 'Ciudad Bolívar', 'latitud': 4.5167, 'longitud': -74.1500},
                {'codigo': '20', 'nombre': 'Sumapaz', 'latitud': 4.2167, 'longitud': -74.3500}
            ]
            
            for localidad in localidades_bogota:
                cursor.execute("""
                    INSERT INTO localidades (codigo, nombre, latitud_centro, longitud_centro, descripcion, activa, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
                """, (
                    localidad['codigo'],
                    localidad['nombre'],
                    localidad['latitud'],
                    localidad['longitud'],
                    f"Localidad {localidad['nombre']} de Bogotá D.C.",
                    True
                ))
            
            print("✓ 20 localidades de Bogotá insertadas exitosamente")
        
        connection.commit()
        return True
    except Exception as e:
        print(f"Error insertando localidades: {e}")
        return False
    finally:
        connection.close()

def main():
    """Función principal"""
    print("=== Agregando Tabla de Localidades - Synapsis Apoyos ===")
    print()
    
    # Crear tabla localidades
    print("1. Creando tabla 'localidades'...")
    if not crear_tabla_localidades():
        print("❌ Error creando tabla localidades")
        sys.exit(1)
    
    # Insertar localidades de Bogotá
    print("\n2. Insertando localidades de Bogotá...")
    if not insertar_localidades_bogota():
        print("❌ Error insertando localidades")
        sys.exit(1)
    
    print("\n✅ ¡Tabla de localidades configurada exitosamente!")
    print("\n📍 Localidades disponibles:")
    print("   • 20 localidades de Bogotá D.C. con coordenadas de centroide")
    print("   • Campos preparados para geometría GeoJSON")
    print("   • Referencias opcionales en solicitudes y ubicaciones")
    print("\n🚀 Listo para integrar con APIs y mapas!")

if __name__ == '__main__':
    main()