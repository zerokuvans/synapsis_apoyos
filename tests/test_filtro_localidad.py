#!/usr/bin/env python3
"""
Script para probar el filtro por localidad en las solicitudes
"""

from app import create_app
from app.models.solicitud import Solicitud
from app.models.localidad import Localidad

def test_filtro_localidad():
    app = create_app()
    with app.app_context():
        print("🧪 Probando filtro por localidad...")
        
        # Obtener todas las solicitudes
        todas_solicitudes = Solicitud.query.all()
        print(f"📊 Total de solicitudes: {len(todas_solicitudes)}")
        
        # Mostrar solicitudes con sus localidades
        print("\n📍 Solicitudes con localidades asignadas:")
        for solicitud in todas_solicitudes:
            if solicitud.localidad:
                print(f"   • ID: {solicitud.id}, Estado: {solicitud.estado}, Localidad: {solicitud.localidad.codigo} - {solicitud.localidad.nombre}")
            else:
                print(f"   • ID: {solicitud.id}, Estado: {solicitud.estado}, Localidad: Sin asignar")
        
        # Probar filtro por localidad específica (Engativá)
        localidad_engativa = Localidad.query.filter_by(codigo='10').first()
        if localidad_engativa:
            solicitudes_engativa = Solicitud.query.filter_by(localidad_id=localidad_engativa.id).all()
            print(f"\n🔍 Solicitudes en {localidad_engativa.nombre}: {len(solicitudes_engativa)}")
            for solicitud in solicitudes_engativa:
                print(f"   • ID: {solicitud.id}, Estado: {solicitud.estado}, Tipo: {solicitud.tipo_apoyo}")
        
        # Probar filtro por estado y localidad
        solicitudes_completadas_engativa = Solicitud.query.filter_by(
            localidad_id=localidad_engativa.id,
            estado='completada'
        ).all()
        print(f"\n✅ Solicitudes completadas en {localidad_engativa.nombre}: {len(solicitudes_completadas_engativa)}")
        
        # Probar el método to_dict con localidad
        if solicitudes_completadas_engativa:
            solicitud_ejemplo = solicitudes_completadas_engativa[0]
            dict_solicitud = solicitud_ejemplo.to_dict()
            print(f"\n📋 Ejemplo de solicitud con localidad (ID {solicitud_ejemplo.id}):")
            print(f"   • Localidad ID: {dict_solicitud.get('localidad_id')}")
            print(f"   • Localidad Nombre: {dict_solicitud.get('localidad_nombre')}")
            print(f"   • Localidad Código: {dict_solicitud.get('localidad_codigo')}")
        
        # Verificar que todas las localidades están disponibles
        localidades = Localidad.get_all_active()
        print(f"\n🏘️ Localidades disponibles para filtro: {len(localidades)}")
        for localidad in localidades[:5]:  # Mostrar solo las primeras 5
            solicitudes_en_localidad = Solicitud.query.filter_by(localidad_id=localidad.id).count()
            print(f"   • {localidad.codigo} - {localidad.nombre}: {solicitudes_en_localidad} solicitudes")
        
        print("\n✅ Prueba del filtro por localidad completada exitosamente!")

if __name__ == "__main__":
    test_filtro_localidad()