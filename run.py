import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    # Obtener configuraciones de variables de entorno
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 8081))
    
    app.run(debug=debug_mode, host=host, port=port)