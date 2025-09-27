#!/usr/bin/env python3
"""
Script para configurar la base de datos MySQL de Synapsis Apoyos
"""

import pymysql
import sys
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

# Configuración de la base de datos
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '732137A031E4b@',
    'charset': 'utf8mb4'
}

DB_NAME = 'synapsis_apoyos'

def crear_conexion(incluir_db=False):
    """Crea una conexión a MySQL"""
    config = DB_CONFIG.copy()
    if incluir_db:
        config['database'] = DB_NAME
    
    try:
        connection = pymysql.connect(**config)
        return connection
    except Exception as e:
        print(f"Error conectando a MySQL: {e}")
        return None

def crear_base_datos():
    """Crea la base de datos si no existe"""
    connection = crear_conexion()
    if not connection:
        return False
    
    try:
        with connection.cursor() as cursor:
            # Crear base de datos
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"✓ Base de datos '{DB_NAME}' creada o ya existe")
        
        connection.commit()
        return True
    except Exception as e:
        print(f"Error creando base de datos: {e}")
        return False
    finally:
        connection.close()

def crear_tablas():
    """Crea todas las tablas del sistema"""
    connection = crear_conexion(incluir_db=True)
    if not connection:
        return False
    
    try:
        with connection.cursor() as cursor:
            # Tabla usuarios
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    nombre VARCHAR(100) NOT NULL,
                    apellido VARCHAR(100) NOT NULL,
                    telefono VARCHAR(20),
                    rol ENUM('tecnico', 'movil', 'lider') NOT NULL,
                    activo BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_usuarios_email (email),
                    INDEX idx_usuarios_rol (rol),
                    INDEX idx_usuarios_activo (activo)
                )
            """)
            print("✓ Tabla 'usuarios' creada")
            
            # Tabla solicitudes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS solicitudes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    tecnico_id INT NOT NULL,
                    tipo_apoyo ENUM('escalera', 'equipos') NOT NULL,
                    latitud DECIMAL(10, 8) NOT NULL,
                    longitud DECIMAL(11, 8) NOT NULL,
                    direccion VARCHAR(500),
                    observaciones TEXT,
                    estado ENUM('pendiente', 'aceptada', 'rechazada', 'completada', 'cancelada', 'expirada') DEFAULT 'pendiente',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    limite_tiempo TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (tecnico_id) REFERENCES usuarios(id) ON DELETE CASCADE,
                    INDEX idx_solicitudes_tecnico (tecnico_id),
                    INDEX idx_solicitudes_estado (estado),
                    INDEX idx_solicitudes_ubicacion (latitud, longitud),
                    INDEX idx_solicitudes_created_at (created_at DESC)
                )
            """)
            print("✓ Tabla 'solicitudes' creada")
            
            # Tabla servicios
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS servicios (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    solicitud_id INT UNIQUE NOT NULL,
                    movil_id INT NOT NULL,
                    aceptado_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    iniciado_at TIMESTAMP NULL,
                    finalizado_at TIMESTAMP NULL,
                    observaciones_finales TEXT,
                    estado_servicio ENUM('aceptado', 'en_ruta', 'en_sitio', 'completado', 'cancelado') DEFAULT 'aceptado',
                    duracion_minutos INT DEFAULT 0,
                    FOREIGN KEY (solicitud_id) REFERENCES solicitudes(id) ON DELETE CASCADE,
                    FOREIGN KEY (movil_id) REFERENCES usuarios(id) ON DELETE CASCADE,
                    INDEX idx_servicios_movil (movil_id),
                    INDEX idx_servicios_estado (estado_servicio),
                    INDEX idx_servicios_fechas (aceptado_at, finalizado_at)
                )
            """)
            print("✓ Tabla 'servicios' creada")
            
            # Tabla ubicaciones
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ubicaciones (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    usuario_id INT NOT NULL,
                    latitud DECIMAL(10, 8) NOT NULL,
                    longitud DECIMAL(11, 8) NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    activa BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
                    INDEX idx_ubicaciones_usuario (usuario_id),
                    INDEX idx_ubicaciones_timestamp (timestamp DESC),
                    INDEX idx_ubicaciones_activa (activa)
                )
            """)
            print("✓ Tabla 'ubicaciones' creada")
            
            # Tabla observaciones
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS observaciones (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    servicio_id INT NOT NULL,
                    contenido TEXT NOT NULL,
                    tipo ENUM('rechazo', 'progreso', 'finalizacion') NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (servicio_id) REFERENCES servicios(id) ON DELETE CASCADE,
                    INDEX idx_observaciones_servicio (servicio_id),
                    INDEX idx_observaciones_tipo (tipo)
                )
            """)
            print("✓ Tabla 'observaciones' creada")
        
        connection.commit()
        return True
    except Exception as e:
        print(f"Error creando tablas: {e}")
        return False
    finally:
        connection.close()

def insertar_datos_prueba():
    """Inserta datos de prueba en el sistema"""
    connection = crear_conexion(incluir_db=True)
    if not connection:
        return False
    
    try:
        with connection.cursor() as cursor:
            # Verificar si ya existen usuarios
            cursor.execute("SELECT COUNT(*) FROM usuarios")
            count = cursor.fetchone()[0]
            
            if count > 0:
                print("✓ Ya existen usuarios en la base de datos")
                return True
            
            # Insertar usuarios de prueba
            usuarios_prueba = [
                {
                    'email': 'tecnico1@synapsis.com',
                    'password': 'tecnico123',
                    'nombre': 'Juan',
                    'apellido': 'Pérez',
                    'telefono': '3001234567',
                    'rol': 'tecnico'
                },
                {
                    'email': 'tecnico2@synapsis.com',
                    'password': 'tecnico123',
                    'nombre': 'Ana',
                    'apellido': 'García',
                    'telefono': '3001234568',
                    'rol': 'tecnico'
                },
                {
                    'email': 'movil1@synapsis.com',
                    'password': 'movil123',
                    'nombre': 'María',
                    'apellido': 'González',
                    'telefono': '3007654321',
                    'rol': 'movil'
                },
                {
                    'email': 'movil2@synapsis.com',
                    'password': 'movil123',
                    'nombre': 'Carlos',
                    'apellido': 'Martínez',
                    'telefono': '3007654322',
                    'rol': 'movil'
                },
                {
                    'email': 'lider1@synapsis.com',
                    'password': 'lider123',
                    'nombre': 'Roberto',
                    'apellido': 'Rodríguez',
                    'telefono': '3009876543',
                    'rol': 'lider'
                }
            ]
            
            for usuario in usuarios_prueba:
                password_hash = generate_password_hash(usuario['password'])
                cursor.execute("""
                    INSERT INTO usuarios (email, password_hash, nombre, apellido, telefono, rol)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    usuario['email'],
                    password_hash,
                    usuario['nombre'],
                    usuario['apellido'],
                    usuario['telefono'],
                    usuario['rol']
                ))
            
            print("✓ Usuarios de prueba insertados")
            
            # Insertar ubicaciones de prueba para móviles (Bogotá)
            ubicaciones_moviles = [
                {'usuario_id': 3, 'latitud': 4.6097, 'longitud': -74.0817},  # Centro Bogotá
                {'usuario_id': 4, 'latitud': 4.6351, 'longitud': -74.0703},  # Zona Norte
            ]
            
            for ubicacion in ubicaciones_moviles:
                cursor.execute("""
                    INSERT INTO ubicaciones (usuario_id, latitud, longitud)
                    VALUES (%s, %s, %s)
                """, (
                    ubicacion['usuario_id'],
                    ubicacion['latitud'],
                    ubicacion['longitud']
                ))
            
            print("✓ Ubicaciones de prueba insertadas")
        
        connection.commit()
        return True
    except Exception as e:
        print(f"Error insertando datos de prueba: {e}")
        return False
    finally:
        connection.close()

def main():
    """Función principal"""
    print("=== Configuración de Base de Datos Synapsis Apoyos ===")
    print()
    
    # Crear base de datos
    print("1. Creando base de datos...")
    if not crear_base_datos():
        print("❌ Error creando base de datos")
        sys.exit(1)
    
    # Crear tablas
    print("\n2. Creando tablas...")
    if not crear_tablas():
        print("❌ Error creando tablas")
        sys.exit(1)
    
    # Insertar datos de prueba
    print("\n3. Insertando datos de prueba...")
    if not insertar_datos_prueba():
        print("❌ Error insertando datos de prueba")
        sys.exit(1)
    
    print("\n✅ ¡Base de datos configurada exitosamente!")
    print("\n📋 Usuarios de prueba creados:")
    print("   • Técnicos: tecnico1@synapsis.com / tecnico2@synapsis.com (password: tecnico123)")
    print("   • Móviles: movil1@synapsis.com / movil2@synapsis.com (password: movil123)")
    print("   • Líder: lider1@synapsis.com (password: lider123)")
    print("\n🚀 La aplicación está lista para ejecutarse!")

if __name__ == '__main__':
    main()