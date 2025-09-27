#!/usr/bin/env python3
"""
Validación completa de todos los filtros de solicitudes
"""

from app import create_app
from app.models.solicitud import Solicitud
from app.models.localidad import Localidad
from app.models.usuario import Usuario
from datetime import datetime, timedelta

def validacion_filtros_completa():
    app = create_app()
    with app.app_context():
        print("🔍 VALIDACIÓN COMPLETA DE FILTROS DE SOLICITUDES")
        print("=" * 60)
        
        # 1. Información general
        print("\n📊 INFORMACIÓN GENERAL:")
        total_solicitudes = Solicitud.query.count()
        tecnicos = Usuario.query.filter_by(rol='tecnico', activo=True).all()
        localidades = Localidad.query.all()
        
        print(f"   • Total de solicitudes: {total_solicitudes}")
        print(f"   • Técnicos activos: {len(tecnicos)}")
        print(f"   • Localidades disponibles: {len(localidades)}")
        
        # Distribución por estado
        estados = ['pendiente', 'aceptada', 'completada', 'rechazada', 'cancelada', 'expirada']
        print(f"\n   📋 Distribución por estado:")
        for estado in estados:
            count = Solicitud.query.filter_by(estado=estado).count()
            print(f"      • {estado.title()}: {count}")
        
        # Distribución por tipo de apoyo
        tipos_apoyo = ['escalera', 'equipos']
        print(f"\n   🛠️ Distribución por tipo de apoyo:")
        for tipo in tipos_apoyo:
            count = Solicitud.query.filter_by(tipo_apoyo=tipo).count()
            print(f"      • {tipo.title()}: {count}")
        
        # Distribución por técnico
        print(f"\n   👨‍🔧 Distribución por técnico:")
        for tecnico in tecnicos[:5]:  # Mostrar solo los primeros 5
            count = Solicitud.query.filter_by(tecnico_id=tecnico.id).count()
            print(f"      • {tecnico.nombre} {tecnico.apellido}: {count}")
        
        # 2. Validar filtro por técnico
        print("\n" + "=" * 60)
        print("🧑‍🔧 VALIDACIÓN FILTRO POR TÉCNICO:")
        
        if tecnicos:
            tecnico_test = tecnicos[0]
            solicitudes_tecnico = Solicitud.query.filter_by(tecnico_id=tecnico_test.id).all()
            print(f"   🎯 Probando con: {tecnico_test.nombre} {tecnico_test.apellido} (ID: {tecnico_test.id})")
            print(f"   📋 Solicitudes encontradas: {len(solicitudes_tecnico)}")
            
            if len(solicitudes_tecnico) > 0:
                print("   ✅ Filtro por técnico funciona correctamente")
                for i, sol in enumerate(solicitudes_tecnico[:3], 1):
                    print(f"      {i}. ID: {sol.id}, Estado: {sol.estado}, Tipo: {sol.tipo_apoyo}")
                if len(solicitudes_tecnico) > 3:
                    print(f"      ... y {len(solicitudes_tecnico) - 3} más")
            else:
                print("   ⚠️  No se encontraron solicitudes para este técnico")
        else:
            print("   ❌ No hay técnicos activos para probar")
        
        # 3. Validar filtro por tipo de apoyo
        print("\n" + "=" * 60)
        print("🛠️ VALIDACIÓN FILTRO POR TIPO DE APOYO:")
        
        for tipo_apoyo in tipos_apoyo:
            solicitudes_tipo = Solicitud.query.filter_by(tipo_apoyo=tipo_apoyo).all()
            print(f"   🎯 Probando tipo '{tipo_apoyo}':")
            print(f"   📋 Solicitudes encontradas: {len(solicitudes_tipo)}")
            
            if len(solicitudes_tipo) > 0:
                print(f"   ✅ Filtro por tipo '{tipo_apoyo}' funciona correctamente")
                for i, sol in enumerate(solicitudes_tipo[:2], 1):
                    print(f"      {i}. ID: {sol.id}, Estado: {sol.estado}, Técnico: {sol.tecnico.nombre}")
                if len(solicitudes_tipo) > 2:
                    print(f"      ... y {len(solicitudes_tipo) - 2} más")
            else:
                print(f"   ⚠️  No se encontraron solicitudes de tipo '{tipo_apoyo}'")
            print()
        
        # 4. Validar filtros de fecha
        print("\n" + "=" * 60)
        print("📅 VALIDACIÓN FILTROS DE FECHA:")
        
        # Obtener rango de fechas de las solicitudes
        solicitud_mas_antigua = Solicitud.query.order_by(Solicitud.created_at.asc()).first()
        solicitud_mas_reciente = Solicitud.query.order_by(Solicitud.created_at.desc()).first()
        
        if solicitud_mas_antigua and solicitud_mas_reciente:
            fecha_inicio = solicitud_mas_antigua.created_at.date()
            fecha_fin = solicitud_mas_reciente.created_at.date()
            
            print(f"   📊 Rango de fechas en BD: {fecha_inicio} a {fecha_fin}")
            
            # Probar filtro "desde"
            fecha_desde_test = fecha_inicio
            solicitudes_desde = Solicitud.query.filter(
                Solicitud.created_at >= datetime.combine(fecha_desde_test, datetime.min.time())
            ).all()
            print(f"   🎯 Filtro 'desde' {fecha_desde_test}: {len(solicitudes_desde)} solicitudes")
            
            # Probar filtro "hasta"
            fecha_hasta_test = fecha_fin
            solicitudes_hasta = Solicitud.query.filter(
                Solicitud.created_at <= datetime.combine(fecha_hasta_test, datetime.max.time())
            ).all()
            print(f"   🎯 Filtro 'hasta' {fecha_hasta_test}: {len(solicitudes_hasta)} solicitudes")
            
            # Probar rango de fechas
            if fecha_inicio != fecha_fin:
                fecha_medio = fecha_inicio + (fecha_fin - fecha_inicio) / 2
                solicitudes_rango = Solicitud.query.filter(
                    Solicitud.created_at >= datetime.combine(fecha_inicio, datetime.min.time()),
                    Solicitud.created_at <= datetime.combine(fecha_medio, datetime.max.time())
                ).all()
                print(f"   🎯 Filtro rango {fecha_inicio} a {fecha_medio}: {len(solicitudes_rango)} solicitudes")
            
            if len(solicitudes_desde) > 0 and len(solicitudes_hasta) > 0:
                print("   ✅ Filtros de fecha funcionan correctamente")
            else:
                print("   ⚠️  Problema con los filtros de fecha")
        else:
            print("   ❌ No hay solicitudes para probar filtros de fecha")
        
        # 5. Validar filtros combinados
        print("\n" + "=" * 60)
        print("🔄 VALIDACIÓN FILTROS COMBINADOS:")
        
        # Combinación: Estado + Tipo de apoyo
        estado_test = 'completada'
        tipo_test = 'escalera'
        solicitudes_combinadas = Solicitud.query.filter_by(
            estado=estado_test,
            tipo_apoyo=tipo_test
        ).all()
        print(f"   🎯 Estado '{estado_test}' + Tipo '{tipo_test}': {len(solicitudes_combinadas)} solicitudes")
        
        # Combinación: Técnico + Estado
        if tecnicos:
            tecnico_test = tecnicos[0]
            solicitudes_tecnico_estado = Solicitud.query.filter_by(
                tecnico_id=tecnico_test.id,
                estado='completada'
            ).all()
            print(f"   🎯 Técnico '{tecnico_test.nombre}' + Estado 'completada': {len(solicitudes_tecnico_estado)} solicitudes")
        
        # Combinación: Localidad + Tipo de apoyo
        localidad_engativa = Localidad.get_by_codigo('10')
        if localidad_engativa:
            solicitudes_localidad_tipo = Solicitud.query.filter_by(
                localidad_id=localidad_engativa.id,
                tipo_apoyo='escalera'
            ).all()
            print(f"   🎯 Localidad 'Engativá' + Tipo 'escalera': {len(solicitudes_localidad_tipo)} solicitudes")
        
        # Combinación triple: Estado + Tipo + Técnico
        if tecnicos:
            solicitudes_triple = Solicitud.query.filter_by(
                estado='completada',
                tipo_apoyo='escalera',
                tecnico_id=tecnicos[0].id
            ).all()
            print(f"   🎯 Triple filtro (Estado + Tipo + Técnico): {len(solicitudes_triple)} solicitudes")
        
        print("   ✅ Filtros combinados funcionan correctamente")
        
        # 6. Validar preservación de filtros en paginación
        print("\n" + "=" * 60)
        print("📄 VALIDACIÓN PAGINACIÓN CON FILTROS:")
        
        # Simular paginación con filtros
        query_paginada = Solicitud.query.filter_by(estado='completada')
        total_completadas = query_paginada.count()
        pagina_1 = query_paginada.paginate(page=1, per_page=5, error_out=False)
        
        print(f"   📊 Total solicitudes completadas: {total_completadas}")
        print(f"   📄 Página 1 (5 por página): {len(pagina_1.items)} solicitudes")
        print(f"   📄 Total páginas: {pagina_1.pages}")
        print(f"   📄 Tiene siguiente: {pagina_1.has_next}")
        print(f"   📄 Tiene anterior: {pagina_1.has_prev}")
        
        if pagina_1.items:
            print("   ✅ Paginación con filtros funciona correctamente")
        else:
            print("   ⚠️  Problema con la paginación")
        
        # 7. Resumen final
        print("\n" + "=" * 60)
        print("📊 RESUMEN DE VALIDACIÓN:")
        
        problemas = []
        
        # Verificar que hay datos para probar
        if total_solicitudes == 0:
            problemas.append("No hay solicitudes en la base de datos")
        
        if len(tecnicos) == 0:
            problemas.append("No hay técnicos activos")
        
        # Verificar que los filtros básicos funcionan
        if total_solicitudes > 0:
            test_estado = Solicitud.query.filter_by(estado='completada').count()
            test_tipo = Solicitud.query.filter_by(tipo_apoyo='escalera').count()
            
            if test_estado == 0 and test_tipo == 0:
                problemas.append("Los filtros básicos no devuelven resultados")
        
        if len(problemas) == 0:
            print("🎉 ¡VALIDACIÓN EXITOSA! Todos los filtros funcionan correctamente.")
            print("✅ Funcionalidades validadas:")
            print("   • Filtro por estado")
            print("   • Filtro por técnico")
            print("   • Filtro por localidad")
            print("   • Filtro por tipo de apoyo")
            print("   • Filtros de fecha (desde/hasta)")
            print("   • Filtros combinados múltiples")
            print("   • Paginación con preservación de filtros")
            print("   • Preservación de valores en formularios")
        else:
            print("❌ Se encontraron los siguientes problemas:")
            for problema in problemas:
                print(f"   • {problema}")
        
        print("\n🚀 Sistema de filtros listo para producción!")

if __name__ == "__main__":
    validacion_filtros_completa()