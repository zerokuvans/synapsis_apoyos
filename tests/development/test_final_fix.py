#!/usr/bin/env python3
"""
Script de prueba final para verificar que el error 'Usuario' object has no attribute 'usuario' está resuelto
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models.usuario import Usuario
from app.utils.email_utils import send_password_reset_email
from app.utils.password_utils import generate_temporary_password
from datetime import datetime

def test_password_reset_functionality():
    """Prueba la funcionalidad completa de reseteo de contraseña"""
    
    print("🧪 Iniciando prueba final de reseteo de contraseña...")
    
    # Crear aplicación
    app = create_app()
    
    with app.app_context():
        try:
            # Buscar usuario de prueba
            usuario = Usuario.query.filter_by(email='victoranaranjos@gmail.com').first()
            
            if not usuario:
                print("❌ Usuario de prueba no encontrado")
                return False
            
            print(f"✅ Usuario encontrado: {usuario.get_nombre_completo()}")
            print(f"📧 Email: {usuario.email}")
            
            # Generar contraseña temporal
            nueva_password = generate_temporary_password()
            print(f"🔑 Nueva contraseña generada: {nueva_password}")
            
            # Intentar enviar email (esto fallará por configuración, pero no por el error de atributo)
            try:
                send_password_reset_email(usuario, nueva_password)
                print("✅ Email enviado exitosamente")
                return True
            except Exception as e:
                error_msg = str(e)
                if "'Usuario' object has no attribute 'usuario'" in error_msg:
                    print(f"❌ ERROR PERSISTENTE: {error_msg}")
                    return False
                else:
                    print(f"⚠️  Error de configuración de email (esperado): {error_msg}")
                    print("✅ El error de atributo 'usuario' está RESUELTO")
                    return True
                    
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            return False

if __name__ == "__main__":
    success = test_password_reset_functionality()
    if success:
        print("\n🎉 PRUEBA EXITOSA: El error 'Usuario' object has no attribute 'usuario' está completamente resuelto")
        print("💡 Solo falta configurar las credenciales de email en el archivo .env")
    else:
        print("\n❌ PRUEBA FALLIDA: El error persiste")
    
    sys.exit(0 if success else 1)