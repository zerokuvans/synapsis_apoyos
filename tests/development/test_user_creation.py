#!/usr/bin/env python3
"""
Script para probar la creación de usuarios después de las correcciones
"""

from app import create_app, db
from app.models.usuario import Usuario

def test_user_creation():
    """Probar la creación de usuarios"""
    app = create_app()
    
    with app.app_context():
        try:
            # Probar creación de usuario con el constructor corregido
            test_user = Usuario(
                email='test@example.com',
                password='test123',
                nombre='Test',
                apellido='User',
                rol='tecnico',
                telefono='3001234567'
            )
            
            print("✅ Usuario creado exitosamente:")
            print(f"   - Email: {test_user.email}")
            print(f"   - Nombre: {test_user.get_nombre_completo()}")
            print(f"   - Rol: {test_user.rol}")
            print(f"   - Activo: {test_user.activo}")
            print(f"   - Teléfono: {test_user.telefono}")
            
            # Verificar que el campo activo tenga el valor por defecto
            assert test_user.activo == True, "El campo activo debería ser True por defecto"
            
            # Verificar que la contraseña se haya establecido correctamente
            assert test_user.check_password('test123'), "La contraseña no se estableció correctamente"
            
            print("\n🎉 Todas las pruebas pasaron exitosamente!")
            
        except Exception as e:
            print(f"❌ Error en la creación de usuario: {str(e)}")
            return False
    
    return True

if __name__ == '__main__':
    test_user_creation()