#!/usr/bin/env python3
"""
Script para migrar datos existentes de vehículos a la nueva estructura
"""

import os
import sys
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db

def migrate_vehiculos_data():
    """Migrar datos existentes de vehículos"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔄 Migrando datos de vehículos...")
            
            # Obtener todos los vehículos existentes
            result = db.session.execute(db.text("SELECT * FROM vehiculos")).fetchall()
            print(f"📊 Encontrados {len(result)} vehículos para migrar")
            
            if not result:
                print("ℹ️  No hay vehículos para migrar")
                return True
            
            # Migrar cada vehículo
            for row in result:
                vehiculo_id = row[0]  # id
                placa = row[1]        # placa
                modelo = row[2]       # modelo
                color = row[3]        # color
                año = row[4]          # año
                tipo_antiguo = row[5] # tipo (columna antigua)
                
                print(f"🚗 Migrando vehículo ID {vehiculo_id} - {placa}")
                
                # Mapear tipo antiguo a tipo_vehiculo nuevo
                tipo_mapping = {
                    'moto': 'moto',
                    'carro': 'carro', 
                    'camioneta': 'camioneta',
                    'furgon': 'furgon',
                    'auto': 'carro',
                    'automovil': 'carro',
                    'motocicleta': 'moto'
                }
                
                tipo_vehiculo = tipo_mapping.get(tipo_antiguo.lower() if tipo_antiguo else '', 'carro')
                
                # Valores por defecto para campos requeridos
                marca = 'Sin especificar' if not hasattr(row, 'marca') or not row.marca else row.marca
                combustible = 'gasolina'  # Valor por defecto
                
                try:
                    # Actualizar el registro con los nuevos campos
                    update_sql = """
                    UPDATE vehiculos 
                    SET 
                        marca = :marca,
                        tipo_vehiculo = :tipo_vehiculo,
                        combustible = :combustible
                    WHERE id = :vehiculo_id
                    """
                    
                    db.session.execute(db.text(update_sql), {
                        'marca': marca,
                        'tipo_vehiculo': tipo_vehiculo,
                        'combustible': combustible,
                        'vehiculo_id': vehiculo_id
                    })
                    
                    print(f"  ✅ Migrado: {placa} -> tipo: {tipo_vehiculo}, marca: {marca}")
                    
                except Exception as e:
                    print(f"  ❌ Error migrando {placa}: {str(e)}")
                    continue
            
            # Confirmar cambios
            db.session.commit()
            print("✅ Migración de datos completada")
            
            # Verificar resultados
            print("\n🔍 Verificando migración...")
            result = db.session.execute(db.text(
                "SELECT id, placa, marca, tipo_vehiculo, combustible FROM vehiculos LIMIT 5"
            )).fetchall()
            
            for row in result:
                print(f"  📋 ID {row[0]}: {row[1]} - {row[2]} {row[3]} ({row[4]})")
            
            return True
            
        except Exception as e:
            print(f"❌ Error en migración de datos: {str(e)}")
            db.session.rollback()
            return False

def cleanup_old_columns():
    """Limpiar columnas antiguas que ya no se usan"""
    app = create_app()
    
    with app.app_context():
        try:
            print("\n🧹 Limpiando columnas antiguas...")
            
            # Lista de columnas que pueden ser eliminadas
            old_columns = ['tipo', 'soat_vigente', 'revision_tecnica']
            
            for column in old_columns:
                try:
                    # Verificar si la columna existe
                    inspector = db.inspect(db.engine)
                    columns = inspector.get_columns('vehiculos')
                    column_names = [col['name'] for col in columns]
                    
                    if column in column_names:
                        print(f"  🗑️  Eliminando columna: {column}")
                        db.session.execute(db.text(f"ALTER TABLE vehiculos DROP COLUMN {column}"))
                        db.session.commit()
                        print(f"  ✅ Columna {column} eliminada")
                    else:
                        print(f"  ℹ️  Columna {column} no existe")
                        
                except Exception as e:
                    print(f"  ⚠️  Error eliminando {column}: {str(e)}")
                    db.session.rollback()
                    continue
            
            print("✅ Limpieza de columnas completada")
            return True
            
        except Exception as e:
            print(f"❌ Error en limpieza: {str(e)}")
            return False

def verify_final_structure():
    """Verificar la estructura final de la tabla"""
    app = create_app()
    
    with app.app_context():
        try:
            print("\n🔍 Verificación final de estructura...")
            
            inspector = db.inspect(db.engine)
            columns = inspector.get_columns('vehiculos')
            
            print(f"📋 Total de columnas: {len(columns)}")
            
            required_columns = [
                'id', 'placa', 'marca', 'modelo', 'año', 'color', 
                'tipo_vehiculo', 'combustible', 'activo', 'movil_id'
            ]
            
            column_names = [col['name'] for col in columns]
            
            print("✅ Columnas presentes:")
            for col in required_columns:
                status = "✅" if col in column_names else "❌"
                print(f"  {status} {col}")
            
            # Verificar algunos datos
            result = db.session.execute(db.text(
                "SELECT COUNT(*) as total, "
                "COUNT(CASE WHEN marca IS NOT NULL THEN 1 END) as con_marca, "
                "COUNT(CASE WHEN tipo_vehiculo IS NOT NULL THEN 1 END) as con_tipo "
                "FROM vehiculos"
            )).fetchone()
            
            print(f"\n📊 Datos migrados:")
            print(f"  Total vehículos: {result[0]}")
            print(f"  Con marca: {result[1]}")
            print(f"  Con tipo_vehiculo: {result[2]}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error en verificación: {str(e)}")
            return False

if __name__ == "__main__":
    print("🚀 Iniciando migración de datos de vehículos...")
    print(f"⏰ Timestamp: {datetime.now()}")
    
    # Paso 1: Migrar datos
    success = migrate_vehiculos_data()
    
    if success:
        # Paso 2: Limpiar columnas antiguas (opcional)
        print("\n" + "="*50)
        cleanup_old_columns()
        
        # Paso 3: Verificación final
        print("\n" + "="*50)
        verify_final_structure()
        
        print("\n✅ ¡Migración de datos completada exitosamente!")
    else:
        print("\n❌ La migración de datos falló")
        sys.exit(1)