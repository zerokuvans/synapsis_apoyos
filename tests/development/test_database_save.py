#!/usr/bin/env python3
"""
Script para probar el guardado de usuarios en la base de datos
"""

from app import create_app, db
from app.models.usuario import Usuario
import random
import string

def generate_random_email():
    """Generar un email aleatorio para evitar conflictos"""
    random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"test_{random_string}@example.com"

def test_database_save():
    """Probar el guardado completo en la base de datos"""
    app = create_app()
    
    with app.app_context():
        try:
            # Generar email único
            email = generate_random_email()
            
            print(f"🔄 Creando usuario con email: {email}")
            
            # Crear usuario
            test_user = Usuario(
                email=email,
                password='test123',
                nombre='Test',
                apellido='Database',
                rol='tecnico',
                telefono='3001234567'
            )
            
            print("✅ Usuario creado en memoria")
            
            # Agregar a la sesión
            db.session.add(test_user)
            print("✅ Usuario agregado a la sesión")
            
            # Hacer commit
            db.session.commit()
            print("✅ Commit realizado exitosamente")
            
            # Verificar que se guardó obteniendo el ID
            user_id = test_user.id
            print(f"✅ Usuario guardado con ID: {user_id}")
            
            # Buscar el usuario en la base de datos
            found_user = Usuario.query.filter_by(email=email).first()
            
            if found_user:
                print("✅ Usuario encontrado en la base de datos:")
                print(f"   - ID: {found_user.id}")
                print(f"   - Email: {found_user.email}")
                print(f"   - Nombre: {found_user.get_nombre_completo()}")
                print(f"   - Rol: {found_user.rol}")
                print(f"   - Activo: {found_user.activo}")
                print(f"   - Fecha creación: {found_user.created_at}")
                
                # Limpiar - eliminar el usuario de prueba
                db.session.delete(found_user)
                db.session.commit()
                print("🧹 Usuario de prueba eliminado")
                
                print("\n🎉 ¡ÉXITO! El guardado en base de datos funciona correctamente")
                return True
            else:
                print("❌ ERROR: Usuario no encontrado en la base de datos después del commit")
                return False
                
        except Exception as e:
            print(f"❌ Error durante el proceso: {str(e)}")
            print(f"   Tipo de error: {type(e).__name__}")
            
            # Intentar rollback en caso de error
            try:
                db.session.rollback()
                print("🔄 Rollback realizado")
            except:
                pass
                
            return False

if __name__ == '__main__':
    success = test_database_save()
    if not success:
        print("\n❌ La prueba de guardado en base de datos FALLÓ")
        exit(1)
    else:
        print("\n✅ La prueba de guardado en base de datos fue EXITOSA")