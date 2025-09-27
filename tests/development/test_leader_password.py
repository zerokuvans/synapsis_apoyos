#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.usuario import Usuario

def test_leader_password():
    """Probar contraseñas comunes para el líder"""
    app = create_app()
    
    with app.app_context():
        try:
            # Obtener el primer líder
            lider = Usuario.query.filter_by(rol='lider').first()
            
            if not lider:
                print("❌ No se encontró ningún líder")
                return
            
            print(f"🔍 Probando contraseñas para: {lider.email}")
            
            # Contraseñas comunes a probar
            passwords_to_test = [
                'password123',
                'lider123',
                '123456',
                'admin',
                'password',
                'synapsis123',
                'lider1',
                'roberto123'
            ]
            
            for password in passwords_to_test:
                if lider.check_password(password):
                    print(f"✅ CONTRASEÑA ENCONTRADA: {password}")
                    print(f"📧 Email: {lider.email}")
                    print(f"👤 Nombre: {lider.get_nombre_completo()}")
                    return
                else:
                    print(f"❌ {password} - Incorrecta")
            
            print("\n❌ Ninguna contraseña común funcionó")
            print("💡 Sugerencia: Crear un nuevo usuario líder para pruebas")
            
        except Exception as e:
            print(f"❌ Error probando contraseñas: {str(e)}")

if __name__ == '__main__':
    test_leader_password()