#!/usr/bin/env python3
"""
Script para probar la configuración de correo electrónico
"""

from app import create_app
from app.utils.email_utils import validate_email_config, send_notification_email
from app.models.usuario import Usuario
from app.utils.password_utils import generate_temporary_password
from app.utils.email_utils import send_password_reset_email

def test_email_configuration():
    """Prueba la configuración de correo electrónico"""
    app = create_app()
    
    with app.app_context():
        print("🔧 Probando configuración de correo electrónico...")
        print("=" * 50)
        
        # 1. Validar configuración
        print("1. Validando configuración de correo...")
        is_valid, missing_configs = validate_email_config()
        
        if is_valid:
            print("✅ Configuración de correo válida")
        else:
            print("❌ Configuración de correo incompleta")
            print(f"   Configuraciones faltantes: {', '.join(missing_configs)}")
            print("\n📝 Para configurar el correo:")
            print("   1. Copia .env.example a .env")
            print("   2. Completa las variables de correo en .env")
            print("   3. Para Gmail, usa una App Password")
            return False
        
        # 2. Mostrar configuración actual (sin mostrar contraseñas)
        print("\n2. Configuración actual:")
        print(f"   Servidor: {app.config.get('MAIL_SERVER')}")
        print(f"   Puerto: {app.config.get('MAIL_PORT')}")
        print(f"   TLS: {app.config.get('MAIL_USE_TLS')}")
        print(f"   SSL: {app.config.get('MAIL_USE_SSL')}")
        print(f"   Usuario: {app.config.get('MAIL_USERNAME')}")
        print(f"   Remitente por defecto: {app.config.get('MAIL_DEFAULT_SENDER')}")
        
        # 3. Buscar un usuario de prueba
        print("\n3. Buscando usuario de prueba...")
        usuario_prueba = Usuario.query.filter(
            Usuario.email.isnot(None),
            Usuario.email != ''
        ).first()
        
        if not usuario_prueba:
            print("❌ No se encontró ningún usuario con email para prueba")
            print("   Agrega un email a algún usuario en la base de datos")
            return False
        
        print(f"✅ Usuario de prueba encontrado: {usuario_prueba.get_nombre_completo()} ({usuario_prueba.email})")
        
        # 4. Generar contraseña temporal
        print("\n4. Generando contraseña temporal...")
        nueva_password = generate_temporary_password()
        print(f"✅ Contraseña temporal generada: {nueva_password}")
        
        # 5. Probar envío de correo (sin cambiar la contraseña real)
        print("\n5. Probando envío de correo...")
        print("   ⚠️  NOTA: Esto enviará un correo real al usuario")
        
        respuesta = input("   ¿Continuar con el envío de prueba? (s/N): ")
        if respuesta.lower() != 's':
            print("   ⏭️  Prueba de envío omitida")
            return True
        
        try:
            # Enviar correo de prueba
            success, message = send_password_reset_email(usuario_prueba, nueva_password)
            
            if success:
                print("✅ Correo enviado exitosamente!")
                print(f"   Mensaje: {message}")
                print(f"   Destinatario: {usuario_prueba.email}")
            else:
                print("❌ Error al enviar correo")
                print(f"   Error: {message}")
                return False
                
        except Exception as e:
            print(f"❌ Excepción al enviar correo: {str(e)}")
            return False
        
        print("\n🎉 Todas las pruebas completadas exitosamente!")
        return True

if __name__ == "__main__":
    print("🧪 Iniciando pruebas de configuración de correo...")
    print("=" * 60)
    
    success = test_email_configuration()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ RESULTADO: Configuración de correo funcionando correctamente")
        print("\n📋 Próximos pasos:")
        print("   1. La funcionalidad de reseteo de contraseña está lista")
        print("   2. Los líderes pueden resetear contraseñas desde /lider/usuarios")
        print("   3. Los correos se enviarán automáticamente")
    else:
        print("❌ RESULTADO: Hay problemas con la configuración de correo")
        print("\n🔧 Para solucionar:")
        print("   1. Revisa el archivo .env.example")
        print("   2. Configura las variables de correo en .env")
        print("   3. Ejecuta este script nuevamente")
    
    print("\n🔗 URLs de la aplicación:")
    print("   - http://127.0.0.1:5000")
    print("   - http://192.168.0.10:5000")