#!/usr/bin/env python3
"""
Script para probar el filtro de localidades corregido
"""

from app import create_app
from app.models.solicitud import Solicitud
from app.models.localidad import Localidad

def test_filtro_corregido():
    app = create_app()
    with app.app_context():
        print("🧪 Probando filtro de localidades corregido...")
        
        # Obtener todas las solicitudes
        todas_solicitudes = Solicitud.query.all()
        print(f"📊 Total de solicitudes: {len(todas_solicitudes)}")
        
        # Mostrar distribución por localidad
        print("\n📍 Distribución de solicitudes por localidad:")
        localidades = Localidad.get_all_active()
        
        for localidad in localidades:
            solicitudes_en_localidad = Solicitud.query.filter_by(localidad_id=localidad.id).all()
            if len(solicitudes_en_localidad) > 0:
                print(f"   • {localidad.codigo} - {localidad.nombre}: {len(solicitudes_en_localidad)} solicitudes")
                for sol in solicitudes_en_localidad:
                    print(f"     - ID: {sol.id}, Estado: {sol.estado}, Tipo: {sol.tipo_apoyo}")
        
        # Probar filtro específico para Engativá (código 10)
        print(f"\n🔍 Probando filtro para Engativá (código 10):")
        localidad_engativa = Localidad.get_by_codigo('10')
        
        if localidad_engativa:
            print(f"   ✓ Localidad encontrada: {localidad_engativa.nombre} (ID: {localidad_engativa.id})")
            
            # Filtrar usando localidad_id (método corregido)
            solicitudes_filtradas = Solicitud.query.filter_by(localidad_id=localidad_engativa.id).all()
            print(f"   📋 Solicitudes encontradas: {len(solicitudes_filtradas)}")
            
            for solicitud in solicitudes_filtradas:
                print(f"     • ID: {solicitud.id}, Estado: {solicitud.estado}, Tipo: {solicitud.tipo_apoyo}")
                print(f"       Localidad ID: {solicitud.localidad_id}, Localidad: {solicitud.localidad.nombre if solicitud.localidad else 'N/A'}")
        else:
            print("   ❌ Localidad Engativá no encontrada")
        
        # Probar filtro combinado (estado + localidad)
        print(f"\n🔍 Probando filtro combinado (completadas + Engativá):")
        if localidad_engativa:
            solicitudes_combinadas = Solicitud.query.filter_by(
                localidad_id=localidad_engativa.id,
                estado='completada'
            ).all()
            print(f"   📋 Solicitudes completadas en Engativá: {len(solicitudes_combinadas)}")
            
            for solicitud in solicitudes_combinadas:
                print(f"     • ID: {solicitud.id}, Estado: {solicitud.estado}, Tipo: {solicitud.tipo_apoyo}")
        
        print("\n✅ Prueba del filtro corregido completada!")

if __name__ == "__main__":
    test_filtro_corregido()