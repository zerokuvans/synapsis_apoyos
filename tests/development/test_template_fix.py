#!/usr/bin/env python3
"""
Script para probar que la plantilla de correo funcione correctamente
sin enviar correos reales
"""

from app import create_app
from app.models.usuario import Usuario
from app.utils.password_utils import generate_temporary_password
from app.utils.timezone_utils import get_bogota_timestamp, format_bogota_time
from flask import render_template

def test_template_rendering():
    """Prueba que la plantilla se renderice correctamente"""
    app = create_app()
    
    with app.app_context():
        print("🧪 Probando renderizado de plantilla de correo...")
        print("=" * 50)
        
        # 1. Buscar un usuario de prueba
        print("1. Buscando usuario de prueba...")
        usuario_prueba = Usuario.query.filter(
            Usuario.email.isnot(None),
            Usuario.email != ''
        ).first()
        
        if not usuario_prueba:
            print("❌ No se encontró ningún usuario con email para prueba")
            return False
        
        print(f"✅ Usuario encontrado: {usuario_prueba.get_nombre_completo()} ({usuario_prueba.email})")
        
        # 2. Generar contraseña temporal
        print("\n2. Generando contraseña temporal...")
        nueva_password = generate_temporary_password()
        print(f"✅ Contraseña temporal: {nueva_password}")
        
        # 3. Obtener fecha de reseteo
        print("\n3. Obteniendo fecha de reseteo...")
        fecha_reseteo = format_bogota_time(get_bogota_timestamp())
        print(f"✅ Fecha de reseteo: {fecha_reseteo}")
        
        # 4. Probar renderizado de plantilla
        print("\n4. Probando renderizado de plantilla...")
        try:
            html_content = render_template(
                'emails/password_reset.html',
                usuario=usuario_prueba,
                nueva_password=nueva_password,
                fecha_reseteo=fecha_reseteo
            )
            
            print("✅ Plantilla renderizada exitosamente!")
            print(f"   Longitud del HTML: {len(html_content)} caracteres")
            
            # 5. Verificar que los campos se hayan reemplazado correctamente
            print("\n5. Verificando contenido de la plantilla...")
            
            # Verificar que no haya errores de atributos
            if "{{ usuario.usuario }}" in html_content:
                print("❌ ERROR: Aún hay referencias a 'usuario.usuario' en la plantilla")
                return False
            
            # Verificar que los campos correctos estén presentes
            checks = [
                (usuario_prueba.email, "Email del usuario"),
                (usuario_prueba.nombre, "Nombre del usuario"),
                (usuario_prueba.apellido, "Apellido del usuario"),
                (nueva_password, "Nueva contraseña"),
                (fecha_reseteo, "Fecha de reseteo"),
                (usuario_prueba.rol.title(), "Rol del usuario")
            ]
            
            all_checks_passed = True
            for value, description in checks:
                if str(value) in html_content:
                    print(f"   ✅ {description}: {value}")
                else:
                    print(f"   ❌ {description}: {value} NO encontrado")
                    all_checks_passed = False
            
            if all_checks_passed:
                print("\n🎉 Todas las verificaciones pasaron exitosamente!")
                print("✅ La plantilla de correo está funcionando correctamente")
                return True
            else:
                print("\n❌ Algunas verificaciones fallaron")
                return False
                
        except Exception as e:
            print(f"❌ Error al renderizar plantilla: {str(e)}")
            return False

if __name__ == "__main__":
    print("🧪 Iniciando prueba de plantilla de correo...")
    print("=" * 60)
    
    success = test_template_rendering()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ RESULTADO: La plantilla de correo funciona correctamente")
        print("\n📋 El error 'Usuario' object has no attribute 'usuario' ha sido corregido")
        print("   Ahora la funcionalidad de reseteo de contraseña debería funcionar")
        print("   (solo necesitas configurar las credenciales de correo en .env)")
    else:
        print("❌ RESULTADO: Hay problemas con la plantilla de correo")
    
    print("\n🔗 URLs de la aplicación:")
    print("   - http://127.0.0.1:5000")
    print("   - http://192.168.0.10:5000")