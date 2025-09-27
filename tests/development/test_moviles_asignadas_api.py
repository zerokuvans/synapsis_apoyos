from app import create_app
from app.models.usuario import Usuario
from app.models.servicio import Servicio
from app.models.solicitud import Solicitud
from app.models.ubicacion import Ubicacion
import requests
import json

def test_api_moviles_asignadas():
    """Probar la API de móviles asignadas directamente"""
    app = create_app()
    
    with app.app_context():
        print("=== PROBANDO API DE MÓVILES ASIGNADAS ===")
        
        # Verificar datos en la base de datos
        tecnico = Usuario.query.filter_by(nombre='Juan', apellido='Pérez', rol='tecnico').first()
        if not tecnico:
            print("❌ Técnico no encontrado")
            return
            
        print(f"✅ Técnico: {tecnico.nombre} {tecnico.apellido} (ID: {tecnico.id})")
        
        # Verificar ubicación del técnico
        ubicacion_tecnico = Ubicacion.query.filter_by(usuario_id=tecnico.id).first()
        if ubicacion_tecnico:
            print(f"📍 Ubicación técnico: {ubicacion_tecnico.latitud}, {ubicacion_tecnico.longitud}")
        else:
            print("❌ Técnico sin ubicación")
            return
            
        # Verificar servicios activos
        servicios_activos = Servicio.query.filter(
            Servicio.estado_servicio.in_(['aceptado', 'en_ruta', 'en_sitio'])
        ).all()
        
        print(f"📊 Servicios activos: {len(servicios_activos)}")
        
        for servicio in servicios_activos:
            solicitud = Solicitud.query.get(servicio.solicitud_id)
            if solicitud and solicitud.tecnico_id == tecnico.id:
                print(f"✅ Servicio #{servicio.id} asignado al técnico")
                print(f"   Estado: {servicio.estado_servicio}")
                print(f"   Móvil ID: {servicio.movil_id}")
                
                # Verificar móvil
                movil = Usuario.query.get(servicio.movil_id)
                if movil:
                    print(f"   Móvil: {movil.nombre} {movil.apellido}")
                    
                    # Verificar ubicación de la móvil
                    ubicacion_movil = Ubicacion.query.filter_by(usuario_id=movil.id).first()
                    if ubicacion_movil:
                        print(f"   📍 Ubicación móvil: {ubicacion_movil.latitud}, {ubicacion_movil.longitud}")
                    else:
                        print(f"   ❌ Móvil sin ubicación")
        
        print("\n=== SIMULANDO LLAMADA A LA API ===")
        
        # Simular request context
        with app.test_request_context(
            f'/tecnico/api/moviles-asignadas?lat={ubicacion_tecnico.latitud}&lng={ubicacion_tecnico.longitud}',
            method='GET'
        ):
            from flask_login import login_user
            from app.blueprints.tecnico.routes import api_moviles_asignadas
            
            # Simular login
            login_user(tecnico)
            
            try:
                # Llamar a la función directamente
                response = api_moviles_asignadas()
                
                # Obtener datos de la respuesta
                if hasattr(response, 'get_json'):
                    data = response.get_json()
                    print(f"✅ API ejecutada exitosamente")
                    print(f"📊 Datos recibidos: {json.dumps(data, indent=2, default=str)}")
                    
                    moviles_asignadas = data.get('moviles_asignadas', [])
                    print(f"\n📱 Total móviles asignadas: {len(moviles_asignadas)}")
                    
                    if moviles_asignadas:
                        for i, movil in enumerate(moviles_asignadas, 1):
                            print(f"\n🚗 Móvil {i}:")
                            print(f"   Nombre: {movil.get('nombre', 'N/A')}")
                            print(f"   Estado: {movil.get('estado_texto', 'N/A')}")
                            print(f"   Distancia: {movil.get('distancia_km', 'N/A')} km")
                            print(f"   Tipo apoyo: {movil.get('tipo_apoyo', 'N/A')}")
                            print(f"   Coordenadas: {movil.get('coordenadas', 'N/A')}")
                    else:
                        print("❌ No se encontraron móviles asignadas")
                        print("\n🔍 Posibles causas:")
                        print("   - No hay servicios aceptados para este técnico")
                        print("   - Las móviles no tienen ubicación actualizada")
                        print("   - Error en la consulta de la base de datos")
                        
                elif hasattr(response, 'data'):
                    # Decodificar datos JSON manualmente
                    try:
                        data_str = response.data.decode('utf-8')
                        data = json.loads(data_str)
                        print(f"✅ API ejecutada exitosamente")
                        print(f"📊 Datos recibidos: {json.dumps(data, indent=2, default=str)}")
                        
                        moviles_asignadas = data.get('moviles_asignadas', [])
                        print(f"\n📱 Total móviles asignadas: {len(moviles_asignadas)}")
                        
                        if moviles_asignadas:
                            for i, movil in enumerate(moviles_asignadas, 1):
                                print(f"\n🚗 Móvil {i}:")
                                print(f"   Nombre: {movil.get('nombre', 'N/A')}")
                                print(f"   Estado: {movil.get('estado_texto', 'N/A')}")
                                print(f"   Distancia: {movil.get('distancia_km', 'N/A')} km")
                                print(f"   Tipo apoyo: {movil.get('tipo_apoyo', 'N/A')}")
                                print(f"   Coordenadas: {movil.get('coordenadas', 'N/A')}")
                        else:
                            print("❌ No se encontraron móviles asignadas en la respuesta")
                    except json.JSONDecodeError:
                        print(f"✅ Respuesta raw: {response.data}")
                else:
                    print(f"✅ Respuesta: {response}")
                    
            except Exception as e:
                print(f"❌ Error ejecutando API: {e}")
                import traceback
                traceback.print_exc()

if __name__ == '__main__':
    test_api_moviles_asignadas()