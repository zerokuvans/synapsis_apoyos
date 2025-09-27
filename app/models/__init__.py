# Importar todos los modelos para que estén disponibles
from .usuario import Usuario
from .solicitud import Solicitud
from .servicio import Servicio
from .ubicacion import Ubicacion
from .observacion import Observacion
from .vehiculo import Vehiculo

__all__ = ['Usuario', 'Solicitud', 'Servicio', 'Ubicacion', 'Observacion', 'Vehiculo']