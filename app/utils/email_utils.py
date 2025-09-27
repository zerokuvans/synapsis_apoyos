from flask import render_template, current_app
from flask_mail import Message
from app import mail
from app.utils.timezone_utils import get_bogota_timestamp, format_bogota_time
import logging

def send_password_reset_email(usuario, nueva_password):
    """
    Envía un correo electrónico con la nueva contraseña temporal al usuario.
    
    Args:
        usuario: Objeto Usuario con los datos del usuario
        nueva_password (str): Nueva contraseña temporal generada
    
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        # Verificar que el usuario tenga email
        if not usuario.email:
            return False, "El usuario no tiene un email registrado"
        
        # Obtener la fecha actual en zona horaria de Bogotá
        fecha_reseteo = format_bogota_time(get_bogota_timestamp())
        
        # Crear el mensaje
        msg = Message(
            subject='Reseteo de Contraseña - Synapsis Apoyos',
            recipients=[usuario.email],
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        
        # Renderizar la plantilla HTML
        msg.html = render_template(
            'emails/password_reset.html',
            usuario=usuario,
            nueva_password=nueva_password,
            fecha_reseteo=fecha_reseteo
        )
        
        # Crear versión de texto plano como respaldo
        msg.body = f"""
Hola {usuario.nombre} {usuario.apellido},

Se ha generado una nueva contraseña temporal para tu cuenta en Synapsis Apoyos.

Tu nueva contraseña temporal es: {nueva_password}

Detalles de tu cuenta:
- Email: {usuario.email}
- Nombre: {usuario.get_nombre_completo()}
- Rol: {usuario.rol.title()}
- Fecha de reseteo: {fecha_reseteo}

IMPORTANTE: Esta es una contraseña temporal. Por motivos de seguridad, te recomendamos cambiarla inmediatamente después de iniciar sesión.

Instrucciones:
1. Ingresa al sistema con tu email: {usuario.email}
2. Usa la contraseña temporal mostrada arriba
3. Ve a tu perfil y cambia la contraseña por una de tu preferencia

Si no solicitaste este cambio, contacta inmediatamente al administrador del sistema.

--
Synapsis Apoyos
Sistema de Gestión de Servicios Técnicos
        """
        
        # Enviar el correo
        mail.send(msg)
        
        # Log del envío exitoso
        current_app.logger.info(f"Correo de reseteo de contraseña enviado exitosamente a {usuario.email} para el usuario {usuario.get_nombre_completo()}")
        
        return True, "Correo enviado exitosamente"
        
    except Exception as e:
        # Log del error
        current_app.logger.error(f"Error al enviar correo de reseteo de contraseña a {usuario.email}: {str(e)}")
        return False, f"Error al enviar el correo: {str(e)}"

def send_notification_email(to_email, subject, template, **kwargs):
    """
    Función genérica para enviar correos de notificación.
    
    Args:
        to_email (str): Email del destinatario
        subject (str): Asunto del correo
        template (str): Nombre de la plantilla a usar
        **kwargs: Variables adicionales para la plantilla
    
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        msg = Message(
            subject=subject,
            recipients=[to_email],
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        
        # Renderizar la plantilla HTML
        msg.html = render_template(template, **kwargs)
        
        # Enviar el correo
        mail.send(msg)
        
        current_app.logger.info(f"Correo de notificación enviado exitosamente a {to_email}")
        return True, "Correo enviado exitosamente"
        
    except Exception as e:
        current_app.logger.error(f"Error al enviar correo de notificación a {to_email}: {str(e)}")
        return False, f"Error al enviar el correo: {str(e)}"

def validate_email_config():
    """
    Valida que la configuración de correo esté completa.
    
    Returns:
        tuple: (is_valid: bool, missing_configs: list)
    """
    required_configs = [
        'MAIL_SERVER',
        'MAIL_USERNAME',
        'MAIL_PASSWORD',
        'MAIL_DEFAULT_SENDER'
    ]
    
    missing_configs = []
    
    for config in required_configs:
        if not current_app.config.get(config):
            missing_configs.append(config)
    
    is_valid = len(missing_configs) == 0
    
    return is_valid, missing_configs