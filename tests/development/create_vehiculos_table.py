#!/usr/bin/env python3
"""
Script para crear/actualizar la tabla vehiculos en MySQL
"""

import os
import sys
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.vehiculo import Vehiculo

def migrate_vehiculos_table():
    """Migrar la tabla vehiculos a la nueva estructura"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🚗 Migrando tabla vehiculos...")
            
            # Verificar si la tabla ya existe
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            if 'vehiculos' not in existing_tables:
                print("📋 Tabla vehiculos no existe, creando nueva...")
                db.create_all()
                print("✅ Tabla vehiculos creada exitosamente")
                return True
            
            # La tabla existe, verificar estructura
            columns = inspector.get_columns('vehiculos')
            column_names = [col['name'] for col in columns]
            print(f"📋 Columnas existentes: {column_names}")
            
            # Verificar si faltan columnas del modelo
            required_columns = {
                'id': 'INT AUTO_INCREMENT PRIMARY KEY',
                'placa': 'VARCHAR(10) UNIQUE NOT NULL',
                'marca': 'VARCHAR(50) NOT NULL',
                'modelo': 'VARCHAR(50) NOT NULL',
                'año': 'INT NOT NULL',
                'color': 'VARCHAR(30) NOT NULL',
                'tipo_vehiculo': "ENUM('moto', 'carro', 'camioneta', 'furgon') NOT NULL",
                'numero_motor': 'VARCHAR(50)',
                'numero_chasis': 'VARCHAR(50)',
                'cilindraje': 'VARCHAR(20)',
                'combustible': "ENUM('gasolina', 'diesel', 'electrico', 'hibrido') NOT NULL",
                'activo': 'BOOLEAN DEFAULT TRUE',
                'observaciones': 'TEXT',
                'movil_id': 'INT',
                'created_at': 'DATETIME DEFAULT CURRENT_TIMESTAMP',
                'updated_at': 'DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'
            }
            
            missing_columns = [col for col in required_columns.keys() if col not in column_names]
            
            if not missing_columns:
                print("✅ La tabla tiene todas las columnas necesarias")
                return True
            
            print(f"🔧 Faltan columnas: {missing_columns}")
            print("📝 Agregando columnas faltantes...")
            
            # Agregar columnas faltantes una por una
            for column_name in missing_columns:
                if column_name == 'id':
                    continue  # No podemos agregar ID como AUTO_INCREMENT a tabla existente
                
                column_def = required_columns[column_name]
                
                try:
                    # Ajustar definición para ALTER TABLE
                    if 'DEFAULT TRUE' in column_def:
                        column_def = column_def.replace('DEFAULT TRUE', 'DEFAULT 1')
                    elif 'DEFAULT FALSE' in column_def:
                        column_def = column_def.replace('DEFAULT FALSE', 'DEFAULT 0')
                    
                    sql = f"ALTER TABLE vehiculos ADD COLUMN {column_name} {column_def}"
                    print(f"  ➕ Agregando columna: {column_name}")
                    db.session.execute(db.text(sql))
                    db.session.commit()
                    
                except Exception as e:
                    print(f"  ⚠️  Error agregando {column_name}: {str(e)}")
                    # Continuar con las demás columnas
                    db.session.rollback()
            
            # Agregar índices si no existen
            try:
                print("🔗 Agregando índices...")
                
                # Índice en placa (si no existe)
                try:
                    db.session.execute(db.text("CREATE INDEX idx_vehiculos_placa ON vehiculos(placa)"))
                    db.session.commit()
                    print("  ✅ Índice en placa creado")
                except:
                    print("  ℹ️  Índice en placa ya existe")
                    db.session.rollback()
                
                # Índice en activo
                try:
                    db.session.execute(db.text("CREATE INDEX idx_vehiculos_activo ON vehiculos(activo)"))
                    db.session.commit()
                    print("  ✅ Índice en activo creado")
                except:
                    print("  ℹ️  Índice en activo ya existe")
                    db.session.rollback()
                
                # Índice en movil_id
                try:
                    db.session.execute(db.text("CREATE INDEX idx_vehiculos_movil_id ON vehiculos(movil_id)"))
                    db.session.commit()
                    print("  ✅ Índice en movil_id creado")
                except:
                    print("  ℹ️  Índice en movil_id ya existe")
                    db.session.rollback()
                
            except Exception as e:
                print(f"⚠️  Error creando índices: {str(e)}")
            
            # Agregar clave foránea si no existe
            try:
                print("🔑 Verificando clave foránea...")
                foreign_keys = inspector.get_foreign_keys('vehiculos')
                
                has_movil_fk = any(fk['constrained_columns'] == ['movil_id'] for fk in foreign_keys)
                
                if not has_movil_fk:
                    db.session.execute(db.text(
                        "ALTER TABLE vehiculos ADD CONSTRAINT fk_vehiculos_movil_id "
                        "FOREIGN KEY (movil_id) REFERENCES usuarios(id) ON DELETE SET NULL"
                    ))
                    db.session.commit()
                    print("  ✅ Clave foránea movil_id creada")
                else:
                    print("  ℹ️  Clave foránea movil_id ya existe")
                    
            except Exception as e:
                print(f"⚠️  Error con clave foránea: {str(e)}")
                db.session.rollback()
            
            print("✅ Migración de tabla vehiculos completada")
            return True
                
        except Exception as e:
            print(f"❌ Error en migración: {str(e)}")
            db.session.rollback()
            return False

def verify_table_structure():
    """Verificar la estructura de la tabla vehiculos"""
    app = create_app()
    
    with app.app_context():
        try:
            inspector = db.inspect(db.engine)
            
            if 'vehiculos' not in inspector.get_table_names():
                print("❌ La tabla 'vehiculos' no existe")
                return False
            
            columns = inspector.get_columns('vehiculos')
            indexes = inspector.get_indexes('vehiculos')
            foreign_keys = inspector.get_foreign_keys('vehiculos')
            
            print("\n🔍 Verificación de estructura:")
            print(f"📋 Columnas: {len(columns)}")
            for col in columns:
                print(f"  - {col['name']}: {col['type']}")
            
            print(f"\n🔗 Índices: {len(indexes)}")
            for idx in indexes:
                print(f"  - {idx['name']}: {idx['column_names']}")
            
            print(f"\n🔑 Claves foráneas: {len(foreign_keys)}")
            for fk in foreign_keys:
                print(f"  - {fk['name']}: {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")
            
            # Verificar columnas específicas
            column_names = [col['name'] for col in columns]
            required_columns = [
                'id', 'placa', 'marca', 'modelo', 'año', 'color', 
                'tipo_vehiculo', 'combustible', 'activo', 'movil_id'
            ]
            
            missing = [col for col in required_columns if col not in column_names]
            if missing:
                print(f"\n❌ Faltan columnas: {missing}")
                return False
            
            print("\n✅ Estructura de tabla verificada correctamente")
            return True
            
        except Exception as e:
            print(f"❌ Error al verificar estructura: {str(e)}")
            return False

if __name__ == "__main__":
    print("🚀 Iniciando migración de tabla vehiculos...")
    print(f"⏰ Timestamp: {datetime.now()}")
    
    success = migrate_vehiculos_table()
    
    if success:
        print("\n🔍 Verificando estructura final...")
        verify_table_structure()
        print("\n✅ ¡Migración completada exitosamente!")
    else:
        print("\n❌ La migración falló")
        sys.exit(1)