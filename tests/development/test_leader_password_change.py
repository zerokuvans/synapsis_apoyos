#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.usuario import Usuario

def test_leader_password_change():
    """Probar el cambio de contraseña del líder"""
    app = create_app()
    
    with app.app_context():
        try:
            # Obtener el primer líder
            lider = Usuario.query.filter_by(rol='lider').first()
            
            if not lider:
                print("❌ No se encontró ningún líder")
                return
            
            print(f"🔍 Probando cambio de contraseña para: {lider.email}")
            print(f"👤 Nombre: {lider.get_nombre_completo()}")
            
            # Contraseña actual (asumiendo que es una de las comunes)
            password_actual = 'lider123'  # Cambiar por la contraseña real
            nueva_password = 'nuevaPassword123'
            
            # Verificar contraseña actual
            if not lider.check_password(password_actual):
                print(f"❌ La contraseña actual '{password_actual}' es incorrecta")
                print("💡 Intenta con una de estas contraseñas comunes:")
                passwords_to_test = ['password123', 'lider123', '123456', 'admin', 'password', 'synapsis123']
                
                for pwd in passwords_to_test:
                    if lider.check_password(pwd):
                        print(f"✅ Contraseña actual encontrada: {pwd}")
                        password_actual = pwd
                        break
                else:
                    print("❌ No se pudo encontrar la contraseña actual")
                    return
            
            print(f"✅ Contraseña actual verificada: {password_actual}")
            
            # Cambiar contraseña
            print(f"🔄 Cambiando contraseña a: {nueva_password}")
            lider.set_password(nueva_password)
            db.session.commit()
            
            # Verificar que la nueva contraseña funciona
            if lider.check_password(nueva_password):
                print("✅ ¡Contraseña cambiada exitosamente!")
                print(f"📧 Email: {lider.email}")
                print(f"🔑 Nueva contraseña: {nueva_password}")
                
                # Verificar que la contraseña anterior ya no funciona
                if not lider.check_password(password_actual):
                    print("✅ La contraseña anterior ya no es válida")
                else:
                    print("⚠️  ADVERTENCIA: La contraseña anterior aún funciona")
                    
            else:
                print("❌ Error: La nueva contraseña no funciona")
            
        except Exception as e:
            print(f"❌ Error probando cambio de contraseña: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    test_leader_password_change()