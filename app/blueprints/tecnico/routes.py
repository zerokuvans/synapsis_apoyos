from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.blueprints.tecnico import tecnico_bp
from app.blueprints.auth.routes import role_required
from app.models.solicitud import Solicitud
from app.models.servicio import Servicio
from app.models.ubicacion import Ubicacion
from app.models.usuario import Usuario
from app import db
from datetime import datetime
from sqlalchemy import and_, func

@tecnico_bp.route('/dashboard')
@login_required
@role_required('tecnico')
def dashboard():
    """Dashboard principal del técnico"""
    from app.models.servicio import Servicio
    from sqlalchemy import func
    from datetime import datetime, timedelta
    from app.utils.timezone_utils import get_bogota_timestamp
    
    # Obtener solicitudes recientes del técnico
    solicitudes = Solicitud.query.filter_by(
        tecnico_id=current_user.id
    ).order_by(Solicitud.created_at.desc()).limit(10).all()
    
    # Calcular estadísticas reales del técnico
    # Total de solicitudes del técnico
    total_solicitudes = Solicitud.query.filter_by(tecnico_id=current_user.id).count()
    
    # Solicitudes completadas (que tienen servicio completado)
    solicitudes_completadas = db.session.query(Solicitud).select_from(Solicitud).join(
        Servicio, Solicitud.id == Servicio.solicitud_id
    ).filter(
        Solicitud.tecnico_id == current_user.id,
        Servicio.estado_servicio == 'completado'
    ).count()
    
    # Solicitudes en curso (aceptadas pero no completadas)
    solicitudes_en_curso = db.session.query(Solicitud).select_from(Solicitud).join(
        Servicio, Solicitud.id == Servicio.solicitud_id
    ).filter(
        Solicitud.tecnico_id == current_user.id,
        Servicio.estado_servicio.in_(['aceptado', 'en_ruta', 'en_sitio'])
    ).count()
    
    # Solicitudes disponibles (pendientes sin asignar)
    solicitudes_disponibles = Solicitud.query.filter_by(
        tecnico_id=current_user.id,
        estado='pendiente'
    ).count()
    
    # Obtener móviles cercanas (usar ubicación del técnico si está disponible)
    ubicacion_tecnico = Ubicacion.query.filter_by(usuario_id=current_user.id).first()
    if ubicacion_tecnico:
        moviles_cercanas = Ubicacion.obtener_moviles_cercanas(
            latitud=ubicacion_tecnico.latitud,
            longitud=ubicacion_tecnico.longitud,
            radio_km=20
        )
    else:
        # Usar coordenadas de Bogotá como fallback
        moviles_cercanas = Ubicacion.obtener_moviles_cercanas(
            latitud=4.6097,  # Centro de Bogotá
            longitud=-74.0817,
            radio_km=20
        )
    
    # Calcular estadísticas adicionales
    # Tiempo promedio de respuesta (desde solicitud hasta aceptación)
    tiempo_promedio_respuesta = None
    try:
        servicios_con_tiempo = db.session.query(
            func.avg(
                (func.julianday(Servicio.aceptado_at) - func.julianday(Solicitud.created_at)) * 24 * 60
            ).label('promedio_minutos')
        ).select_from(Servicio).join(
            Solicitud, Servicio.solicitud_id == Solicitud.id
        ).filter(
            Solicitud.tecnico_id == current_user.id,
            Servicio.aceptado_at.isnot(None)
        ).first()
        
        if servicios_con_tiempo and servicios_con_tiempo.promedio_minutos:
            tiempo_promedio_respuesta = round(servicios_con_tiempo.promedio_minutos, 1)
    except Exception:
        # Si hay error en el cálculo, usar valor por defecto
        tiempo_promedio_respuesta = None
    
    # Estadísticas por tipo de apoyo
    estadisticas_tipo = db.session.query(
        Solicitud.tipo_apoyo,
        func.count(Solicitud.id).label('total')
    ).filter(
        Solicitud.tecnico_id == current_user.id
    ).group_by(Solicitud.tipo_apoyo).all()
    
    # Convertir a diccionario para fácil acceso en template
    stats_por_tipo = {stat.tipo_apoyo: stat.total for stat in estadisticas_tipo}
    
    # Fecha de registro del técnico
    fecha_registro = current_user.created_at if hasattr(current_user, 'created_at') else None
    
    # Preparar datos de estadísticas para el template
    estadisticas = {
        'total_solicitudes': total_solicitudes,
        'completadas': solicitudes_completadas,
        'en_curso': solicitudes_en_curso,
        'disponibles': solicitudes_disponibles,
        'tiempo_promedio_respuesta': tiempo_promedio_respuesta,
        'por_tipo': stats_por_tipo,
        'fecha_registro': fecha_registro,
        'moviles_cercanas_count': len(moviles_cercanas) if moviles_cercanas else 0
    }
    
    return render_template('tecnico/dashboard.html', 
                         solicitudes=solicitudes,
                         moviles_cercanas=moviles_cercanas,
                         estadisticas=estadisticas)

@tecnico_bp.route('/solicitud/nueva')
@login_required
@role_required('tecnico')
def nueva_solicitud():
    """Formulario para crear nueva solicitud"""
    return render_template('tecnico/nueva_solicitud.html')

@tecnico_bp.route('/solicitud/crear', methods=['POST'])
@login_required
@role_required('tecnico')
def crear_solicitud():
    """Crear nueva solicitud de apoyo"""
    try:
        tipo_apoyo = request.form.get('tipo_apoyo')
        latitud = float(request.form.get('latitud'))
        longitud = float(request.form.get('longitud'))
        observaciones = request.form.get('observaciones', '').strip()
        direccion = request.form.get('direccion', '').strip()
        
        if not tipo_apoyo or tipo_apoyo not in ['escalera', 'equipos']:
            flash('Tipo de apoyo no válido', 'error')
            return redirect(url_for('tecnico.nueva_solicitud'))
        
        if not latitud or not longitud:
            flash('Ubicación requerida', 'error')
            return redirect(url_for('tecnico.nueva_solicitud'))
        
        # Verificar si el técnico tiene solicitudes pendientes
        solicitud_pendiente = Solicitud.query.filter_by(
            tecnico_id=current_user.id,
            estado='pendiente'
        ).first()
        
        if solicitud_pendiente:
            flash('Ya tienes una solicitud pendiente. Espera a que sea atendida o cancélala.', 'warning')
            return redirect(url_for('tecnico.dashboard'))
        
        # Crear nueva solicitud
        solicitud = Solicitud(
            tecnico_id=current_user.id,
            tipo_apoyo=tipo_apoyo,
            latitud=latitud,
            longitud=longitud,
            observaciones=observaciones,
            direccion=direccion
        )
        
        db.session.add(solicitud)
        db.session.commit()
        
        flash(f'Solicitud de {tipo_apoyo} creada exitosamente', 'success')
        return redirect(url_for('tecnico.dashboard'))
        
    except ValueError:
        flash('Coordenadas no válidas', 'error')
        return redirect(url_for('tecnico.nueva_solicitud'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error creando solicitud: {str(e)}', 'error')
        return redirect(url_for('tecnico.nueva_solicitud'))

@tecnico_bp.route('/solicitud/<int:solicitud_id>/cancelar', methods=['POST'])
@login_required
@role_required('tecnico')
def cancelar_solicitud(solicitud_id):
    """Cancelar solicitud del técnico"""
    try:
        solicitud = Solicitud.query.filter_by(
            id=solicitud_id,
            tecnico_id=current_user.id
        ).first()
        
        if not solicitud:
            flash('Solicitud no encontrada', 'error')
            return redirect(url_for('tecnico.dashboard'))
        
        observaciones = request.form.get('observaciones', 'Cancelada por el técnico')
        
        success, message = solicitud.cancelar(observaciones)
        
        if success:
            db.session.commit()
            flash(message, 'success')
        else:
            flash(message, 'error')
        
        return redirect(url_for('tecnico.dashboard'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error cancelando solicitud: {str(e)}', 'error')
        return redirect(url_for('tecnico.dashboard'))

@tecnico_bp.route('/historial')
@login_required
@role_required('tecnico')
def historial():
    """Historial de solicitudes del técnico"""
    page = request.args.get('page', 1, type=int)
    estado = request.args.get('estado', 'todas')
    
    query = Solicitud.query.filter_by(tecnico_id=current_user.id)
    
    if estado != 'todas':
        query = query.filter_by(estado=estado)
    
    solicitudes = query.order_by(Solicitud.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    return render_template('tecnico/historial.html', 
                         solicitudes=solicitudes,
                         estado_filtro=estado)

@tecnico_bp.route('/mapa')
@login_required
@role_required('tecnico')
def mapa():
    """Mapa en tiempo real con móviles cercanas"""
    return render_template('tecnico/mapa.html')

@tecnico_bp.route('/perfil')
@login_required
@role_required('tecnico')
def perfil():
    """Perfil del técnico"""
    return render_template('tecnico/perfil.html')

@tecnico_bp.route('/perfil/actualizar', methods=['POST'])
@login_required
@role_required('tecnico')
def actualizar_perfil():
    """Actualizar perfil del técnico"""
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
                return redirect(url_for('tecnico.perfil'))
            
            current_user.set_password(nueva_password)
        
        db.session.commit()
        flash('Perfil actualizado exitosamente', 'success')
        return redirect(url_for('tecnico.perfil'))
        
    except Exception as e:
        db.session.rollback()
        flash('Error al actualizar perfil', 'error')
        return redirect(url_for('tecnico.perfil'))

# APIs para tracking en tiempo real
@tecnico_bp.route('/api/moviles-cercanas')
@login_required
@role_required('tecnico')
def api_moviles_cercanas():
    """API para obtener móviles cercanas activas en tiempo real"""
    try:
        # Obtener parámetros
        radio = request.args.get('radio', 20, type=int)  # km
        lat_tecnico = request.args.get('lat', type=float)
        lng_tecnico = request.args.get('lng', type=float)
        solo_disponibles = request.args.get('solo_disponibles', 'false').lower() == 'true'
        
        if not lat_tecnico or not lng_tecnico:
            return jsonify({'error': 'Coordenadas de técnico requeridas'}), 400
        
        # Buscar móviles activas con ubicaciones recientes
        from app.models.servicio import Servicio
        from sqlalchemy import and_, func, text, desc
        from datetime import datetime, timedelta
        from app.utils.timezone_utils import get_bogota_timestamp
        
        # Tiempo límite para considerar móviles activas (últimos 15 minutos)
        tiempo_limite = get_bogota_timestamp() - timedelta(minutes=15)
        
        # Subconsulta para obtener la ubicación más reciente de cada móvil
        subquery = db.session.query(
            Ubicacion.usuario_id,
            func.max(Ubicacion.timestamp).label('max_timestamp')
        ).filter(
            Ubicacion.activa == True,
            Ubicacion.timestamp >= tiempo_limite
        ).group_by(Ubicacion.usuario_id).subquery()
        
        # Consulta principal para móviles activas con ubicaciones recientes
        moviles_query = db.session.query(
            Usuario.id,
            Usuario.nombre,
            Usuario.apellido,
            Usuario.telefono,
            Usuario.last_activity,
            Ubicacion.latitud,
            Ubicacion.longitud,
            Ubicacion.timestamp
        ).join(
            Ubicacion, Usuario.id == Ubicacion.usuario_id
        ).join(
            subquery, 
            and_(
                Ubicacion.usuario_id == subquery.c.usuario_id,
                Ubicacion.timestamp == subquery.c.max_timestamp
            )
        ).filter(
            and_(
                Usuario.rol == 'movil',
                Usuario.activo == True,
                Usuario.last_activity >= tiempo_limite
            )
        ).order_by(desc(Ubicacion.timestamp))
        
        moviles_cercanas = []
        moviles_disponibles = 0
        moviles_ocupadas = 0
        
        for movil in moviles_query.all():
            # Calcular distancia
            distancia = calcular_distancia_haversine(
                lat_tecnico, lng_tecnico, movil.latitud, movil.longitud
            )
            
            if distancia <= radio:
                # Verificar si tiene servicio activo
                servicio_activo = Servicio.query.filter_by(
                    movil_id=movil.id
                ).filter(
                    Servicio.estado_servicio.in_(['aceptado', 'en_ruta', 'en_sitio'])
                ).first()
                
                estado = 'ocupada' if servicio_activo else 'disponible'
                
                # Contar móviles por estado
                if estado == 'disponible':
                    moviles_disponibles += 1
                else:
                    moviles_ocupadas += 1
                
                # Si solo se quieren disponibles, filtrar
                if solo_disponibles and estado != 'disponible':
                    continue
                
                # Calcular tiempo estimado de llegada (considerando tráfico urbano)
                tiempo_estimado = round(distancia * 3.5)  # 3.5 min por km en ciudad
                
                # Determinar nivel de prioridad basado en distancia
                if distancia <= 5:
                    prioridad = 'alta'
                elif distancia <= 10:
                    prioridad = 'media'
                else:
                    prioridad = 'baja'
                
                movil_info = {
                    'id': movil.id,
                    'nombre': f"{movil.nombre} {movil.apellido}",
                    'telefono': movil.telefono,
                    'coordenadas': {
                        'lat': float(movil.latitud),
                        'lng': float(movil.longitud)
                    },
                    'distancia_km': round(distancia, 2),
                    'tiempo_estimado_min': tiempo_estimado,
                    'estado': estado,
                    'prioridad': prioridad,
                    'ultima_actualizacion': movil.timestamp.isoformat(),
                    'tiempo_desde_actualizacion': int((get_bogota_timestamp() - movil.timestamp).total_seconds() / 60),
                    'servicio_activo_id': servicio_activo.id if servicio_activo else None,
                    'activa_recientemente': (get_bogota_timestamp() - movil.last_activity).total_seconds() < 900  # 15 min
                }
                
                # Agregar información del servicio activo si existe
                if servicio_activo:
                    movil_info['servicio_activo'] = {
                        'id': servicio_activo.id,
                        'estado': servicio_activo.estado_servicio,
                        'tipo_apoyo': servicio_activo.solicitud.tipo_apoyo if servicio_activo.solicitud else None,
                        'tiempo_inicio': servicio_activo.created_at.isoformat()
                    }
                
                moviles_cercanas.append(movil_info)
        
        # Ordenar por prioridad y luego por distancia
        def sort_key(movil):
            prioridad_orden = {'alta': 1, 'media': 2, 'baja': 3}
            estado_orden = {'disponible': 1, 'ocupada': 2}
            return (estado_orden.get(movil['estado'], 3), 
                   prioridad_orden.get(movil['prioridad'], 4), 
                   movil['distancia_km'])
        
        moviles_cercanas.sort(key=sort_key)
        
        return jsonify({
            'success': True,
            'moviles': moviles_cercanas,
            'estadisticas': {
                'total': len(moviles_cercanas),
                'disponibles': moviles_disponibles,
                'ocupadas': moviles_ocupadas,
                'radio_km': radio,
                'tiempo_limite_min': 15
            },
            'tecnico': {
                'coordenadas': {
                    'lat': lat_tecnico,
                    'lng': lng_tecnico
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'moviles': [],
            'estadisticas': {
                'total': 0,
                'disponibles': 0,
                'ocupadas': 0,
                'radio_km': radio,
                'tiempo_limite_min': 15
            }
        }), 500

@tecnico_bp.route('/api/moviles-asignadas')
@login_required
@role_required('tecnico')
def api_moviles_asignadas():
    """API para obtener móviles asignadas a servicios del técnico"""
    try:
        lat_tecnico = request.args.get('lat', type=float)
        lng_tecnico = request.args.get('lng', type=float)
        
        if not lat_tecnico or not lng_tecnico:
            return jsonify({'error': 'Coordenadas de técnico requeridas'}), 400
        
        # Buscar servicios activos del técnico
        from app.models.servicio import Servicio
        
        servicios_activos = db.session.query(
            Servicio.id,
            Servicio.estado_servicio,
            Servicio.aceptado_at,
            Servicio.iniciado_at,
            Usuario.id.label('movil_id'),
            Usuario.nombre,
            Usuario.apellido,
            Usuario.telefono,
            Ubicacion.latitud,
            Ubicacion.longitud,
            Ubicacion.timestamp,
            Solicitud.tipo_apoyo,
            Solicitud.observaciones
        ).join(
            Solicitud, Servicio.solicitud_id == Solicitud.id
        ).join(
            Usuario, Servicio.movil_id == Usuario.id
        ).outerjoin(
            Ubicacion, Usuario.id == Ubicacion.usuario_id
        ).filter(
            and_(
                Solicitud.tecnico_id == current_user.id,
                Servicio.estado_servicio.in_(['aceptado', 'en_ruta', 'en_sitio'])
            )
        ).all()
        
        moviles_asignadas = []
        for servicio in servicios_activos:
            if servicio.latitud and servicio.longitud:
                # Calcular distancia
                distancia = calcular_distancia_haversine(
                    lat_tecnico, lng_tecnico, servicio.latitud, servicio.longitud
                )
                
                # Determinar estado y color
                estado_info = {
                    'aceptado': {'texto': 'Aceptado', 'color': '#ffc107'},
                    'en_ruta': {'texto': 'En Camino', 'color': '#17a2b8'},
                    'en_sitio': {'texto': 'En el Sitio', 'color': '#28a745'}
                }
                
                estado = estado_info.get(servicio.estado_servicio, {'texto': 'Desconocido', 'color': '#6c757d'})
                
                moviles_asignadas.append({
                    'servicio_id': servicio.id,
                    'movil_id': servicio.movil_id,
                    'nombre': f"{servicio.nombre} {servicio.apellido}",
                    'telefono': servicio.telefono,
                    'coordenadas': {
                        'lat': float(servicio.latitud),
                        'lng': float(servicio.longitud)
                    },
                    'distancia_km': round(distancia, 2),
                    'tiempo_estimado_min': round(distancia * 2.5),
                    'estado': servicio.estado_servicio,
                    'estado_texto': estado['texto'],
                    'estado_color': estado['color'],
                    'tipo_apoyo': servicio.tipo_apoyo,
                    'observaciones': servicio.observaciones,
                    'aceptado_at': servicio.aceptado_at.isoformat() if servicio.aceptado_at else None,
                    'iniciado_at': servicio.iniciado_at.isoformat() if servicio.iniciado_at else None,
                    'ultima_actualizacion': servicio.timestamp.isoformat() if servicio.timestamp else None
                })
        
        return jsonify({
            'moviles_asignadas': moviles_asignadas,
            'total': len(moviles_asignadas)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@tecnico_bp.route('/api/actualizar-ubicacion', methods=['POST'])
@login_required
@role_required('tecnico')
def api_actualizar_ubicacion_tecnico():
    """API para actualizar ubicación del técnico en tiempo real"""
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