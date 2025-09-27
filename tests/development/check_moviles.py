from app import create_app
from app.models.usuario import Usuario
from app.models.ubicacion import Ubicacion
from datetime import datetime, timedelta

app = create_app()
app.app_context().push()

print('=== USUARIOS MÓVILES ===')
moviles = Usuario.query.filter_by(rol='movil').all()
print(f'Total móviles: {len(moviles)}')
for m in moviles:
    print(f'ID: {m.id}, Nombre: {m.nombre}, Email: {m.email}, Activo: {m.activo}')

print('\n=== UBICACIONES ===')
ubicaciones = Ubicacion.query.all()
print(f'Total ubicaciones: {len(ubicaciones)}')
for u in ubicaciones:
    print(f'ID: {u.id}, Usuario: {u.usuario_id}, Lat: {u.latitud}, Lng: {u.longitud}, Activa: {u.activa}, Timestamp: {u.timestamp}')

print('\n=== UBICACIONES RECIENTES (últimos 30 min) ===')
tiempo_limite = datetime.utcnow() - timedelta(minutes=30)
ubicaciones_recientes = Ubicacion.query.filter(Ubicacion.timestamp >= tiempo_limite).all()
print(f'Ubicaciones recientes: {len(ubicaciones_recientes)}')
for u in ubicaciones_recientes:
    usuario = Usuario.query.get(u.usuario_id)
    print(f'Usuario: {usuario.nombre if usuario else "N/A"} ({usuario.rol if usuario else "N/A"}), Lat: {u.latitud}, Lng: {u.longitud}, Timestamp: {u.timestamp}')

print('\n=== MÓVILES CON UBICACIONES RECIENTES ===')
from app import db
moviles_query = db.session.query(Usuario, Ubicacion).join(
    Ubicacion, Usuario.id == Ubicacion.usuario_id
).filter(
    Usuario.rol == 'movil',
    Usuario.activo == True,
    Ubicacion.activa == True,
    Ubicacion.timestamp >= tiempo_limite
).all()

print(f'Móviles con ubicaciones recientes: {len(moviles_query)}')
for usuario, ubicacion in moviles_query:
    print(f'Móvil: {usuario.nombre}, Lat: {ubicacion.latitud}, Lng: {ubicacion.longitud}, Timestamp: {ubicacion.timestamp}')