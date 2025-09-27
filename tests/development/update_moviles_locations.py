from app import create_app
from app.models.ubicacion import Ubicacion
from app import db
from datetime import datetime

app = create_app()
app.app_context().push()

print('=== ACTUALIZANDO UBICACIONES DE MÓVILES ===')

# Obtener todas las ubicaciones de móviles
ubicaciones = Ubicacion.query.all()
print(f'Total ubicaciones encontradas: {len(ubicaciones)}')

# Actualizar timestamps a la fecha/hora actual
for ubicacion in ubicaciones:
    ubicacion.timestamp = datetime.utcnow()
    print(f'Actualizando ubicación ID {ubicacion.id} para usuario {ubicacion.usuario_id}')

# Guardar cambios
try:
    db.session.commit()
    print('✅ Ubicaciones actualizadas exitosamente!')
except Exception as e:
    db.session.rollback()
    print(f'❌ Error actualizando ubicaciones: {e}')

# Verificar las ubicaciones actualizadas
print('\n=== VERIFICANDO UBICACIONES ACTUALIZADAS ===')
ubicaciones_actualizadas = Ubicacion.query.all()
for u in ubicaciones_actualizadas:
    print(f'ID: {u.id}, Usuario: {u.usuario_id}, Timestamp: {u.timestamp}, Activa: {u.activa}')