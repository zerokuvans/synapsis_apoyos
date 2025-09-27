from app import create_app
from app.models.servicio import Servicio
from app.models.solicitud import Solicitud
from app.models.usuario import Usuario
from app.models.ubicacion import Ubicacion
from datetime import datetime, timedelta

def verificar_servicios_aceptados():
    """Verificar servicios aceptados y ubicaciones de móviles"""
    app = create_app()
    
    with app.app_context():
        print("=== VERIFICACIÓN DE SERVICIOS ACEPTADOS ===")
        
        # 1. Buscar servicios con estado 'aceptado', 'en_ruta', 'en_sitio'
        servicios_activos = Servicio.query.filter(
            Servicio.estado_servicio.in_(['aceptado', 'en_ruta', 'en_sitio'])
        ).all()
        
        print(f"\n📊 Total de servicios activos: {len(servicios_activos)}")
        
        if not servicios_activos:
            print("❌ No hay servicios activos (aceptado, en_ruta, en_sitio)")
            
            # Verificar si hay servicios en general
            todos_servicios = Servicio.query.all()
            print(f"📋 Total de servicios en BD: {len(todos_servicios)}")
            
            if todos_servicios:
                print("\n🔍 Estados de servicios existentes:")
                for servicio in todos_servicios[-5:]:  # Últimos 5
                    print(f"  - Servicio #{servicio.id}: {servicio.estado_servicio} (Móvil: {servicio.movil_id})")
        else:
            print("\n✅ Servicios activos encontrados:")
            for servicio in servicios_activos:
                print(f"\n🚗 Servicio #{servicio.id}:")
                print(f"   Estado: {servicio.estado_servicio}")
                print(f"   Móvil ID: {servicio.movil_id}")
                print(f"   Solicitud ID: {servicio.solicitud_id}")
                print(f"   Aceptado: {servicio.aceptado_at}")
                
                # Verificar móvil
                movil = Usuario.query.get(servicio.movil_id)
                if movil:
                    print(f"   Móvil: {movil.nombre} {movil.apellido}")
                    
                    # Verificar ubicación de la móvil
                    ubicacion = Ubicacion.query.filter_by(usuario_id=movil.id).first()
                    if ubicacion:
                        tiempo_desde_actualizacion = datetime.utcnow() - ubicacion.timestamp
                        print(f"   📍 Ubicación: {ubicacion.latitud}, {ubicacion.longitud}")
                        print(f"   🕒 Última actualización: {ubicacion.timestamp} ({tiempo_desde_actualizacion} atrás)")
                        
                        if tiempo_desde_actualizacion > timedelta(minutes=30):
                            print(f"   ⚠️  UBICACIÓN DESACTUALIZADA (más de 30 min)")
                        else:
                            print(f"   ✅ Ubicación actualizada")
                    else:
                        print(f"   ❌ NO TIENE UBICACIÓN REGISTRADA")
                        
                # Verificar técnico
                solicitud = Solicitud.query.get(servicio.solicitud_id)
                if solicitud:
                    tecnico = Usuario.query.get(solicitud.tecnico_id)
                    if tecnico:
                        print(f"   👨‍🔧 Técnico: {tecnico.nombre} {tecnico.apellido}")
                        
                        # Verificar ubicación del técnico
                        ubicacion_tecnico = Ubicacion.query.filter_by(usuario_id=tecnico.id).first()
                        if ubicacion_tecnico:
                            print(f"   📍 Ubicación técnico: {ubicacion_tecnico.latitud}, {ubicacion_tecnico.longitud}")
                        else:
                            print(f"   ❌ Técnico sin ubicación")
        
        print("\n=== VERIFICACIÓN DE TÉCNICOS ACTIVOS ===")
        tecnicos = Usuario.query.filter_by(rol='tecnico').all()
        print(f"📊 Total técnicos: {len(tecnicos)}")
        
        for tecnico in tecnicos:
            ubicacion = Ubicacion.query.filter_by(usuario_id=tecnico.id).first()
            if ubicacion:
                tiempo_desde = datetime.utcnow() - ubicacion.timestamp
                print(f"👨‍🔧 {tecnico.nombre} {tecnico.apellido}: Ubicación actualizada hace {tiempo_desde}")
            else:
                print(f"👨‍🔧 {tecnico.nombre} {tecnico.apellido}: SIN UBICACIÓN")

if __name__ == '__main__':
    verificar_servicios_aceptados()