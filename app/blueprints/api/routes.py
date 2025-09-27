from flask import request, jsonify
from flask_login import login_required, current_user
from app.blueprints.api import api_bp
from app.models.solicitud import Solicitud
from app.models.servicio import Servicio
from app.models.ubicacion import Ubicacion
from app.models.usuario import Usuario
from app.models.localidad import Localidad
from app import db
from datetime import datetime, timedelta
import json

# ============================================================================
# APIs de Solicitudes
# ============================================================================

@api_bp.route('/solicitudes', methods=['POST'])
@login_required
def crear_solicitud():
    """API para crear nueva solicitud de apoyo"""
    try:
        if current_user.rol != 'tecnico':
            return jsonify({
                'success': False,
                'message': 'Solo los técnicos pueden crear solicitudes'
            }), 403
        
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No se recibieron datos'
            }), 400
        
        # Validar campos requeridos
        required_fields = ['tipo_apoyo', 'latitud', 'longitud']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Campo requerido: {field}'
                }), 400
        
        # Validar tipo de apoyo
        if data['tipo_apoyo'] not in ['escalera', 'equipos']:
            return jsonify({
                'success': False,
                'message': 'Tipo de apoyo debe ser "escalera" o "equipos"'
            }), 400
        
        # Verificar solicitudes pendientes
        solicitud_pendiente = Solicitud.query.filter_by(
            tecnico_id=current_user.id,
            estado='pendiente'
        ).first()
        
        if solicitud_pendiente:
            return jsonify({
                'success': False,
                'message': 'Ya tienes una solicitud pendiente'
            }), 409
        
        # Crear solicitud
        solicitud = Solicitud(
            tecnico_id=current_user.id,
            tipo_apoyo=data['tipo_apoyo'],
            latitud=float(data['latitud']),
            longitud=float(data['longitud']),
            observaciones=data.get('observaciones', ''),
            direccion=data.get('direccion', '')
        )
        
        db.session.add(solicitud)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'solicitud_id': solicitud.id,
            'estado': solicitud.estado,
            'tiempo_limite': solicitud.limite_tiempo.isoformat(),
            'message': 'Solicitud creada exitosamente'
        }), 201
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': f'Error en los datos: {str(e)}'
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error interno: {str(e)}'
        }), 500

@api_bp.route('/solicitudes/cercanas', methods=['GET'])
@login_required
def obtener_solicitudes_cercanas():
    """API para obtener solicitudes cercanas (para móviles)"""
    try:
        if current_user.rol != 'movil':
            return jsonify({
                'success': False,
                'message': 'Solo las móviles pueden ver solicitudes cercanas'
            }), 403
        
        # Obtener parámetros
        latitud = request.args.get('latitud', type=float)
        longitud = request.args.get('longitud', type=float)
        radio_km = request.args.get('radio_km', 10, type=int)
        
        if not latitud or not longitud:
            return jsonify({
                'success': False,
                'message': 'Latitud y longitud son requeridas'
            }), 400
        
        # Verificar que no tenga servicios activos
        servicio_activo = Servicio.query.filter_by(
            movil_id=current_user.id
        ).filter(
            Servicio.estado_servicio.in_(['aceptado', 'en_ruta', 'en_sitio'])
        ).first()
        
        if servicio_activo:
            return jsonify({
                'success': False,
                'message': 'Tienes un servicio activo',
                'servicio_activo': servicio_activo.to_dict()
            }), 409
        
        # Buscar solicitudes pendientes
        solicitudes_pendientes = Solicitud.query.filter_by(estado='pendiente').all()
        
        solicitudes_cercanas = []
        ubicacion_movil = Ubicacion(
            usuario_id=current_user.id,
            latitud=latitud,
            longitud=longitud
        )
        
        for solicitud in solicitudes_pendientes:
            if not solicitud.is_expirada():
                distancia = ubicacion_movil.calcular_distancia(
                    solicitud.get_coordenadas()
                )
                
                if distancia <= radio_km:
                    solicitud_data = solicitud.to_dict()
                    solicitud_data['distancia_km'] = round(distancia, 2)
                    solicitudes_cercanas.append(solicitud_data)
        
        # Ordenar por distancia
        solicitudes_cercanas.sort(key=lambda x: x['distancia_km'])
        
        return jsonify({
            'success': True,
            'solicitudes': solicitudes_cercanas,
            'total': len(solicitudes_cercanas)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error interno: {str(e)}'
        }), 500

@api_bp.route('/solicitudes/<int:solicitud_id>/responder', methods=['PUT'])
@login_required
def responder_solicitud(solicitud_id):
    """API para aceptar o rechazar solicitud"""
    try:
        if current_user.rol != 'movil':
            return jsonify({
                'success': False,
                'message': 'Solo las móviles pueden responder solicitudes'
            }), 403
        
        data = request.get_json()
        
        if not data or 'accion' not in data:
            return jsonify({
                'success': False,
                'message': 'Acción requerida (aceptar/rechazar)'
            }), 400
        
        accion = data['accion']
        if accion not in ['aceptar', 'rechazar']:
            return jsonify({
                'success': False,
                'message': 'Acción debe ser "aceptar" o "rechazar"'
            }), 400
        
        solicitud = Solicitud.query.get_or_404(solicitud_id)
        
        if solicitud.estado != 'pendiente':
            return jsonify({
                'success': False,
                'message': 'La solicitud ya no está disponible',
                'nuevo_estado': solicitud.estado
            }), 409
        
        if accion == 'aceptar':
            # Verificar servicios activos
            servicio_activo = Servicio.query.filter_by(
                movil_id=current_user.id
            ).filter(
                Servicio.estado_servicio.in_(['aceptado', 'en_ruta', 'en_sitio'])
            ).first()
            
            if servicio_activo:
                return jsonify({
                    'success': False,
                    'message': 'Ya tienes un servicio activo'
                }), 409
            
            success, message = solicitud.aceptar(current_user.id)
            
        else:  # rechazar
            observaciones = data.get('observaciones', '').strip()
            if not observaciones:
                return jsonify({
                    'success': False,
                    'message': 'Observaciones requeridas para rechazar'
                }), 400
            
            success, message = solicitud.rechazar(observaciones)
        
        if success:
            db.session.commit()
            return jsonify({
                'success': True,
                'nuevo_estado': solicitud.estado,
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 400
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error interno: {str(e)}'
        }), 500

# ============================================================================
# APIs de Ubicación
# ============================================================================

@api_bp.route('/ubicacion', methods=['PUT'])
@login_required
def actualizar_ubicacion():
    """API para actualizar ubicación en tiempo real"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No se recibieron datos'
            }), 400
        
        # Validar campos requeridos
        required_fields = ['latitud', 'longitud']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Campo requerido: {field}'
                }), 400
        
        latitud = float(data['latitud'])
        longitud = float(data['longitud'])
        
        # Desactivar ubicaciones anteriores
        Ubicacion.query.filter_by(
            usuario_id=current_user.id,
            activa=True
        ).update({'activa': False})
        
        # Crear nueva ubicación
        ubicacion = Ubicacion(
            usuario_id=current_user.id,
            latitud=latitud,
            longitud=longitud
        )
        
        db.session.add(ubicacion)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'ubicacion_id': ubicacion.id,
            'timestamp': ubicacion.timestamp.isoformat()
        })
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': f'Coordenadas no válidas: {str(e)}'
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error interno: {str(e)}'
        }), 500

@api_bp.route('/ubicaciones/moviles', methods=['GET'])
@login_required
def obtener_ubicaciones_moviles():
    """API para obtener ubicaciones de móviles (para técnicos y líderes)"""
    try:
        if current_user.rol not in ['tecnico', 'lider']:
            return jsonify({
                'success': False,
                'message': 'No tienes permisos para ver ubicaciones'
            }), 403
        
        # Parámetros opcionales
        latitud = request.args.get('latitud', type=float)
        longitud = request.args.get('longitud', type=float)
        radio_km = request.args.get('radio_km', 20, type=int)
        
        if latitud and longitud:
            # Buscar móviles cercanas
            moviles_cercanas = Ubicacion.obtener_moviles_cercanas(
                latitud, longitud, radio_km
            )
            
            ubicaciones = []
            for item in moviles_cercanas:
                ubicacion_data = item['ubicacion'].to_dict()
                ubicacion_data['distancia_km'] = item['distancia_km']
                ubicacion_data['usuario'] = item['usuario'].to_dict()
                ubicaciones.append(ubicacion_data)
        else:
            # Obtener todas las ubicaciones activas de móviles
            tiempo_limite = datetime.utcnow() - timedelta(minutes=30)
            
            query = db.session.query(Ubicacion, Usuario).join(
                Usuario, Ubicacion.usuario_id == Usuario.id
            ).filter(
                Usuario.rol == 'movil',
                Usuario.activo == True,
                Ubicacion.activa == True,
                Usuario.last_activity >= tiempo_limite
            )
            
            ubicaciones = []
            for ubicacion, usuario in query.all():
                ubicacion_data = ubicacion.to_dict()
                ubicacion_data['usuario'] = usuario.to_dict()
                ubicaciones.append(ubicacion_data)
        
        return jsonify({
            'success': True,
            'ubicaciones': ubicaciones,
            'total': len(ubicaciones)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error interno: {str(e)}'
        }), 500

@api_bp.route('/moviles/cercanas', methods=['GET'])
@login_required
def obtener_moviles_cercanas():
    """API específica para obtener móviles cercanas para el mapa del técnico"""
    try:
        if current_user.rol != 'tecnico':
            return jsonify({
                'success': False,
                'message': 'Solo los técnicos pueden ver móviles cercanas'
            }), 403
        
        # Obtener parámetros
        latitud = request.args.get('lat', type=float)
        longitud = request.args.get('lng', type=float)
        radio_km = request.args.get('radio', 10, type=int)
        
        if not latitud or not longitud:
            return jsonify({
                'success': False,
                'message': 'Latitud y longitud son requeridas'
            }), 400
        
        # Buscar móviles cercanas activas
        tiempo_limite = datetime.utcnow() - timedelta(minutes=30)
        
        # Query para obtener móviles con ubicaciones recientes
        query = db.session.query(Usuario, Ubicacion).select_from(Usuario).join(
            Ubicacion, Usuario.id == Ubicacion.usuario_id
        ).filter(
            Usuario.rol == 'movil',
            Usuario.activo == True,
            Ubicacion.activa == True,
            Usuario.last_activity >= tiempo_limite
        )
        
        moviles_data = []
        ubicacion_tecnico = Ubicacion(
            usuario_id=current_user.id,
            latitud=latitud,
            longitud=longitud
        )
        
        for usuario, ubicacion in query.all():
            # Calcular distancia
            distancia = ubicacion_tecnico.calcular_distancia(
                (ubicacion.latitud, ubicacion.longitud)
            )
            
            if distancia <= radio_km:
                # Verificar si la móvil está disponible
                servicio_activo = Servicio.query.filter_by(
                    movil_id=usuario.id
                ).filter(
                    Servicio.estado_servicio.in_(['aceptado', 'en_ruta', 'en_sitio'])
                ).first()
                
                estado = 'ocupada' if servicio_activo else 'disponible'
                tiempo_estimado = max(5, int(distancia * 2 + (distancia * 0.5)))  # Estimación básica
                
                movil_data = {
                    'id': usuario.id,
                    'nombre': f"{usuario.nombre} {usuario.apellido}",
                    'latitud': float(ubicacion.latitud),
                    'longitud': float(ubicacion.longitud),
                    'distancia': round(distancia, 1),
                    'estado': estado,
                    'tiempoEstimado': tiempo_estimado,
                    'ultimaActualizacion': ubicacion.timestamp.isoformat()
                }
                
                moviles_data.append(movil_data)
        
        # Ordenar por distancia
        moviles_data.sort(key=lambda x: x['distancia'])
        
        return jsonify({
            'success': True,
            'moviles': moviles_data,
            'total': len(moviles_data),
            'disponibles': len([m for m in moviles_data if m['estado'] == 'disponible'])
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error interno: {str(e)}'
        }), 500

# ============================================================================
# APIs de Servicios
# ============================================================================

@api_bp.route('/servicios/activo', methods=['GET'])
@login_required
def obtener_servicio_activo():
    """API para obtener el servicio activo del usuario"""
    try:
        if current_user.rol == 'tecnico':
            # Buscar solicitud aceptada del técnico
            solicitud = Solicitud.query.filter_by(
                tecnico_id=current_user.id,
                estado='aceptada'
            ).first()
            
            if solicitud and solicitud.servicio:
                return jsonify({
                    'success': True,
                    'servicio': solicitud.servicio.to_dict(),
                    'solicitud': solicitud.to_dict()
                })
        
        elif current_user.rol == 'movil':
            # Buscar servicio activo de la móvil
            servicio = Servicio.query.filter_by(
                movil_id=current_user.id
            ).filter(
                Servicio.estado_servicio.in_(['aceptado', 'en_ruta', 'en_sitio'])
            ).first()
            
            if servicio:
                return jsonify({
                    'success': True,
                    'servicio': servicio.to_dict(),
                    'solicitud': servicio.solicitud.to_dict()
                })
        
        return jsonify({
            'success': True,
            'servicio': None,
            'message': 'No hay servicios activos'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error interno: {str(e)}'
        }), 500

@api_bp.route('/servicios/<int:servicio_id>/estado', methods=['PUT'])
@login_required
def actualizar_estado_servicio(servicio_id):
    """API para actualizar el estado del servicio"""
    try:
        if current_user.rol != 'movil':
            return jsonify({
                'success': False,
                'message': 'Solo las móviles pueden actualizar servicios'
            }), 403
        
        data = request.get_json()
        
        if not data or 'accion' not in data:
            return jsonify({
                'success': False,
                'message': 'Acción requerida'
            }), 400
        
        servicio = Servicio.query.filter_by(
            id=servicio_id,
            movil_id=current_user.id
        ).first_or_404()
        
        accion = data['accion']
        
        if accion == 'iniciar_ruta':
            success, message = servicio.iniciar_ruta()
        elif accion == 'llegar_sitio':
            success, message = servicio.llegar_al_sitio()
        elif accion == 'iniciar_servicio':
            success, message = servicio.iniciar_servicio()
        elif accion == 'finalizar':
            observaciones = data.get('observaciones_finales', '')
            success, message = servicio.finalizar_servicio(observaciones)
        elif accion == 'cancelar':
            observaciones = data.get('observaciones', '').strip()
            if not observaciones:
                return jsonify({
                    'success': False,
                    'message': 'Observaciones requeridas para cancelar'
                }), 400
            success, message = servicio.cancelar_servicio(observaciones)
        else:
            return jsonify({
                'success': False,
                'message': 'Acción no válida'
            }), 400
        
        if success:
            db.session.commit()
            return jsonify({
                'success': True,
                'nuevo_estado': servicio.estado_servicio,
                'servicio': servicio.to_dict(),
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 400
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error interno: {str(e)}'
        }), 500

# ============================================================================
# APIs de Estadísticas (para líderes)
# ============================================================================

@api_bp.route('/estadisticas/dashboard', methods=['GET'])
@login_required
def obtener_estadisticas_dashboard():
    """API para obtener estadísticas del dashboard"""
    try:
        if current_user.rol != 'lider':
            return jsonify({
                'success': False,
                'message': 'Solo los líderes pueden ver estadísticas'
            }), 403
        
        hoy = datetime.utcnow().date()
        inicio_mes = datetime(hoy.year, hoy.month, 1)
        
        # Métricas básicas
        # Usar comparación de rango de fechas para SQLite
        inicio_dia = datetime.combine(hoy, datetime.min.time())
        fin_dia = datetime.combine(hoy, datetime.max.time())
        
        estadisticas = {
            'solicitudes_hoy': Solicitud.query.filter(
                Solicitud.created_at.between(inicio_dia, fin_dia)
            ).count(),
            
            'servicios_activos': Servicio.query.filter(
                Servicio.estado_servicio.in_(['aceptado', 'en_ruta', 'en_sitio'])
            ).count(),
            
            'solicitudes_pendientes': Solicitud.query.filter_by(
                estado='pendiente'
            ).count(),
            
            'solicitudes_mes': Solicitud.query.filter(
                Solicitud.created_at >= inicio_mes
            ).count(),
            
            'servicios_completados_mes': Servicio.query.filter(
                Servicio.estado_servicio == 'completado',
                Servicio.finalizado_at >= inicio_mes
            ).count()
        }
        
        # Móviles activas
        tiempo_limite = datetime.utcnow() - timedelta(minutes=30)
        estadisticas['moviles_activas'] = db.session.query(Usuario).filter(
            Usuario.rol == 'movil',
            Usuario.activo == True,
            Usuario.last_activity >= tiempo_limite
        ).count()
        
        return jsonify({
            'success': True,
            'estadisticas': estadisticas
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error interno: {str(e)}'
        }), 500

@api_bp.route('/responder-solicitud', methods=['POST'])
def responder_solicitud_apoyo():
    try:
        data = request.get_json()
        
        # Validar datos requeridos
        if not data or 'solicitud_id' not in data or 'respuesta' not in data:
            return jsonify({
                'success': False,
                'message': 'Datos incompletos. Se requiere solicitud_id y respuesta.'
            }), 400
        
        solicitud_id = data['solicitud_id']
        respuesta = data['respuesta']
        
        # Buscar la solicitud
        solicitud = Solicitud.query.get(solicitud_id)
        if not solicitud:
            return jsonify({
                'success': False,
                'message': 'Solicitud no encontrada.'
            }), 404
        
        # Verificar que la solicitud esté pendiente
        if solicitud.estado != 'pendiente':
            return jsonify({
                'success': False,
                'message': 'La solicitud ya ha sido procesada.'
            }), 400
        
        # Actualizar la solicitud según la respuesta
        if respuesta == 'aceptar':
            solicitud.estado = 'aceptada'
            solicitud.fecha_respuesta = datetime.utcnow()
            
            # Aquí se podría asignar una móvil automáticamente
            # o esperar a que el líder la asigne manualmente
            
            mensaje = 'Solicitud aceptada exitosamente.'
        elif respuesta == 'rechazar':
            solicitud.estado = 'rechazada'
            solicitud.fecha_respuesta = datetime.utcnow()
            mensaje = 'Solicitud rechazada.'
        else:
            return jsonify({
                'success': False,
                'message': 'Respuesta inválida. Use "aceptar" o "rechazar".'
            }), 400
        
        # Guardar cambios
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': mensaje,
            'solicitud': {
                'id': solicitud.id,
                'estado': solicitud.estado,
                'fecha_respuesta': solicitud.fecha_respuesta.isoformat() if solicitud.fecha_respuesta else None
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error procesando la respuesta: {str(e)}'
        }), 500

# Endpoints para el módulo líder - Mapa general
@api_bp.route('/lider/moviles-activas', methods=['GET'])
@login_required
def obtener_moviles_activas():
    """Obtener todas las móviles activas para el mapa general del líder"""
    try:
        moviles = []
        
        # Consultar móviles con sesiones activas (últimos 30 minutos)
        tiempo_limite = datetime.utcnow() - timedelta(minutes=30)
        
        # Obtener usuarios móviles con actividad reciente (sesiones activas)
        from sqlalchemy import text
        moviles_query = db.session.query(Usuario, Ubicacion).join(
            Ubicacion, Usuario.id == Ubicacion.usuario_id
        ).filter(
            Usuario.rol == 'movil',
            Usuario.activo == True,
            Ubicacion.activa == True,
            text('usuarios.last_activity >= :tiempo_limite')
        ).params(tiempo_limite=tiempo_limite).all()
        
        for usuario, ubicacion in moviles_query:
            # Calcular tiempo desde última actualización
            tiempo_transcurrido = datetime.utcnow() - ubicacion.timestamp
            minutos = int(tiempo_transcurrido.total_seconds() / 60)
            
            # Determinar estado basado en servicios activos
            servicios_activos = Servicio.query.filter(
                Servicio.movil_id == usuario.id,
                Servicio.estado_servicio.in_(['en_camino', 'en_sitio'])
            ).count()
            
            estado = 'en_servicio' if servicios_activos > 0 else 'disponible'
            
            moviles.append({
                'id': usuario.id,
                'nombre': usuario.nombre,
                'latitud': float(ubicacion.latitud),
                'longitud': float(ubicacion.longitud),
                'estado': estado,
                'telefono': usuario.telefono or 'No disponible',
                'ultima_actualizacion': f'Hace {minutos} min' if minutos > 0 else 'Ahora'
            })
        
        return jsonify({
            'success': True,
            'moviles': moviles,
            'total': len(moviles)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error obteniendo móviles activas: {str(e)}'
        }), 500

@api_bp.route('/lider/solicitudes-activas', methods=['GET'])
@login_required
def obtener_solicitudes_activas():
    """Obtener todas las solicitudes activas para el mapa general del líder"""
    try:
        solicitudes = []
        
        # Consultar solicitudes pendientes de la base de datos
        try:
            solicitudes_query = Solicitud.query.filter(
                Solicitud.estado.in_(['pendiente', 'aceptada'])
            ).all()
            
            for solicitud in solicitudes_query:
                # Obtener información del técnico
                tecnico = Usuario.query.get(solicitud.tecnico_id)
                
                # Calcular tiempo transcurrido
                tiempo_transcurrido = datetime.utcnow() - solicitud.created_at
                minutos = int(tiempo_transcurrido.total_seconds() / 60)
                
                solicitudes.append({
                    'id': solicitud.id,
                    'tipo_apoyo': solicitud.tipo_apoyo,
                    'latitud': float(solicitud.latitud) if solicitud.latitud else 4.6097,
                    'longitud': float(solicitud.longitud) if solicitud.longitud else -74.0817,
                    'tecnico_nombre': tecnico.nombre if tecnico else 'Técnico',
                    'tiempo_transcurrido': f'{minutos} min',
                    'observaciones': solicitud.observaciones or '',
                    'estado': solicitud.estado
                })
                
        except Exception as db_error:
            # Si hay error en la consulta, retornar lista vacía
            solicitudes = []
        
        return jsonify({
            'success': True,
            'solicitudes': solicitudes,
            'total': len(solicitudes)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error obteniendo solicitudes activas: {str(e)}'
        }), 500

@api_bp.route('/lider/servicios-activos', methods=['GET'])
@login_required
def obtener_servicios_activos():
    """Obtener todos los servicios activos para el mapa general del líder"""
    try:
        servicios = []
        
        # Consultar servicios activos de la base de datos
        servicios_query = Servicio.query.filter(
            Servicio.estado_servicio.in_(['en_camino', 'en_sitio'])
        ).all()
        
        for servicio in servicios_query:
            # Obtener información del móvil y técnico
            movil = Usuario.query.get(servicio.movil_id) if servicio.movil_id else None
            tecnico = Usuario.query.get(servicio.tecnico_id) if servicio.tecnico_id else None
            
            # Calcular tiempo de servicio
            if servicio.iniciado_at:
                tiempo_transcurrido = datetime.utcnow() - servicio.iniciado_at
                minutos = int(tiempo_transcurrido.total_seconds() / 60)
                tiempo_servicio = f'{minutos} min'
            else:
                tiempo_servicio = 'Recién iniciado'
            
            # Obtener ubicación del servicio (de la solicitud original)
            solicitud = Solicitud.query.get(servicio.solicitud_id) if servicio.solicitud_id else None
            
            servicios.append({
                'id': servicio.id,
                'latitud': float(solicitud.latitud) if solicitud and solicitud.latitud else 4.6097,
                'longitud': float(solicitud.longitud) if solicitud and solicitud.longitud else -74.0817,
                'movil_nombre': movil.nombre if movil else 'Móvil no asignado',
                'tecnico_nombre': tecnico.nombre if tecnico else 'Técnico no disponible',
                'tiempo_servicio': tiempo_servicio,
                'estado': servicio.estado_servicio,
                'tipo_apoyo': solicitud.tipo_apoyo if solicitud else 'No especificado'
            })
        
        return jsonify({
            'success': True,
            'servicios': servicios,
            'total': len(servicios)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error obteniendo servicios activos: {str(e)}'
        }), 500

# Endpoints para el módulo técnico - Móviles asignadas
@api_bp.route('/tecnico/moviles-asignadas', methods=['GET'])
@login_required
def obtener_moviles_asignadas():
    """Obtener móviles asignadas a servicios del técnico logueado"""
    try:
        if current_user.rol != 'tecnico':
            return jsonify({
                'success': False,
                'message': 'Solo los técnicos pueden acceder a esta información'
            }), 403
        
        moviles_asignadas = []
        
        # Buscar solicitudes del técnico que tengan servicios activos
        solicitudes_con_servicio = db.session.query(Solicitud, Servicio, Usuario).join(
            Servicio, Solicitud.id == Servicio.solicitud_id
        ).join(
            Usuario, Servicio.movil_id == Usuario.id
        ).filter(
            Solicitud.tecnico_id == current_user.id,
            Servicio.estado_servicio.in_(['en_camino', 'en_sitio'])
        ).all()
        
        for solicitud, servicio, movil in solicitudes_con_servicio:
            # Obtener ubicación actual de la móvil
            ubicacion_movil = Ubicacion.query.filter_by(
                usuario_id=movil.id,
                activa=True
            ).order_by(Ubicacion.timestamp.desc()).first()
            
            if ubicacion_movil:
                # Calcular tiempo desde que inició el servicio
                if servicio.iniciado_at:
                    tiempo_transcurrido = datetime.utcnow() - servicio.iniciado_at
                    minutos = int(tiempo_transcurrido.total_seconds() / 60)
                    tiempo_servicio = f'{minutos} min'
                else:
                    tiempo_servicio = 'Recién iniciado'
                
                # Calcular distancia aproximada entre móvil y técnico
                distancia = 0
                if solicitud.latitud and solicitud.longitud:
                    from math import radians, cos, sin, asin, sqrt
                    
                    def haversine(lon1, lat1, lon2, lat2):
                        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
                        dlon = lon2 - lon1
                        dlat = lat2 - lat1
                        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                        c = 2 * asin(sqrt(a))
                        r = 6371  # Radio de la Tierra en kilómetros
                        return c * r
                    
                    distancia = haversine(
                        float(ubicacion_movil.longitud), float(ubicacion_movil.latitud),
                        float(solicitud.longitud), float(solicitud.latitud)
                    )
                
                moviles_asignadas.append({
                    'id': movil.id,
                    'nombre': movil.nombre,
                    'latitud': float(ubicacion_movil.latitud),
                    'longitud': float(ubicacion_movil.longitud),
                    'estado': servicio.estado_servicio,
                    'telefono': movil.telefono or 'No disponible',
                    'tiempo_servicio': tiempo_servicio,
                    'distancia_km': round(distancia, 2),
                    'solicitud_id': solicitud.id,
                    'tipo_apoyo': solicitud.tipo_apoyo,
                    'ultima_actualizacion': ubicacion_movil.timestamp.strftime('%H:%M')
                })
        
        return jsonify({
            'success': True,
            'moviles': moviles_asignadas,
            'total': len(moviles_asignadas)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error obteniendo móviles asignadas: {str(e)}'
        }), 500

# ============================================================================
# APIs de Localidades y Polígonos
# ============================================================================

@api_bp.route('/localidades', methods=['GET'])
def obtener_localidades():
    """API para obtener todas las localidades activas"""
    try:
        localidades = Localidad.get_all_active()
        
        localidades_data = []
        for localidad in localidades:
            localidades_data.append(localidad.to_dict(include_geometry=False))
        
        return jsonify({
            'success': True,
            'localidades': localidades_data,
            'total': len(localidades_data)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error obteniendo localidades: {str(e)}'
        }), 500

@api_bp.route('/localidades/polygons', methods=['GET'])
def obtener_poligonos_localidades():
    """API para obtener coordenadas de polígonos de todas las localidades"""
    try:
        localidades = Localidad.query.filter(
            Localidad.geometria.isnot(None),
            Localidad.activa == True
        ).all()
        
        polygons_data = []
        for localidad in localidades:
            geojson = localidad.get_geojson(include_properties=True)
            if geojson:
                polygons_data.append(geojson)
        
        return jsonify({
            'success': True,
            'type': 'FeatureCollection',
            'features': polygons_data,
            'total': len(polygons_data)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error obteniendo polígonos: {str(e)}'
        }), 500

@api_bp.route('/localidades/<codigo>/polygon', methods=['GET'])
def obtener_poligono_localidad(codigo):
    """API para obtener el polígono de una localidad específica"""
    try:
        localidad = Localidad.get_by_codigo(codigo)
        
        if not localidad:
            return jsonify({
                'success': False,
                'message': f'Localidad con código {codigo} no encontrada'
            }), 404
        
        geojson = localidad.get_geojson(include_properties=True)
        
        if not geojson:
            return jsonify({
                'success': False,
                'message': 'La localidad no tiene geometría definida'
            }), 404
        
        return jsonify({
            'success': True,
            'localidad': localidad.to_dict(),
            'geometry': geojson
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error obteniendo polígono: {str(e)}'
        }), 500

@api_bp.route('/localidades/detect-by-coordinates', methods=['POST'])
def detectar_localidad_por_coordenadas():
    """API para detectar en qué localidad se encuentra un punto específico"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No se recibieron datos'
            }), 400
        
        # Validar campos requeridos
        if 'latitud' not in data or 'longitud' not in data:
            return jsonify({
                'success': False,
                'message': 'Latitud y longitud son requeridas'
            }), 400
        
        try:
            latitud = float(data['latitud'])
            longitud = float(data['longitud'])
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'message': 'Latitud y longitud deben ser números válidos'
            }), 400
        
        # Buscar localidad que contenga el punto
        localidad = Localidad.find_localidad_by_point(latitud, longitud)
        
        if localidad:
            return jsonify({
                'success': True,
                'localidad': localidad.to_dict(),
                'coordenadas': {
                    'latitud': latitud,
                    'longitud': longitud
                },
                'dentro_de_localidad': True
            })
        else:
            # Si no se encuentra con polígonos precisos, buscar por proximidad
            localidad_cercana = Localidad.get_localidad_por_coordenadas(
                latitud, longitud, radio_km=2.0
            )
            
            if localidad_cercana:
                return jsonify({
                    'success': True,
                    'localidad': localidad_cercana.to_dict(),
                    'coordenadas': {
                        'latitud': latitud,
                        'longitud': longitud
                    },
                    'dentro_de_localidad': False,
                    'localidad_cercana': True,
                    'message': 'Punto fuera de límites, localidad más cercana encontrada'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'No se encontró ninguna localidad para las coordenadas proporcionadas',
                    'coordenadas': {
                        'latitud': latitud,
                        'longitud': longitud
                    }
                }), 404
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error detectando localidad: {str(e)}'
        }), 500

@api_bp.route('/localidades/<codigo>/bounds', methods=['GET'])
def obtener_limites_localidad(codigo):
    """API para obtener los límites (bounding box) de una localidad"""
    try:
        localidad = Localidad.get_by_codigo(codigo)
        
        if not localidad:
            return jsonify({
                'success': False,
                'message': f'Localidad con código {codigo} no encontrada'
            }), 404
        
        bounds = localidad.get_bounds()
        
        if not bounds:
            return jsonify({
                'success': False,
                'message': 'La localidad no tiene geometría definida'
            }), 404
        
        return jsonify({
            'success': True,
            'localidad': localidad.to_dict(),
            'bounds': bounds
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error obteniendo límites: {str(e)}'
        }), 500

@api_bp.route('/solicitudes/por-localidad/<codigo>', methods=['GET'])
@login_required
def obtener_solicitudes_por_localidad(codigo):
    """API para obtener solicitudes filtradas por localidad"""
    try:
        if current_user.rol not in ['lider', 'tecnico']:
            return jsonify({
                'success': False,
                'message': 'No tienes permisos para acceder a esta información'
            }), 403
        
        localidad = Localidad.get_by_codigo(codigo)
        
        if not localidad:
            return jsonify({
                'success': False,
                'message': f'Localidad con código {codigo} no encontrada'
            }), 404
        
        # Obtener todas las solicitudes
        solicitudes = Solicitud.query.filter(
            Solicitud.estado.in_(['pendiente', 'aceptada'])
        ).all()
        
        solicitudes_en_localidad = []
        
        for solicitud in solicitudes:
            if solicitud.latitud and solicitud.longitud:
                # Verificar si la solicitud está dentro de la localidad
                if localidad.contains_point(float(solicitud.latitud), float(solicitud.longitud)):
                    solicitud_data = solicitud.to_dict()
                    
                    # Agregar información del técnico
                    tecnico = Usuario.query.get(solicitud.tecnico_id)
                    if tecnico:
                        solicitud_data['tecnico_nombre'] = tecnico.nombre
                    
                    solicitudes_en_localidad.append(solicitud_data)
        
        return jsonify({
            'success': True,
            'localidad': localidad.to_dict(),
            'solicitudes': solicitudes_en_localidad,
            'total': len(solicitudes_en_localidad)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error obteniendo solicitudes por localidad: {str(e)}'
        }), 500