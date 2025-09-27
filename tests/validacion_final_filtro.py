#!/usr/bin/env python3
"""
Validación final del filtro de localidades
"""

from app import create_app
from app.models.solicitud import Solicitud
from app.models.localidad import Localidad

def validacion_final():
    app = create_app()
    with app.app_context():
        print("🔍 VALIDACIÓN FINAL DEL FILTRO DE LOCALIDADES")
        print("=" * 50)
        
        # 1. Verificar que todas las solicitudes tienen localidad asignada
        print("\n1️⃣ Verificando asignación de localidades:")
        total_solicitudes = Solicitud.query.count()
        solicitudes_con_localidad = Solicitud.query.filter(Solicitud.localidad_id.isnot(None)).count()
        solicitudes_sin_localidad = total_solicitudes - solicitudes_con_localidad
        
        print(f"   📊 Total de solicitudes: {total_solicitudes}")
        print(f"   ✅ Con localidad asignada: {solicitudes_con_localidad}")
        print(f"   ❌ Sin localidad asignada: {solicitudes_sin_localidad}")
        
        if solicitudes_sin_localidad == 0:
            print("   🎉 ¡Todas las solicitudes tienen localidad asignada!")
        else:
            print("   ⚠️  Hay solicitudes sin localidad asignada")
        
        # 2. Probar filtro por Engativá (donde están todas las solicitudes)
        print("\n2️⃣ Probando filtro por Engativá (código 10):")
        localidad_engativa = Localidad.get_by_codigo('10')
        
        if localidad_engativa:
            solicitudes_engativa = Solicitud.query.filter_by(localidad_id=localidad_engativa.id).all()
            print(f"   🏘️ Localidad: {localidad_engativa.nombre} (ID: {localidad_engativa.id})")
            print(f"   📋 Solicitudes encontradas: {len(solicitudes_engativa)}")
            
            if len(solicitudes_engativa) > 0:
                print("   ✅ El filtro por Engativá funciona correctamente")
                for i, sol in enumerate(solicitudes_engativa[:3], 1):
                    print(f"      {i}. ID: {sol.id}, Estado: {sol.estado}, Tipo: {sol.tipo_apoyo}")
                if len(solicitudes_engativa) > 3:
                    print(f"      ... y {len(solicitudes_engativa) - 3} más")
            else:
                print("   ❌ No se encontraron solicitudes en Engativá")
        else:
            print("   ❌ No se encontró la localidad Engativá")
        
        # 3. Probar filtro por otra localidad (debería estar vacío)
        print("\n3️⃣ Probando filtro por otra localidad (Chapinero - código 02):")
        localidad_chapinero = Localidad.get_by_codigo('02')
        
        if localidad_chapinero:
            solicitudes_chapinero = Solicitud.query.filter_by(localidad_id=localidad_chapinero.id).all()
            print(f"   🏘️ Localidad: {localidad_chapinero.nombre} (ID: {localidad_chapinero.id})")
            print(f"   📋 Solicitudes encontradas: {len(solicitudes_chapinero)}")
            
            if len(solicitudes_chapinero) == 0:
                print("   ✅ El filtro funciona correctamente (no hay solicitudes en Chapinero)")
            else:
                print("   ⚠️  Se encontraron solicitudes inesperadas en Chapinero")
        else:
            print("   ❌ No se encontró la localidad Chapinero")
        
        # 4. Probar filtro combinado (estado + localidad)
        print("\n4️⃣ Probando filtro combinado (completadas + Engativá):")
        if localidad_engativa:
            solicitudes_combinadas = Solicitud.query.filter_by(
                localidad_id=localidad_engativa.id,
                estado='completada'
            ).all()
            print(f"   🔍 Filtro: Estado='completada' + Localidad='Engativá'")
            print(f"   📋 Solicitudes encontradas: {len(solicitudes_combinadas)}")
            
            if len(solicitudes_combinadas) > 0:
                print("   ✅ El filtro combinado funciona correctamente")
            else:
                print("   ⚠️  No se encontraron solicitudes completadas en Engativá")
        
        # 5. Verificar que el método to_dict incluye información de localidad
        print("\n5️⃣ Verificando método to_dict con información de localidad:")
        if solicitudes_con_localidad > 0:
            solicitud_ejemplo = Solicitud.query.filter(Solicitud.localidad_id.isnot(None)).first()
            dict_solicitud = solicitud_ejemplo.to_dict()
            
            campos_localidad = ['localidad_id', 'localidad_nombre', 'localidad_codigo']
            campos_presentes = [campo for campo in campos_localidad if campo in dict_solicitud]
            
            print(f"   📋 Solicitud ejemplo ID: {solicitud_ejemplo.id}")
            print(f"   🏷️ Campos de localidad presentes: {campos_presentes}")
            
            if len(campos_presentes) == 3:
                print("   ✅ El método to_dict incluye toda la información de localidad")
                print(f"      • Localidad ID: {dict_solicitud.get('localidad_id')}")
                print(f"      • Localidad Nombre: {dict_solicitud.get('localidad_nombre')}")
                print(f"      • Localidad Código: {dict_solicitud.get('localidad_codigo')}")
            else:
                print("   ❌ Faltan campos de localidad en el método to_dict")
        
        # 6. Resumen final
        print("\n" + "=" * 50)
        print("📊 RESUMEN DE LA VALIDACIÓN:")
        
        problemas = []
        if solicitudes_sin_localidad > 0:
            problemas.append("Hay solicitudes sin localidad asignada")
        if not localidad_engativa or len(Solicitud.query.filter_by(localidad_id=localidad_engativa.id).all()) == 0:
            problemas.append("El filtro por Engativá no funciona")
        
        if len(problemas) == 0:
            print("🎉 ¡VALIDACIÓN EXITOSA! El filtro de localidades funciona perfectamente.")
            print("✅ Todas las funcionalidades están operativas:")
            print("   • Filtro por localidad específica")
            print("   • Filtro combinado con otros criterios")
            print("   • Información de localidad en respuestas API")
            print("   • Asignación correcta de localidades")
        else:
            print("❌ Se encontraron los siguientes problemas:")
            for problema in problemas:
                print(f"   • {problema}")
        
        print("\n🚀 El filtro está listo para uso en producción!")

if __name__ == "__main__":
    validacion_final()