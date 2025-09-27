from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app.blueprints.auth import auth_bp
from app.models.usuario import Usuario
from app import db, limiter

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")  # Máximo 10 intentos de login por minuto
def login():
    """Página de inicio de sesión"""
    # Si ya está autenticado, redirigir al dashboard correspondiente
    if current_user.is_authenticated:
        return redirect_to_dashboard(current_user.rol)
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = bool(request.form.get('remember'))
        
        if not email or not password:
            flash('Por favor ingresa email y contraseña', 'error')
            return render_template('auth/login.html')
        
        # Buscar usuario por email
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario and usuario.check_password(password):
            if not usuario.activo:
                flash('Tu cuenta está desactivada. Contacta al administrador.', 'error')
                return render_template('auth/login.html')
            
            # Iniciar sesión
            login_user(usuario, remember=remember)
            flash(f'¡Bienvenido {usuario.get_nombre_completo()}!', 'success')
            
            # Redirigir según el rol
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            
            return redirect_to_dashboard(usuario.rol)
        else:
            flash('Email o contraseña incorrectos', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Cerrar sesión"""
    logout_user()
    flash('Has cerrado sesión exitosamente', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/api/login', methods=['POST'])
@limiter.limit("5 per minute")  # Más restrictivo para API
def api_login():
    """API endpoint para login"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No se recibieron datos'
            }), 400
        
        email = data.get('email')
        password = data.get('password')
        rol = data.get('role')  # Opcional: validar rol específico
        
        if not email or not password:
            return jsonify({
                'success': False,
                'message': 'Email y contraseña son requeridos'
            }), 400
        
        # Buscar usuario
        usuario = Usuario.query.filter_by(email=email).first()
        
        if not usuario:
            return jsonify({
                'success': False,
                'message': 'Usuario no encontrado'
            }), 401
        
        if not usuario.check_password(password):
            return jsonify({
                'success': False,
                'message': 'Contraseña incorrecta'
            }), 401
        
        if not usuario.activo:
            return jsonify({
                'success': False,
                'message': 'Cuenta desactivada'
            }), 401
        
        # Validar rol si se especifica
        if rol and usuario.rol != rol:
            return jsonify({
                'success': False,
                'message': f'No tienes permisos de {rol}'
            }), 403
        
        # Iniciar sesión
        login_user(usuario)
        
        return jsonify({
            'success': True,
            'user_id': usuario.id,
            'redirect_url': get_dashboard_url(usuario.rol),
            'user': usuario.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error interno: {str(e)}'
        }), 500

@auth_bp.route('/api/logout', methods=['POST'])
@login_required
def api_logout():
    """API endpoint para logout"""
    try:
        logout_user()
        return jsonify({
            'success': True,
            'message': 'Sesión cerrada exitosamente'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error cerrando sesión: {str(e)}'
        }), 500

@auth_bp.route('/api/current-user')
@login_required
def api_current_user():
    """API endpoint para obtener usuario actual"""
    try:
        return jsonify({
            'success': True,
            'user': current_user.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error obteniendo usuario: {str(e)}'
        }), 500

def redirect_to_dashboard(rol):
    """Redirige al dashboard según el rol del usuario"""
    if rol == 'tecnico':
        return redirect(url_for('tecnico.dashboard'))
    elif rol == 'movil':
        return redirect(url_for('movil.dashboard'))
    elif rol == 'lider':
        return redirect(url_for('lider.dashboard'))
    else:
        flash('Rol de usuario no válido', 'error')
        return redirect(url_for('auth.login'))

def get_dashboard_url(rol):
    """Obtiene la URL del dashboard según el rol"""
    if rol == 'tecnico':
        return url_for('tecnico.dashboard')
    elif rol == 'movil':
        return url_for('movil.dashboard')
    elif rol == 'lider':
        return url_for('lider.dashboard')
    else:
        return url_for('auth.login')

# Decorador personalizado para verificar roles
def role_required(roles):
    """Decorador para requerir roles específicos"""
    def decorator(f):
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            
            if isinstance(roles, str):
                required_roles = [roles]
            else:
                required_roles = roles
            
            if current_user.rol not in required_roles:
                flash('No tienes permisos para acceder a esta página', 'error')
                return redirect_to_dashboard(current_user.rol)
            
            return f(*args, **kwargs)
        
        decorated_function.__name__ = f.__name__
        return decorated_function
    return decorator