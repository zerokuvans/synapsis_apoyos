#!/usr/bin/env python3
from app import create_app
from app.models.solicitud import Solicitud
from app.models.localidad import Localidad

def verificar_solicitudes_localidades():
    app = create_app()
    with app.app_context():
        # Verificar total de solicitudes
        total_solicitudes = Solicitud.query.count()
        print(f"📊 Total de solicitudes en la base de datos: {total_solicitudes}")
        
        if total_solicitudes == 0:
            print("❌ No hay solicitudes en la base de datos para probar el filtro")
            return
        
        # Verificar algunas solicitudes
        solicitudes = Solicitud.query.limit(10).all()
        print(f"\n🔍 Primeras {len(solicitudes)} solicitudes:")
        
        solicitudes_con_localidad = 0
        for solicitud in solicitudes:
            localidad_id = getattr(solicitud, 'localidad_id', None)
            if localidad_id:
                solicitudes_con_localidad += 1
                localidad = Localidad.query.get(localidad_id)
                localidad_nombre = localidad.nombre if localidad else "Localidad no encontrada"
            else:
                localidad_nombre = "Sin localidad asignada"
            
            print(f"  • ID: {solicitud.id}, Estado: {solicitud.estado}, Localidad: {localidad_nombre}")
        
        print(f"\n📍 Solicitudes con localidad asignada: {solicitudes_con_localidad}/{len(solicitudes)}")
        
        # Verificar localidades disponibles
        localidades = Localidad.get_all_active()
        print(f"🏘️ Localidades disponibles: {len(localidades)}")
        
        # Probar filtro por localidad específica
        if localidades:
            primera_localidad = localidades[0]
            solicitudes_filtradas = Solicitud.query.filter_by(localidad_id=primera_localidad.id).all()
            print(f"🔎 Solicitudes en {primera_localidad.nombre}: {len(solicitudes_filtradas)}")

if __name__ == "__main__":
    verificar_solicitudes_localidades()