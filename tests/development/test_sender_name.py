#!/usr/bin/env python3
"""
Script para probar el nombre del remitente en los emails
"""

import os
import sys
from flask import Flask
from flask_mail import Mail, Message
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def test_sender_name():
    """Prueba el nombre del remitente configurado"""
    
    print("=" * 60)
    print("🧪 PRUEBA DE NOMBRE DEL REMITENTE")
    print("=" * 60)
    
    # Crear aplicación Flask temporal
    app = Flask(__name__)
    
    # Configurar Flask-Mail
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')
    
    print(f"📧 Configuración del remitente:")
    print(f"   MAIL_USERNAME: {app.config['MAIL_USERNAME']}")
    print(f"   MAIL_DEFAULT_SENDER: {app.config['MAIL_DEFAULT_SENDER']}")
    print()
    
    # Inicializar Flask-Mail
    mail = Mail(app)
    
    with app.app_context():
        try:
            # Crear mensaje de prueba
            msg = Message(
                subject='Prueba de Nombre del Remitente - Synapsis Apoyos',
                recipients=['victoranaranjos@gmail.com'],
                sender=app.config['MAIL_DEFAULT_SENDER']
            )
            
            msg.body = """
Hola,

Este es un email de prueba para verificar que el nombre del remitente aparezca como "Synapsis Apoyos".

Si recibes este email, deberías ver:
- Remitente: Synapsis Apoyos
- Email: vansnaranjo@gmail.com

Saludos,
Sistema Synapsis Apoyos
            """
            
            msg.html = """
<html>
<body>
    <h2>Prueba de Nombre del Remitente</h2>
    <p>Hola,</p>
    <p>Este es un email de prueba para verificar que el nombre del remitente aparezca como <strong>"Synapsis Apoyos"</strong>.</p>
    <p>Si recibes este email, deberías ver:</p>
    <ul>
        <li><strong>Remitente:</strong> Synapsis Apoyos</li>
        <li><strong>Email:</strong> vansnaranjo@gmail.com</li>
    </ul>
    <p>Saludos,<br>Sistema Synapsis Apoyos</p>
</body>
</html>
            """
            
            print("📤 Enviando email de prueba...")
            print(f"   Para: {msg.recipients[0]}")
            print(f"   Remitente configurado: {msg.sender}")
            print(f"   Asunto: {msg.subject}")
            print()
            
            # Enviar el email
            mail.send(msg)
            
            print("✅ Email de prueba enviado exitosamente!")
            print()
            print("🔍 Verifica tu bandeja de entrada:")
            print("   - El remitente debería aparecer como: 'Synapsis Apoyos'")
            print("   - El email debería ser: vansnaranjo@gmail.com")
            print("   - El asunto: 'Prueba de Nombre del Remitente - Synapsis Apoyos'")
            
        except Exception as e:
            print(f"❌ Error al enviar email: {e}")
            return False
    
    print("=" * 60)
    print("🏁 PRUEBA COMPLETADA")
    print("=" * 60)
    return True

if __name__ == "__main__":
    test_sender_name()