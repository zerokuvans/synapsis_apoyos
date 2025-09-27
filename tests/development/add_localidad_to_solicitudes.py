#!/usr/bin/env python3
"""
Script para agregar el campo localidad_id a la tabla solicitudes
y asignar localidades basándose en las coordenadas existentes
"""

import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def conectar_db():
    """Conecta a la base de datos MySQL"""
    try:
        # Usar la configuración de DATABASE_URL
        database_url = os.getenv('DATABASE_URL', '')
        if 'mysql+pymysql://' in database_url:
            # Extraer componentes de la URL
            # mysql+pymysql://root:732137A031E4b%40@localhost/synapsis_apoyos
            url_parts = database_url.replace('mysql+pymysql://', '').split('@')
            user_pass = url_parts[0].split(':')
            host_db = url_parts[1].split('/')
            
            user = user_pass[0]
            password = user_pass[1].replace('%40', '@')  # Decodificar %40 a @
            host = host_db[0]
            database = host_db[1]
        else:
            # Fallback a variables individuales
            host = os.getenv('DB_HOST', 'localhost')
            database = os.getenv('DB_NAME', 'synapsis_apoyos')
            user = os.getenv('DB_USER', 'root')
            password = os.getenv('DB_PASSWORD', '')
        
        connection = mysql.connector.connect(
            host=host,
            database=database,
            user=user,
            password=password
        )
        return connection
    except Error as e:
        print(f"❌ Error conectando a MySQL: {e}")
        return None

def agregar_columna_localidad():
    """Agrega la columna localidad_id a la tabla solicitudes"""
    connection = conectar_db()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        # Verificar si la columna ya existe
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = 'synapsis_apoyos'
            AND TABLE_NAME = 'solicitudes' 
            AND COLUMN_NAME = 'localidad_id'
        """)
        
        existe = cursor.fetchone()[0] > 0
        
        if existe:
            print("✓ La columna 'localidad_id' ya existe en la tabla 'solicitudes'")
            return True
        
        # Agregar la columna
        print("1. Agregando columna 'localidad_id' a la tabla 'solicitudes'...")
        cursor.execute("""
            ALTER TABLE solicitudes 
            ADD COLUMN localidad_id INT NULL,
            ADD INDEX idx_solicitudes_localidad (localidad_id),
            ADD FOREIGN KEY (localidad_id) REFERENCES localidades(id)
        """)
        
        connection.commit()
        print("✓ Columna 'localidad_id' agregada exitosamente")
        return True
        
    except Error as e:
        print(f"❌ Error agregando columna: {e}")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def asignar_localidades_por_coordenadas():
    """Asigna localidades a las solicitudes existentes basándose en sus coordenadas"""
    connection = conectar_db()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        # Obtener solicitudes sin localidad asignada
        cursor.execute("""
            SELECT id, latitud, longitud 
            FROM solicitudes 
            WHERE localidad_id IS NULL
        """)
        
        solicitudes = cursor.fetchall()
        print(f"2. Procesando {len(solicitudes)} solicitudes sin localidad...")
        
        if not solicitudes:
            print("✓ No hay solicitudes sin localidad para procesar")
            return True
        
        # Obtener localidades con sus coordenadas
        cursor.execute("""
            SELECT id, codigo, nombre, latitud_centro, longitud_centro 
            FROM localidades 
            WHERE activa = TRUE
        """)
        
        localidades = cursor.fetchall()
        print(f"   Localidades disponibles: {len(localidades)}")
        
        actualizadas = 0
        
        for solicitud_id, lat_sol, lon_sol in solicitudes:
            # Encontrar la localidad más cercana
            distancia_minima = float('inf')
            localidad_cercana = None
            
            for loc_id, codigo, nombre, lat_loc, lon_loc in localidades:
                # Calcular distancia euclidiana simple
                distancia = ((float(lat_sol) - float(lat_loc)) ** 2 + 
                           (float(lon_sol) - float(lon_loc)) ** 2) ** 0.5
                
                if distancia < distancia_minima:
                    distancia_minima = distancia
                    localidad_cercana = (loc_id, codigo, nombre)
            
            if localidad_cercana:
                # Asignar la localidad más cercana
                cursor.execute("""
                    UPDATE solicitudes 
                    SET localidad_id = %s 
                    WHERE id = %s
                """, (localidad_cercana[0], solicitud_id))
                
                actualizadas += 1
                print(f"   • Solicitud {solicitud_id} → {localidad_cercana[1]} - {localidad_cercana[2]}")
        
        connection.commit()
        print(f"✓ {actualizadas} solicitudes actualizadas con localidades")
        return True
        
    except Error as e:
        print(f"❌ Error asignando localidades: {e}")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def verificar_resultado():
    """Verifica el resultado de la migración"""
    connection = conectar_db()
    if not connection:
        return
    
    try:
        cursor = connection.cursor()
        
        # Contar solicitudes por localidad
        cursor.execute("""
            SELECT 
                l.codigo,
                l.nombre,
                COUNT(s.id) as total_solicitudes
            FROM localidades l
            LEFT JOIN solicitudes s ON l.id = s.localidad_id
            GROUP BY l.id, l.codigo, l.nombre
            ORDER BY total_solicitudes DESC
        """)
        
        resultados = cursor.fetchall()
        
        print("\n📊 Distribución de solicitudes por localidad:")
        total_con_localidad = 0
        for codigo, nombre, total in resultados:
            if total > 0:
                print(f"   • {codigo} - {nombre}: {total} solicitudes")
                total_con_localidad += total
        
        # Contar solicitudes sin localidad
        cursor.execute("SELECT COUNT(*) FROM solicitudes WHERE localidad_id IS NULL")
        sin_localidad = cursor.fetchone()[0]
        
        print(f"\n✅ Resumen:")
        print(f"   • Solicitudes con localidad: {total_con_localidad}")
        print(f"   • Solicitudes sin localidad: {sin_localidad}")
        
    except Error as e:
        print(f"❌ Error verificando resultado: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def main():
    print("🔄 Iniciando migración de localidades en solicitudes...")
    
    # Paso 1: Agregar columna
    if not agregar_columna_localidad():
        print("❌ Falló la adición de la columna")
        return
    
    # Paso 2: Asignar localidades
    if not asignar_localidades_por_coordenadas():
        print("❌ Falló la asignación de localidades")
        return
    
    # Paso 3: Verificar resultado
    verificar_resultado()
    
    print("\n🚀 ¡Migración completada exitosamente!")
    print("   Las solicitudes ahora pueden filtrarse por localidad")

if __name__ == "__main__":
    main()