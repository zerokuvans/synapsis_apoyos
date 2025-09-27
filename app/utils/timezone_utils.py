from datetime import datetime
import pytz

# Zona horaria de Bogotá, Colombia
BOGOTA_TZ = pytz.timezone('America/Bogota')
UTC_TZ = pytz.UTC

def get_bogota_time():
    """Obtiene la hora actual en zona horaria de Bogotá"""
    utc_now = datetime.utcnow()
    utc_time = UTC_TZ.localize(utc_now)
    return utc_time.astimezone(BOGOTA_TZ)

def utc_to_bogota(utc_datetime):
    """Convierte un datetime UTC a zona horaria de Bogotá"""
    if utc_datetime.tzinfo is None:
        utc_time = UTC_TZ.localize(utc_datetime)
    else:
        utc_time = utc_datetime.astimezone(UTC_TZ)
    return utc_time.astimezone(BOGOTA_TZ)

def bogota_to_utc(bogota_datetime):
    """Convierte un datetime de Bogotá a UTC"""
    if bogota_datetime.tzinfo is None:
        bogota_time = BOGOTA_TZ.localize(bogota_datetime)
    else:
        bogota_time = bogota_datetime.astimezone(BOGOTA_TZ)
    return bogota_time.astimezone(UTC_TZ)

def format_bogota_time(utc_datetime, format_str='%d/%m/%Y %H:%M'):
    """Formatea un datetime UTC a string en zona horaria de Bogotá"""
    bogota_time = utc_to_bogota(utc_datetime)
    return bogota_time.strftime(format_str)

def get_bogota_timestamp():
    """Obtiene timestamp actual en zona horaria de Bogotá para base de datos"""
    return get_bogota_time().replace(tzinfo=None)  # Sin timezone info para MySQL