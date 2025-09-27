# Synapsis Apoyos

Sistema de gestión de solicitudes de apoyo técnico con geolocalización en tiempo real.

## Descripción

Synapsis Apoyos es una aplicación web desarrollada en Flask que permite la gestión eficiente de solicitudes de apoyo técnico, con seguimiento en tiempo real de técnicos móviles y asignación automática basada en proximidad geográfica.

## Características Principales

- **Gestión de Usuarios**: Sistema de roles (Técnicos, Móviles, Líderes)
- **Geolocalización**: Seguimiento en tiempo real de técnicos móviles
- **Asignación Inteligente**: Asignación automática basada en proximidad
- **Dashboard Interactivo**: Mapas en tiempo real con Leaflet
- **Notificaciones**: Sistema de notificaciones por email
- **Reportes**: Exportación de datos a Excel
- **Seguridad**: Autenticación segura y gestión de sesiones

## Tecnologías

- **Backend**: Flask, SQLAlchemy, Flask-Login
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap
- **Base de Datos**: MySQL
- **Mapas**: Leaflet, OpenStreetMap
- **Tiempo Real**: Socket.IO
- **Email**: Flask-Mail

## Instalación

### Requisitos Previos

- Python 3.8+
- MySQL 8.0+
- Git

### Configuración

1. **Clonar el repositorio**
   ```bash
   git clone <repository-url>
   cd synapsis_apoyos
   ```

2. **Crear entorno virtual**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # source venv/bin/activate  # Linux/Mac
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**
   ```bash
   cp .env.example .env
   ```
   
   Editar `.env` con tus configuraciones:
   ```
   SECRET_KEY=tu-clave-secreta-muy-segura
   DATABASE_URL=mysql+pymysql://usuario:password@localhost/synapsis_apoyos
   GOOGLE_MAPS_API_KEY=tu-api-key-de-google-maps
   MAIL_USERNAME=tu-email@gmail.com
   MAIL_PASSWORD=tu-app-password
   FLASK_ENV=production
   FLASK_DEBUG=False
   ```

5. **Configurar base de datos**
   ```bash
   # Crear base de datos MySQL
   mysql -u root -p
   CREATE DATABASE synapsis_apoyos;
   ```

6. **Ejecutar la aplicación**
   ```bash
   python run.py
   ```

## Configuración de Producción

### Variables de Entorno Importantes

- `FLASK_ENV=production`
- `FLASK_DEBUG=False`
- `SECRET_KEY`: Clave secreta única y segura
- `DATABASE_URL`: URL de conexión a MySQL
- `GOOGLE_MAPS_API_KEY`: API Key de Google Maps
- `MAIL_*`: Configuración de correo electrónico

### Seguridad

- Cambiar `SECRET_KEY` por una clave única y segura
- Configurar HTTPS en producción
- Usar contraseñas seguras para la base de datos
- Configurar firewall apropiadamente
- Revisar logs regularmente

## Estructura del Proyecto

```
synapsis_apoyos/
├── app/
│   ├── blueprints/          # Módulos de la aplicación
│   │   ├── auth/           # Autenticación
│   │   ├── tecnico/        # Dashboard técnicos
│   │   ├── movil/          # Dashboard móviles
│   │   ├── lider/          # Dashboard líderes
│   │   └── api/            # API endpoints
│   ├── models/             # Modelos de base de datos
│   ├── templates/          # Plantillas HTML
│   ├── static/             # Archivos estáticos
│   └── utils/              # Utilidades
├── dev_files/              # Archivos de desarrollo
├── requirements.txt        # Dependencias
├── run.py                  # Punto de entrada
└── .env                    # Variables de entorno
```

## Uso

### Roles de Usuario

1. **Técnicos**: Crean solicitudes de apoyo
2. **Móviles**: Reciben y atienden solicitudes
3. **Líderes**: Supervisan y generan reportes

### Flujo de Trabajo

1. Técnico crea solicitud con ubicación
2. Sistema asigna automáticamente al móvil más cercano
3. Móvil recibe notificación y acepta/rechaza
4. Seguimiento en tiempo real hasta completar
5. Líder supervisa y genera reportes

## Soporte

Para soporte técnico o reportar problemas, contactar al equipo de desarrollo.

## Licencia

Propiedad de Synapsis Apoyos. Todos los derechos reservados.