#!/usr/bin/env python3
"""
Script para diagnosticar problemas de autenticación con Gmail
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def test_gmail_connection():
    """Prueba la conexión con Gmail usando diferentes métodos"""
    
    email = "vansnaranjo@gmail.com"
    password = "M4r14l4r@"
    
    print("🔍 Diagnosticando conexión con Gmail...")
    print(f"📧 Email: {email}")
    print("🔐 Contraseña: [OCULTA]")
    print()
    
    # Probar conexión básica
    try:
        print("1️⃣ Probando conexión SMTP básica...")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        print("✅ Conexión TLS establecida")
        
        # Intentar login
        print("2️⃣ Intentando autenticación...")
        server.login(email, password)
        print("✅ Autenticación exitosa!")
        
        server.quit()
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Error de autenticación: {e}")
        print()
        print("🔧 POSIBLES SOLUCIONES:")
        print("   1. Activar 'Verificación en 2 pasos' en tu cuenta de Google")
        print("   2. Generar una 'Contraseña de aplicación' específica")
        print("   3. Usar la contraseña de aplicación en lugar de tu contraseña normal")
        print()
        print("📋 PASOS PARA CREAR CONTRASEÑA DE APLICACIÓN:")
        print("   1. Ve a https://myaccount.google.com/security")
        print("   2. Activa 'Verificación en 2 pasos'")
        print("   3. Ve a 'Contraseñas de aplicaciones'")
        print("   4. Selecciona 'Correo' y 'Otro (nombre personalizado)'")
        print("   5. Escribe 'Synapsis Apoyos' como nombre")
        print("   6. Usa la contraseña generada (16 caracteres) en el .env")
        return False
        
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def test_email_sending():
    """Prueba enviar un email de prueba"""
    
    email = "vansnaranjo@gmail.com"
    password = "M4r14l4r@"
    
    try:
        print("3️⃣ Probando envío de email de prueba...")
        
        # Crear mensaje
        msg = MIMEMultipart()
        msg['From'] = email
        msg['To'] = email  # Enviarse a sí mismo
        msg['Subject'] = "Prueba de configuración - Synapsis Apoyos"
        
        body = """
        ¡Hola!
        
        Este es un email de prueba para verificar que la configuración de correo
        de Synapsis Apoyos funciona correctamente.
        
        Si recibes este mensaje, la configuración está funcionando.
        
        Saludos,
        Sistema Synapsis Apoyos
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Enviar
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(email, password)
        server.send_message(msg)
        server.quit()
        
        print("✅ Email de prueba enviado exitosamente!")
        print(f"📬 Revisa la bandeja de entrada de {email}")
        return True
        
    except Exception as e:
        print(f"❌ Error al enviar email: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 DIAGNÓSTICO DE CONFIGURACIÓN DE EMAIL")
    print("=" * 60)
    print()
    
    # Probar conexión
    if test_gmail_connection():
        # Si la conexión funciona, probar envío
        test_email_sending()
    
    print()
    print("=" * 60)
    print("🏁 DIAGNÓSTICO COMPLETADO")
    print("=" * 60)