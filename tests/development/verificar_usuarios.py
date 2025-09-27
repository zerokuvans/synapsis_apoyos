from app import create_app
from app.models.usuario import Usuario

def verificar_usuarios():
    """Verificar usuarios existentes en la base de datos"""
    app = create_app()
    
    with app.app_context():
        print("=== USUARIOS EN LA BASE DE DATOS ===")
        
        usuarios = Usuario.query.all()
        print(f"📊 Total usuarios: {len(usuarios)}")
        
        if usuarios:
            for usuario in usuarios:
                print(f"\n👤 Usuario #{usuario.id}:")
                print(f"   Nombre: {usuario.nombre} {usuario.apellido}")
                print(f"   Email: {usuario.email}")
                print(f"   Rol: {usuario.rol}")
                print(f"   Activo: {usuario.activo}")
                print(f"   Teléfono: {usuario.telefono}")
                print(f"   Creado: {usuario.created_at}")
        else:
            print("❌ No hay usuarios en la base de datos")
            
        print("\n=== TÉCNICOS ESPECÍFICAMENTE ===")
        tecnicos = Usuario.query.filter_by(rol='tecnico').all()
        print(f"📊 Total técnicos: {len(tecnicos)}")
        
        for tecnico in tecnicos:
            print(f"\n👨‍🔧 Técnico:")
            print(f"   Nombre: {tecnico.nombre} {tecnico.apellido}")
            print(f"   Email: {tecnico.email}")
            print(f"   Activo: {tecnico.activo}")

if __name__ == '__main__':
    verificar_usuarios()