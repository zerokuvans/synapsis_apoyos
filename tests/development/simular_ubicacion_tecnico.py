from app import create_app
from app.models.usuario import Usuario
from app.models.ubicacion import Ubicacion
from app import db
from datetime import datetime

def simular_ubicacion_tecnico():
    """Simular ubicación del técnico para probar móviles asignadas"""
    app = create_app()
    
    with app.app_context():
        print("=== SIMULANDO UBICACIÓN DEL TÉCNICO ===")
        
        # Buscar técnico Juan Pérez
        tecnico = Usuario.query.filter_by(nombre='Juan', apellido='Pérez', rol='tecnico').first()
        
        if not tecnico:
            print("❌ No se encontró el técnico Juan Pérez")
            return
            
        print(f"✅ Técnico encontrado: {tecnico.nombre} {tecnico.apellido} (ID: {tecnico.id})")
        
        # Verificar si ya tiene ubicación
        ubicacion_existente = Ubicacion.query.filter_by(usuario_id=tecnico.id).first()
        
        if ubicacion_existente:
            print(f"📍 Actualizando ubicación existente...")
            ubicacion_existente.latitud = 4.6097  # Centro de Bogotá
            ubicacion_existente.longitud = -74.0817
            ubicacion_existente.timestamp = datetime.utcnow()
            ubicacion_existente.activa = True
        else:
            print(f"📍 Creando nueva ubicación...")
            nueva_ubicacion = Ubicacion(
                usuario_id=tecnico.id,
                latitud=4.6097,  # Centro de Bogotá
                longitud=-74.0817
            )
            db.session.add(nueva_ubicacion)
        
        try:
            db.session.commit()
            print(f"✅ Ubicación del técnico actualizada: 4.6097, -74.0817")
            
            # Verificar la ubicación
            ubicacion_verificada = Ubicacion.query.filter_by(usuario_id=tecnico.id).first()
            if ubicacion_verificada:
                print(f"📍 Verificación: {ubicacion_verificada.latitud}, {ubicacion_verificada.longitud}")
                print(f"🕒 Timestamp: {ubicacion_verificada.timestamp}")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error actualizando ubicación: {e}")
            return
        
        print("\n=== PROBANDO API DE MÓVILES ASIGNADAS ===")
        
        # Simular llamada a la API
        from app.blueprints.tecnico.routes import api_moviles_asignadas
        from flask import Flask
        from flask_login import login_user
        
        # Crear contexto de request simulado
        with app.test_request_context('/tecnico/api/moviles-asignadas?lat=4.6097&lng=-74.0817'):
            # Simular login del técnico
            login_user(tecnico)
            
            try:
                # Llamar a la API
                response = api_moviles_asignadas()
                print(f"✅ API respondió correctamente")
                
                # Si es una respuesta JSON, obtener los datos
                if hasattr(response, 'get_json'):
                    data = response.get_json()
                    if data:
                        moviles_asignadas = data.get('moviles_asignadas', [])
                        print(f"📊 Móviles asignadas encontradas: {len(moviles_asignadas)}")
                        
                        for movil in moviles_asignadas:
                            print(f"🚗 {movil.get('nombre', 'N/A')} - Estado: {movil.get('estado_texto', 'N/A')}")
                            print(f"   📍 Distancia: {movil.get('distancia_km', 'N/A')} km")
                            print(f"   🔧 Tipo: {movil.get('tipo_apoyo', 'N/A')}")
                    else:
                        print("📊 No hay datos en la respuesta")
                else:
                    print(f"📊 Respuesta: {response}")
                    
            except Exception as e:
                print(f"❌ Error llamando a la API: {e}")
                import traceback
                traceback.print_exc()

if __name__ == '__main__':
    simular_ubicacion_tecnico()