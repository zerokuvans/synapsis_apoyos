#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import requests
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.usuario import Usuario

def test_profile_api():
    """Probar las APIs del perfil del líder"""
    app = create_app()
    
    with app.app_context():
        try:
            # Obtener el líder
            lider = Usuario.query.filter_by(rol='lider').first()
            
            if not lider:
                print("❌ No se encontró ningún líder")
                return
            
            print(f"🔍 Probando APIs de perfil para: {lider.email}")
            print(f"👤 Nombre: {lider.get_nombre_completo()}")
            
            # Restablecer contraseña conocida para las pruebas
            print("\n🔄 Restableciendo contraseña conocida para pruebas...")
            lider.set_password('lider123')
            db.session.commit()
            print("✅ Contraseña restablecida a 'lider123'")
            
            # Configurar sesión para mantener cookies
            session = requests.Session()
            
            # 1. Hacer login
            print("\n1️⃣ Haciendo login...")
            login_data = {
                'email': lider.email,
                'password': 'lider123'
            }
            
            login_response = session.post('http://127.0.0.1:5000/auth/login', data=login_data)
            
            if login_response.status_code == 200 and ('dashboard' in login_response.url or 'lider' in login_response.url):
                print("✅ Login exitoso")
            else:
                print(f"❌ Error en login: {login_response.status_code}")
                print(f"URL de respuesta: {login_response.url}")
                return
            
            # 2. Probar actualización de información personal
            print("\n2️⃣ Probando actualización de información personal...")
            info_data = {
                'nombre': 'Roberto',
                'apellido': 'Rodríguez',
                'telefono': '3001234567',
                'email': lider.email
            }
            
            info_response = session.post(
                'http://127.0.0.1:5000/lider/perfil/actualizar-informacion',
                json=info_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if info_response.status_code == 200:
                result = info_response.json()
                if result.get('success'):
                    print(f"✅ Información actualizada: {result.get('message')}")
                else:
                    print(f"❌ Error actualizando información: {result.get('message')}")
            else:
                print(f"❌ Error HTTP actualizando información: {info_response.status_code}")
                print(f"Respuesta: {info_response.text}")
            
            # 3. Probar cambio de contraseña
            print("\n3️⃣ Probando cambio de contraseña...")
            password_data = {
                'password_actual': 'lider123',
                'password_nueva': 'nuevaPassword456',
                'password_confirmar': 'nuevaPassword456'
            }
            
            password_response = session.post(
                'http://127.0.0.1:5000/lider/perfil/cambiar-password',
                json=password_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if password_response.status_code == 200:
                result = password_response.json()
                if result.get('success'):
                    print(f"✅ Contraseña cambiada: {result.get('message')}")
                    
                    # Verificar que la nueva contraseña funciona en la base de datos
                    # Refrescar la sesión para obtener los datos actualizados
                    db.session.refresh(lider)
                    if lider.check_password('nuevaPassword456'):
                        print("✅ Nueva contraseña verificada en base de datos")
                    else:
                        print("❌ Nueva contraseña NO funciona en base de datos")
                        
                    # Verificar que la contraseña anterior ya no funciona
                    if not lider.check_password('lider123'):
                        print("✅ Contraseña anterior ya no es válida")
                    else:
                        print("❌ Contraseña anterior aún funciona (problema)")
                        
                else:
                    print(f"❌ Error cambiando contraseña: {result.get('message')}")
            else:
                print(f"❌ Error HTTP cambiando contraseña: {password_response.status_code}")
                print(f"Respuesta: {password_response.text}")
            
            # 4. Verificar información actualizada
            print("\n4️⃣ Verificando información actualizada en base de datos...")
            db.session.refresh(lider)
            print(f"📧 Email: {lider.email}")
            print(f"👤 Nombre: {lider.get_nombre_completo()}")
            print(f"📱 Teléfono: {lider.telefono}")
            
            # 5. Probar login con nueva contraseña
            print("\n5️⃣ Probando login con nueva contraseña...")
            new_session = requests.Session()
            new_login_data = {
                'email': lider.email,
                'password': 'nuevaPassword456'
            }
            
            new_login_response = new_session.post('http://127.0.0.1:5000/auth/login', data=new_login_data)
            
            if new_login_response.status_code == 200 and ('dashboard' in new_login_response.url or 'lider' in new_login_response.url):
                print("✅ Login con nueva contraseña exitoso")
            else:
                print(f"❌ Error en login con nueva contraseña: {new_login_response.status_code}")
            
            print("\n🎉 ¡Todas las pruebas completadas!")
            
        except Exception as e:
            print(f"❌ Error en las pruebas: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    test_profile_api()