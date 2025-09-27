#!/usr/bin/env python3
"""
WSGI entry point para Synapsis Apoyos
Optimizado para producción con Gunicorn
"""

import os
import sys
from pathlib import Path

# Agregar el directorio de la aplicación al path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

# Configurar variables de entorno antes de importar la app
os.environ.setdefault('FLASK_ENV', 'production')

# Importar la aplicación
from app import create_app

# Crear la aplicación
app = create_app('production')

if __name__ == "__main__":
    # Para desarrollo local
    app.run(debug=False, host='0.0.0.0', port=5000)