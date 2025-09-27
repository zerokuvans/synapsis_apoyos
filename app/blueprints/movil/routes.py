from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.blueprints.movil import movil_bp
from app.blueprints.auth.routes import role_required
from app.models.solicitud import Solicitud
from app.models.servicio import Servicio
from app.models.ubicacion import Ubicacion
from app.models.usuario import Usuario
from app import db
from datetime import datetime

@movil_bp.route('/dashboard')
@login_required
@role_required('movil')
def dashboard():
    """Dashboard principal de la móvil de apoyo"""
    # Verificar si tiene un servicio activo
    servicio_activo = Servicio.query.filter_by(
        movil_id=current_user.id
    ).filter(
        Servicio.estado_servicio.in_(['aceptado', 'en_ruta', 'en_sitio'])
    ).first()
    
    # Obtener solicitudes cercanas (solo si no tiene servicio activo)
    solicitudes_cercanas = []
    if not servicio_activo:
        # Obtener ubicación actual de la móvil
        ubicacion_actual = current_user.get_ubicacion_actual()
        if ubicacion_actual:
            lat, lon = ubicacion_actual.get_coordenadas()
            
            # Buscar solicitudes pendientes cercanas
            solicitudes_pendientes = Solicitud.query.filter_by(estado='pendiente').all()
            
            for solicitud in solicitudes_pendientes:
                if not solicitud.is_expirada():
                    distancia = ubicacion_actual.calcular_distancia(
                        solicitud.get_coordenadas()
                    )
                    if distancia <= 20:  # 20 km de radio
                        solicitudes_cercanas.append({
                            'solicitud': solicitud,
                            'distancia_km': round(distancia, 2)
                        })
            
            # Ordenar por distancia
            solicitudes_cercanas.sort(key=lambda x: x['distancia_km'])
    
    # Historial reciente
    servicios_recientes = Servicio.query.filter_by(
        movil_id=current_user.id
    ).order_by(Servicio.aceptado_at.desc()).limit(5).all()
    
    return render_template('movil/dashboard.html',
                         servicio_activo=servicio_activo,
                         solicitudes_cercanas=solicitudes_cercanas,
                         servicios_recientes=servicios_recientes)

@movil_bp.route('/solicitud/<int:solicitud_id>/aceptar', methods=['POST'])
@login_required
@role_required('movil')
def aceptar_solicitud(solicitud_id):
    """Aceptar una solicitud de apoyo"""
    try:
        # Verificar que no tenga servicios activos
        servicio_activo = Servicio.query.filter_by(
            movil_id=current_user.id
        ).filter(
            Servicio.estado_servicio.in_(['aceptado', 'en_ruta', 'en_sitio'])
        ).first()
        
        if servicio_activo:
            flash('No puedes aceptar otra solicitud hasta completar la actual', 'warning')
            return redirect(url_for('movil.dashboard'))
        
        # Buscar la solicitud
        solicitud = Solicitud.query.get_or_404(solicitud_id)
        
        if solicitud.estado != 'pendiente':
            flash('Esta solicitud ya no está disponible', 'warning')
            return redirect(url_for('movil.dashboard'))
        
        if solicitud.is_expirada():
            solicitud.marcar_como_expirada()
            db.session.commit()
            flash('Esta solicitud ha expirado', 'warning')
            return redirect(url_for('movil.dashboard'))
        
        # Aceptar la solicitud
        success, message = solicitud.aceptar(current_user.id)
        
        if success:
            db.session.commit()
            flash(f'Solicitud aceptada: {message}', 'success')
        else:
            flash(f'Error: {message}', 'error')
        
        return redirect(url_for('movil.dashboard'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error aceptando solicitud: {str(e)}', 'error')
        return redirect(url_for('movil.dashboard'))

@movil_bp.route('/solicitud/<int:solicitud_id>/rechazar', methods=['POST'])
@login_required
@role_required('movil')
def rechazar_solicitud(solicitud_id):
    """Rechazar una solicitud de apoyo"""
    try:
        solicitud = Solicitud.query.get_or_404(solicitud_id)
        observaciones = request.form.get('observaciones', '').strip()
        
        if not observaciones:
            flash('Las observaciones son obligatorias para rechazar', 'error')
            return redirect(url_for('movil.dashboard'))
        
        if solicitud.estado != 'pendiente':
            flash('Esta solicitud ya no está disponible', 'warning')
            return redirect(url_for('movil.dashboard'))
        
        success, message = solicitud.rechazar(observaciones)
        
        if success:
            db.session.commit()
            flash(f'Solicitud rechazada: {message}', 'info')
        else:
            flash(f'Error: {message}', 'error')
        
        return redirect(url_for('movil.dashboard'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error rechazando solicitud: {str(e)}', 'error')
        return redirect(url_for('movil.dashboard'))

@movil_bp.route('/servicio/<int:servicio_id>/iniciar-ruta', methods=['POST'])
@login_required
@role_required('movil')
def iniciar_ruta(servicio_id):
    """Iniciar ruta hacia el técnico"""
    try:
        servicio = Servicio.query.filter_by(
            id=servicio_id,
            movil_id=current_user.id
        ).first_or_404()
        
        success, message = servicio.iniciar_ruta()
        
        if success:
            db.session.commit()
            flash(message, 'success')
        else:
            flash(message, 'error')
        
        return redirect(url_for('movil.servicio_activo', servicio_id=servicio_id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error iniciando ruta: {str(e)}', 'error')
        return redirect(url_for('movil.dashboard'))

@movil_bp.route('/servicio/<int:servicio_id>/llegar-sitio', methods=['POST'])
@login_required
@role_required('movil')
def llegar_sitio(servicio_id):
    """Marcar llegada al sitio"""
    try:
        servicio = Servicio.query.filter_by(
            id=servicio_id,
            movil_id=current_user.id
        ).first_or_404()
        
        success, message = servicio.llegar_al_sitio()
        
        if success:
            db.session.commit()
            flash(message, 'success')
        else:
            flash(message, 'error')
        
        return redirect(url_for('movil.servicio_activo', servicio_id=servicio_id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error registrando llegada: {str(e)}', 'error')
        return redirect(url_for('movil.dashboard'))

@movil_bp.route('/servicio/<int:servicio_id>/iniciar', methods=['POST'])
@login_required
@role_required('movil')
def iniciar_servicio(servicio_id):
    """Iniciar el servicio de apoyo"""
    try:
        servicio = Servicio.query.filter_by(
            id=servicio_id,
            movil_id=current_user.id
        ).first_or_404()
        
        success, message = servicio.iniciar_servicio()
        
        if success:
            db.session.commit()
            flash(message, 'success')
        else:
            flash(message, 'error')
        
        return redirect(url_for('movil.servicio_activo', servicio_id=servicio_id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error iniciando servicio: {str(e)}', 'error')
        return redirect(url_for('movil.dashboard'))

@movil_bp.route('/servicio/<int:servicio_id>/finalizar', methods=['POST'])
@login_required
@role_required('movil')
def finalizar_servicio(servicio_id):
    """Finalizar el servicio de apoyo"""
    try:
        servicio = Servicio.query.filter_by(
            id=servicio_id,
            movil_id=current_user.id
        ).first_or_404()
        
        observaciones = request.form.get('observaciones_finales', '').strip()
        
        success, message = servicio.finalizar_servicio(observaciones)
        
        if success:
            db.session.commit()
            flash(message, 'success')
            return redirect(url_for('movil.dashboard'))
        else:
            flash(message, 'error')
            return redirect(url_for('movil.servicio_activo', servicio_id=servicio_id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error finalizando servicio: {str(e)}', 'error')
        return redirect(url_for('movil.dashboard'))

@movil_bp.route('/servicio/<int:servicio_id>/cancelar', methods=['POST'])
@login_required
@role_required('movil')
def cancelar_servicio(servicio_id):
    """Cancelar el servicio activo"""
    try:
        servicio = Servicio.query.filter_by(
            id=servicio_id,
            movil_id=current_user.id
        ).first_or_404()
        
        observaciones = request.form.get('observaciones', '').strip()
        
        if not observaciones:
            flash('Las observaciones son obligatorias para cancelar', 'error')
            return redirect(url_for('movil.servicio_activo', servicio_id=servicio_id))
        
        success, message = servicio.cancelar_servicio(observaciones)
        
        if success:
            db.session.commit()
            flash(message, 'info')
            return redirect(url_for('movil.dashboard'))
        else:
            flash(message, 'error')
            return redirect(url_for('movil.servicio_activo', servicio_id=servicio_id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error cancelando servicio: {str(e)}', 'error')
        return redirect(url_for('movil.dashboard'))

@movil_bp.route('/servicio/<int:servicio_id>')
@login_required
@role_required('movil')
def servicio_activo(servicio_id):
    """Vista del servicio activo"""
    servicio = Servicio.query.filter_by(
        id=servicio_id,
        movil_id=current_user.id
    ).first_or_404()
    
    return render_template('movil/servicio_activo.html', servicio=servicio)

@movil_bp.route('/servicio/<int:servicio_id>/detalles')
@login_required
@role_required('movil')
def servicio_detalles(servicio_id):
    """API para obtener detalles completos de un servicio"""
    try:
        servicio = Servicio.query.filter_by(
            id=servicio_id,
            movil_id=current_user.id
        ).first_or_404()
        
        # Preparar datos del servicio
        servicio_data = {
            'id': servicio.id,
            'estado_servicio': servicio.estado_servicio,
            'tipo_apoyo': servicio.solicitud.tipo_apoyo,
            'direccion': servicio.solicitud.direccion,
            'latitud': float(servicio.solicitud.latitud) if servicio.solicitud.latitud else None,
            'longitud': float(servicio.solicitud.longitud) if servicio.solicitud.longitud else None,
            'observaciones_iniciales': servicio.solicitud.observaciones,
            'observaciones_finales': servicio.observaciones,
            'created_at': servicio.solicitud.created_at.isoformat(),
            'aceptado_at': servicio.aceptado_at.isoformat() if servicio.aceptado_at else None,
            'iniciado_at': servicio.iniciado_at.isoformat() if servicio.iniciado_at else None,
            'finalizado_at': servicio.finalizado_at.isoformat() if servicio.finalizado_at else None
        }
        
        return jsonify({
            'success': True,
            'servicio': servicio_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al obtener detalles del servicio: {str(e)}'
        }), 500

@movil_bp.route('/perfil/estadisticas')
@login_required
def estadisticas_perfil():
    """Obtener estadísticas del perfil del móvil"""
    try:
        # Obtener servicios del móvil actual
        servicios = Servicio.query.filter_by(movil_id=current_user.id).all()
        
        total_servicios = len(servicios)
        servicios_completados = len([s for s in servicios if s.estado_servicio == 'completado'])
        
        # Calcular tiempo promedio (en minutos)
        tiempos = []
        for servicio in servicios:
            if servicio.iniciado_at and servicio.finalizado_at:
                tiempo = (servicio.finalizado_at - servicio.iniciado_at).total_seconds() / 60
                tiempos.append(tiempo)
        
        tiempo_promedio = int(sum(tiempos) / len(tiempos)) if tiempos else 0
        
        # Calcular calificación promedio (simulada por ahora)
        calificacion = round(4.2 + (servicios_completados / max(total_servicios, 1)) * 0.8, 1)
        
        # Calcular porcentajes
        porcentaje_aceptacion = int((servicios_completados / max(total_servicios, 1)) * 100)
        eficiencia = min(95, 75 + porcentaje_aceptacion // 4)  # Basado en tasa de completado
        
        return jsonify({
            'success': True,
            'estadisticas': {
                'total_servicios': total_servicios,
                'servicios_completados': servicios_completados,
                'tiempo_promedio': tiempo_promedio,
                'calificacion': calificacion,
                'porcentaje_aceptacion': porcentaje_aceptacion,
                'eficiencia': eficiencia
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al obtener estadísticas: {str(e)}'
        }), 500

def formatear_tiempo_restante(tiempo_servicio_activo_segundos):
    """Formatea el tiempo restante como cuenta regresiva desde 60 minutos"""
    if tiempo_servicio_activo_segundos is None:
        return "60:00"  # Si no ha iniciado, mostrar tiempo completo
    
    limite_segundos = 3600  # 60 minutos
    tiempo_restante_segundos = max(0, limite_segundos - int(tiempo_servicio_activo_segundos))
    
    # Convertir a minutos y segundos
    minutos = tiempo_restante_segundos // 60
    segundos = tiempo_restante_segundos % 60
    
    return f"{minutos:02d}:{segundos:02d}"

def generar_timeline_servicio(servicio):
    """Genera el timeline de eventos del servicio"""
    from app.utils.timezone_utils import format_bogota_time
    
    timeline = []
    
    # Solicitud creada
    timeline.append({
        'titulo': 'Solicitud creada',
        'tiempo_bogota': format_bogota_time(servicio.solicitud.created_at),
        'icono': 'plus-circle',
        'color': 'info'
    })
    
    # Servicio aceptado
    if servicio.aceptado_at:
        timeline.append({
            'titulo': 'Servicio aceptado',
            'tiempo_bogota': format_bogota_time(servicio.aceptado_at),
            'icono': 'check-circle',
            'color': 'success'
        })
    
    # En ruta
    if servicio.estado_servicio in ['en_ruta', 'en_sitio', 'completado']:
        timeline.append({
            'titulo': 'En ruta al sitio',
            'tiempo_bogota': format_bogota_time(servicio.aceptado_at),  # Usar aceptado_at como aproximación
            'icono': 'route',
            'color': 'primary'
        })
    
    # En sitio
    if servicio.estado_servicio in ['en_sitio', 'completado']:
        timeline.append({
            'titulo': 'Llegada al sitio',
            'tiempo_bogota': format_bogota_time(servicio.iniciado_at) if servicio.iniciado_at else 'En proceso',
            'icono': 'map-marker-alt',
            'color': 'warning'
        })
    
    # Servicio iniciado
    if servicio.iniciado_at:
        timeline.append({
            'titulo': 'Servicio iniciado',
            'tiempo_bogota': format_bogota_time(servicio.iniciado_at),
            'icono': 'play-circle',
            'color': 'info'
        })
    
    # Servicio completado
    if servicio.finalizado_at:
        timeline.append({
            'titulo': 'Servicio completado',
            'tiempo_bogota': format_bogota_time(servicio.finalizado_at),
            'icono': 'check-circle',
            'color': 'success'
        })
    
    return timeline

@movil_bp.route('/api/servicio/<int:servicio_id>/detalles')
@login_required
@role_required('movil')
def api_detalles_servicio(servicio_id):
    """API para obtener detalles específicos del servicio en tiempo real"""
    try:
        from app.utils.timezone_utils import get_bogota_time, format_bogota_time
        
        servicio = Servicio.query.filter_by(
            id=servicio_id,
            movil_id=current_user.id
        ).first_or_404()
        
        # Calcular tiempos en zona horaria de Bogotá
        ahora_bogota = get_bogota_time()
        
        # Tiempo transcurrido desde aceptación
        tiempo_desde_aceptacion = None
        if servicio.aceptado_at:
            tiempo_desde_aceptacion = (ahora_bogota - servicio.aceptado_at.replace(tzinfo=None)).total_seconds()
        
        # Tiempo de servicio activo
        tiempo_servicio_activo = None
        if servicio.iniciado_at:
            tiempo_servicio_activo = (ahora_bogota - servicio.iniciado_at.replace(tzinfo=None)).total_seconds()
        
        # Información detallada del servicio
        detalles = {
            'id': servicio.id,
            'estado': servicio.estado_servicio,
            'tipo_apoyo': servicio.solicitud.tipo_apoyo,
            'urgente': servicio.solicitud.is_urgente(),
            'direccion': servicio.solicitud.direccion,
            'tiempo_transcurrido': formatear_tiempo_restante(tiempo_servicio_activo),
            'hora_actual_bogota': format_bogota_time(ahora_bogota),
            'timeline': generar_timeline_servicio(servicio),
            'observaciones': servicio.observaciones_finales,
            
            # Información del técnico
            'tecnico': {
                'id': servicio.solicitud.tecnico.id,
                'nombre_completo': servicio.solicitud.tecnico.nombre_completo,
                'telefono': servicio.solicitud.tecnico.telefono,
                'email': servicio.solicitud.tecnico.email
            },
            
            # Ubicación
            'ubicacion': {
                'direccion': servicio.solicitud.direccion,
                'latitud': float(servicio.solicitud.latitud),
                'longitud': float(servicio.solicitud.longitud)
            },
            
            # Timestamps en zona horaria de Bogotá
            'timestamps': {
                'solicitud_creada': format_bogota_time(servicio.solicitud.created_at),
                'aceptado_at': format_bogota_time(servicio.aceptado_at) if servicio.aceptado_at else None,
                'iniciado_at': format_bogota_time(servicio.iniciado_at) if servicio.iniciado_at else None,
                'finalizado_at': format_bogota_time(servicio.finalizado_at) if servicio.finalizado_at else None,
                'tiempo_actual_bogota': format_bogota_time(ahora_bogota)
            },
            
            # Tiempos calculados
            'tiempos': {
                'desde_aceptacion_segundos': int(tiempo_desde_aceptacion) if tiempo_desde_aceptacion else None,
                'servicio_activo_segundos': int(tiempo_servicio_activo) if tiempo_servicio_activo else None,
                'limite_servicio_segundos': 3600,  # 1 hora límite
                'tiempo_restante_segundos': max(0, 3600 - int(tiempo_servicio_activo)) if tiempo_servicio_activo else 3600
            },
            
            # Observaciones
            'observaciones': {
                'solicitud': servicio.solicitud.observaciones,
                'servicio': servicio.observaciones,
                'finalizacion': servicio.observaciones_finales
            },
            
            # Estado de progreso
            'progreso': {
                'porcentaje_tiempo': min(100, (tiempo_servicio_activo / 3600 * 100)) if tiempo_servicio_activo else 0,
                'estado_timeline': {
                    'aceptado': bool(servicio.aceptado_at),
                    'en_ruta': servicio.estado_servicio in ['en_ruta', 'en_sitio', 'completado'],
                    'en_sitio': servicio.estado_servicio in ['en_sitio', 'completado'],
                    'completado': servicio.estado_servicio == 'completado'
                }
            }
        }
        
        return jsonify({
            'success': True,
            'servicio': detalles,
            'timestamp_servidor': format_bogota_time(ahora_bogota)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@movil_bp.route('/historial')
@login_required
@role_required('movil')
def historial():
    """Historial de servicios de la móvil"""
    page = request.args.get('page', 1, type=int)
    estado = request.args.get('estado', 'todos')
    
    query = Servicio.query.filter_by(movil_id=current_user.id)
    
    if estado != 'todos':
        query = query.filter_by(estado_servicio=estado)
    
    servicios = query.order_by(Servicio.aceptado_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    # Convertir servicios a diccionarios para serialización JSON
    servicios_serializables = [servicio.to_dict() for servicio in servicios.items]
    
    return render_template('movil/historial.html',
                         servicios=servicios,
                         servicios_json=servicios_serializables,
                         estado_filtro=estado)

@movil_bp.route('/mapa')
@login_required
@role_required('movil')
def mapa():
    """Mapa con solicitudes cercanas"""
    return render_template('movil/mapa.html')

@movil_bp.route('/diagnostico-mapa')
@login_required
@role_required('movil')
def diagnostico_mapa():
    """Página de diagnóstico del mapa"""
    return render_template('movil/diagnostico_mapa.html')

@movil_bp.route('/perfil')
@login_required
@role_required('movil')
def perfil():
    """Perfil de la unidad móvil"""
    return render_template('movil/perfil.html')

@movil_bp.route('/perfil/actualizar', methods=['POST'])
@login_required
@role_required('movil')
def actualizar_perfil():
    """Actualizar perfil de la unidad móvil"""
    try:
        current_user.nombre = request.form.get('nombre', current_user.nombre)
        current_user.apellido = request.form.get('apellido', current_user.apellido)
        current_user.telefono = request.form.get('telefono', current_user.telefono)
        
        # Cambiar contraseña si se proporciona
        nueva_password = request.form.get('nueva_password')
        if nueva_password:
            password_actual = request.form.get('password_actual')
            if not current_user.check_password(password_actual):
                flash('Contraseña actual incorrecta', 'error')
                return redirect(url_for('movil.perfil'))
            
            current_user.set_password(nueva_password)
        
        db.session.commit()
        flash('Perfil actualizado exitosamente', 'success')
        return redirect(url_for('movil.perfil'))
        
    except Exception as e:
        db.session.rollback()
        flash('Error al actualizar perfil', 'error')
        return redirect(url_for('movil.perfil'))

# APIs para tracking en tiempo real
@movil_bp.route('/api/solicitudes-cercanas')
@login_required
@role_required('movil')
def api_solicitudes_cercanas():
    """API para obtener solicitudes cercanas con datos reales"""
    try:
        # Obtener parámetros
        radio = request.args.get('radio', 20, type=int)  # km
        tipo_apoyo = request.args.get('tipo_apoyo', 'todos')
        lat_movil = request.args.get('lat', type=float)
        lng_movil = request.args.get('lng', type=float)
        
        if not lat_movil or not lng_movil:
            return jsonify({'error': 'Coordenadas de móvil requeridas'}), 400
        
        # Verificar que no tenga servicios activos
        servicio_activo = Servicio.query.filter_by(
            movil_id=current_user.id
        ).filter(
            Servicio.estado_servicio.in_(['aceptado', 'en_ruta', 'en_sitio'])
        ).first()
        
        if servicio_activo:
            return jsonify({
                'solicitudes': [],
                'mensaje': 'Tienes un servicio activo',
                'servicio_activo': {
                    'id': servicio_activo.id,
                    'estado': servicio_activo.estado_servicio
                }
            })
        
        # Buscar solicitudes pendientes
        solicitudes_pendientes = Solicitud.query.filter_by(estado='pendiente').all()
        
        solicitudes_cercanas = []
        for solicitud in solicitudes_pendientes:
            if not solicitud.is_expirada():
                # Calcular distancia usando coordenadas
                lat_solicitud, lng_solicitud = solicitud.get_coordenadas()
                distancia = calcular_distancia_haversine(
                    lat_movil, lng_movil, lat_solicitud, lng_solicitud
                )
                
                if distancia <= radio:
                    # Filtrar por tipo de apoyo
                    if tipo_apoyo == 'todos' or solicitud.tipo_apoyo == tipo_apoyo:
                        solicitudes_cercanas.append({
                            'id': solicitud.id,
                            'tipo_apoyo': solicitud.tipo_apoyo,
                            'tecnico': solicitud.tecnico.nombre_completo,
                            'telefono': solicitud.tecnico.telefono,
                            'direccion': solicitud.direccion,
                            'coordenadas': {
                                'lat': lat_solicitud,
                                'lng': lng_solicitud
                            },
                            'distancia_km': round(distancia, 2),
                            'tiempo_estimado_min': round(distancia * 2.5),  # Estimación: 2.5 min por km
                            'created_at': solicitud.created_at.isoformat(),
                            'tiempo_limite': solicitud.tiempo_limite.isoformat() if solicitud.tiempo_limite else None,
                            'observaciones': solicitud.observaciones,
                            'urgente': solicitud.is_urgente()
                        })
        
        # Ordenar por distancia
        solicitudes_cercanas.sort(key=lambda x: x['distancia_km'])
        
        return jsonify({
            'solicitudes': solicitudes_cercanas,
            'total': len(solicitudes_cercanas),
            'radio_km': radio
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@movil_bp.route('/api/ruta-tecnico/<int:solicitud_id>')
@login_required
@role_required('movil')
def api_ruta_tecnico(solicitud_id):
    """API para obtener ruta optimizada hacia técnico"""
    try:
        lat_movil = request.args.get('lat', type=float)
        lng_movil = request.args.get('lng', type=float)
        
        if not lat_movil or not lng_movil:
            return jsonify({'error': 'Coordenadas de móvil requeridas'}), 400
        
        solicitud = Solicitud.query.get_or_404(solicitud_id)
        
        if solicitud.estado != 'pendiente':
            return jsonify({'error': 'Solicitud no disponible'}), 400
        
        lat_tecnico, lng_tecnico = solicitud.get_coordenadas()
        
        # Calcular distancia y tiempo estimado
        distancia = calcular_distancia_haversine(lat_movil, lng_movil, lat_tecnico, lng_tecnico)
        tiempo_estimado = round(distancia * 2.5)  # 2.5 min por km
        
        # Generar puntos de ruta simplificada (línea recta por ahora)
        # En producción se podría integrar con Google Directions API
        ruta_puntos = generar_ruta_simplificada(lat_movil, lng_movil, lat_tecnico, lng_tecnico)
        
        return jsonify({
            'origen': {'lat': lat_movil, 'lng': lng_movil},
            'destino': {'lat': lat_tecnico, 'lng': lng_tecnico},
            'distancia_km': round(distancia, 2),
            'tiempo_estimado_min': tiempo_estimado,
            'ruta_puntos': ruta_puntos,
            'tecnico': {
                'nombre': solicitud.tecnico.nombre_completo,
                'telefono': solicitud.tecnico.telefono,
                'direccion': solicitud.direccion
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@movil_bp.route('/api/actualizar-ubicacion', methods=['POST'])
@login_required
@role_required('movil')
def api_actualizar_ubicacion():
    """API para actualizar ubicación de la móvil en tiempo real"""
    try:
        data = request.get_json()
        lat = data.get('lat')
        lng = data.get('lng')
        
        if not lat or not lng:
            return jsonify({'error': 'Coordenadas requeridas'}), 400
        
        # Actualizar o crear ubicación
        ubicacion = Ubicacion.query.filter_by(usuario_id=current_user.id).first()
        
        if ubicacion:
            ubicacion.latitud = lat
            ubicacion.longitud = lng
            ubicacion.updated_at = datetime.utcnow()
        else:
            ubicacion = Ubicacion(
                usuario_id=current_user.id,
                latitud=lat,
                longitud=lng
            )
            db.session.add(ubicacion)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'mensaje': 'Ubicación actualizada',
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

def calcular_distancia_haversine(lat1, lng1, lat2, lng2):
    """Calcular distancia entre dos puntos usando fórmula de Haversine"""
    import math
    
    # Radio de la Tierra en km
    R = 6371.0
    
    # Convertir grados a radianes
    lat1_rad = math.radians(lat1)
    lng1_rad = math.radians(lng1)
    lat2_rad = math.radians(lat2)
    lng2_rad = math.radians(lng2)
    
    # Diferencias
    dlat = lat2_rad - lat1_rad
    dlng = lng2_rad - lng1_rad
    
    # Fórmula de Haversine
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def generar_ruta_simplificada(lat1, lng1, lat2, lng2, puntos=10):
    """Generar puntos de ruta simplificada entre dos coordenadas"""
    ruta = []
    
    for i in range(puntos + 1):
        factor = i / puntos
        lat = lat1 + (lat2 - lat1) * factor
        lng = lng1 + (lng2 - lng1) * factor
        ruta.append({'lat': lat, 'lng': lng})
    
    return ruta