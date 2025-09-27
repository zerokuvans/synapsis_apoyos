#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.usuario import Usuario

def check_users():
    """Verificar usuarios existentes en la base de datos"""
    app = create_app()
    
    with app.app_context():
        try:
            print("=== Usuarios en la Base de Datos ===")
            usuarios = Usuario.query.all()
            
            if not usuarios:
                print("❌ No hay usuarios en la base de datos")
                return
            
            print(f"📊 Total de usuarios: {len(usuarios)}")
            print()
            
            for usuario in usuarios:
                print(f"👤 ID: {usuario.id}")
                print(f"   📧 Email: {usuario.email}")
                print(f"   👨‍💼 Nombre: {usuario.get_nombre_completo()}")
                print(f"   🎭 Rol: {usuario.rol}")
                print(f"   ✅ Activo: {usuario.activo}")
                # print(f"   📅 Creado: {usuario.fecha_creacion}")  # Campo no disponible
                print("-" * 50)
            
            # Verificar si existe un líder
            lideres = Usuario.query.filter_by(rol='lider').all()
            print(f"\n👑 Líderes encontrados: {len(lideres)}")
            
            if lideres:
                for lider in lideres:
                    print(f"   📧 {lider.email} - {lider.get_nombre_completo()}")
            
        except Exception as e:
            print(f"❌ Error verificando usuarios: {str(e)}")

if __name__ == '__main__':
    check_users()