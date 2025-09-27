#!/usr/bin/env python3
"""
Script para verificar solicitudes y servicios en la base de datos
"""

import os
import sys
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.solicitud import Solicitud
from app.models.servicio import Servicio
from app.models.usuario import Usuario

def check_solicitudes_servicios():
    """Verificar solicitudes y servicios en la base de datos"""
    app = create_app()
    
    with app.app_context():
        print("=== VERIFICACIÓN DE SOLICITUDES Y SERVICIOS ===")
        print(f"Fecha/Hora: {datetime.now()}")
        print()
        
        try:
            # Verificar solicitudes
            print("1. SOLICITUDES:")
            solicitudes = Solicitud.query.all()
            print(f"Total solicitudes: {len(solicitudes)}")
            
            for solicitud in solicitudes:
                tecnico = Usuario.query.get(solicitud.tecnico_id)
                print(f"- ID: {solicitud.id}")
                print(f"  Técnico: {tecnico.get_nombre_completo() if tecnico else 'Desconocido'}")
                print(f"  Estado: {solicitud.estado}")
                print(f"  Tipo: {solicitud.tipo_apoyo}")
                # print(f"  Prioridad: {solicitud.prioridad}")  # Campo no disponible
                print(f"  Coordenadas: ({solicitud.latitud}, {solicitud.longitud})")
                print(f"  Creado: {solicitud.created_at}")
                print()
            
            # Verificar solicitudes activas
            solicitudes_activas = Solicitud.query.filter(
                Solicitud.estado.in_(['pendiente', 'aceptada'])
            ).all()
            print(f"Solicitudes activas (pendiente/aceptada): {len(solicitudes_activas)}")
            print()
            
            # Verificar servicios
            print("2. SERVICIOS:")
            servicios = Servicio.query.all()
            print(f"Total servicios: {len(servicios)}")
            
            for servicio in servicios:
                movil = Usuario.query.get(servicio.movil_id) if servicio.movil_id else None
                solicitud = Solicitud.query.get(servicio.solicitud_id) if servicio.solicitud_id else None
                tecnico = Usuario.query.get(solicitud.tecnico_id) if solicitud and solicitud.tecnico_id else None
                
                print(f"- ID: {servicio.id}")
                print(f"  Móvil: {movil.get_nombre_completo() if movil else 'Desconocido'}")
                print(f"  Técnico: {tecnico.get_nombre_completo() if tecnico else 'Desconocido'}")
                print(f"  Estado: {servicio.estado_servicio}")
                print(f"  Solicitud ID: {servicio.solicitud_id}")
                print(f"  Tipo apoyo: {solicitud.tipo_apoyo if solicitud else 'Desconocido'}")
                print(f"  Aceptado: {servicio.aceptado_at}")
                print(f"  Creado: {servicio.aceptado_at}")
                print()
            
            # Verificar servicios activos
            servicios_activos = Servicio.query.filter(
                Servicio.estado_servicio.in_(['aceptado', 'en_ruta', 'en_sitio'])
            ).all()
            print(f"Servicios activos (aceptado/en_ruta/en_sitio): {len(servicios_activos)}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    check_solicitudes_servicios()