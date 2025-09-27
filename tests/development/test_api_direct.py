#!/usr/bin/env python3
"""
Script para probar directamente la API del líder desde el contexto de la aplicación
"""

import os
import sys
from datetime import datetime, timedelta

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.usuario import Usuario
from app.models.ubicacion import Ubicacion
from app.models.servicio import Servicio
from sqlalchemy import text

def test_api_direct():
    """Probar directamente la lógica de la API del líder"""
    app = create_app()
    
    with app.app_context():
        print("=== PROBANDO LÓGICA DE API DEL LÍDER DIRECTAMENTE ===")
        print(f"Fecha/Hora: {datetime.now()}")
        print()
        
        try:
            # Simular la lógica de la API de móviles en tiempo real
            print("1. Consultando móviles con sesiones activas...")
            
            # Consultar móviles con sesiones activas (últimos 30 minutos)
            tiempo_limite = datetime.utcnow() - timedelta(minutes=30)
            print(f"Tiempo límite: {tiempo_limite}")
            
            # Obtener usuarios móviles con actividad reciente
            moviles_query = db.session.query(Usuario, Ubicacion).join(
                Ubicacion, Usuario.id == Ubicacion.usuario_id
            ).filter(
                Usuario.rol == 'movil',
                Usuario.activo == True,
                Usuario.last_activity >= tiempo_limite,
                Ubicacion.activa == True
            ).all()
            
            print(f"Móviles encontradas: {len(moviles_query)}")
            
            moviles = []
            for usuario, ubicacion in moviles_query:
                print(f"\n- Procesando: {usuario.nombre} {usuario.apellido}")
                print(f"  ID: {usuario.id}")
                print(f"  Email: {usuario.email}")
                print(f"  Activo: {usuario.activo}")
                print(f"  Last activity: {usuario.last_activity}")
                print(f"  Ubicación: ({ubicacion.latitud}, {ubicacion.longitud})")
                print(f"  Ubicación activa: {ubicacion.activa}")
                print(f"  Timestamp ubicación: {ubicacion.timestamp}")
                
                # Determinar estado de la móvil
                servicio_activo = Servicio.query.filter(
                    Servicio.movil_id == usuario.id,
                    Servicio.estado_servicio.in_(['aceptado', 'en_ruta', 'en_sitio'])
                ).first()
                
                if servicio_activo:
                    estado = 'ocupada'
                    estado_color = '#dc3545'  # rojo
                    estado_texto = f'En servicio ({servicio_activo.estado_servicio})'
                    servicio_actual = f'Servicio #{servicio_activo.id}'
                    print(f"  Estado: {estado_texto}")
                else:
                    estado = 'disponible'
                    estado_color = '#28a745'  # verde
                    estado_texto = 'Disponible'
                    servicio_actual = None
                    print(f"  Estado: {estado_texto}")
                
                movil_data = {
                    'id': usuario.id,
                    'nombre': usuario.get_nombre_completo(),
                    'coordenadas': {
                        'lat': float(ubicacion.latitud),
                        'lng': float(ubicacion.longitud)
                    },
                    'estado': estado,
                    'estado_color': estado_color,
                    'estado_texto': estado_texto,
                    'telefono': usuario.telefono or 'No disponible',
                    'velocidad_kmh': 0,  # Campo no disponible en el modelo
                    'direccion_movimiento': 0,  # Campo no disponible en el modelo
                    'servicio_actual': servicio_actual,
                    'ultima_actualizacion': ubicacion.timestamp.strftime('%H:%M:%S')
                }
                
                moviles.append(movil_data)
            
            print(f"\n📱 Total móviles activas procesadas: {len(moviles)}")
            
            # Mostrar resultado final
            resultado = {
                'success': True,
                'moviles': moviles
            }
            
            print("\n=== RESULTADO FINAL ===")
            import json
            print(json.dumps(resultado, indent=2, ensure_ascii=False, default=str))
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    test_api_direct()