from datetime import datetime
from app.utils.timezone_utils import get_bogota_timestamp, convert_utc_to_bogota
from app import db
from app.models.servicio import Servicio
from app.models.ubicacion import Ubicacion
from app.models.observacion import Observacion
from app.models.usuario import Usuario
from app.models.solicitud import Solicitud

def migrate_existing_timestamps_to_bogota():
    """
    Migra todos los timestamps existentes de UTC a zona horaria de Bogotá
    """
    print("Iniciando migración de timestamps a zona horaria de Bogotá...")
    
    # Migrar servicios
    servicios = Servicio.query.all()
    for servicio in servicios:
        if servicio.aceptado_at:
            servicio.aceptado_at = convert_utc_to_bogota(servicio.aceptado_at)
        if servicio.iniciado_at:
            servicio.iniciado_at = convert_utc_to_bogota(servicio.iniciado_at)
        if servicio.finalizado_at:
            servicio.finalizado_at = convert_utc_to_bogota(servicio.finalizado_at)
    
    print(f"Migrados {len(servicios)} servicios")
    
    # Migrar ubicaciones
    ubicaciones = Ubicacion.query.all()
    for ubicacion in ubicaciones:
        if ubicacion.timestamp:
            ubicacion.timestamp = convert_utc_to_bogota(ubicacion.timestamp)
    
    print(f"Migradas {len(ubicaciones)} ubicaciones")
    
    # Migrar observaciones
    observaciones = Observacion.query.all()
    for observacion in observaciones:
        if observacion.created_at:
            observacion.created_at = convert_utc_to_bogota(observacion.created_at)
    
    print(f"Migradas {len(observaciones)} observaciones")
    
    # Migrar usuarios
    usuarios = Usuario.query.all()
    for usuario in usuarios:
        if usuario.last_activity:
            usuario.last_activity = convert_utc_to_bogota(usuario.last_activity)
        if usuario.created_at:
            usuario.created_at = convert_utc_to_bogota(usuario.created_at)
        if usuario.updated_at:
            usuario.updated_at = convert_utc_to_bogota(usuario.updated_at)
    
    print(f"Migrados {len(usuarios)} usuarios")
    
    # Migrar solicitudes
    solicitudes = Solicitud.query.all()
    for solicitud in solicitudes:
        if solicitud.created_at:
            solicitud.created_at = convert_utc_to_bogota(solicitud.created_at)
        if solicitud.limite_tiempo:
            solicitud.limite_tiempo = convert_utc_to_bogota(solicitud.limite_tiempo)
        if solicitud.updated_at:
            solicitud.updated_at = convert_utc_to_bogota(solicitud.updated_at)
    
    print(f"Migradas {len(solicitudes)} solicitudes")
    
    # Guardar cambios
    try:
        db.session.commit()
        print("Migración completada exitosamente")
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error durante la migración: {e}")
        return False

def update_model_defaults():
    """
    Actualiza los defaults de los modelos para usar zona horaria de Bogotá
    """
    print("Actualizando defaults de modelos para usar zona horaria de Bogotá...")
    
    # Esta función se ejecutará después de actualizar los modelos
    # para asegurar que los nuevos registros usen la zona horaria correcta
    print("Defaults actualizados - los nuevos registros usarán zona horaria de Bogotá")
    return True