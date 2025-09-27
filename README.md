# Synapsis Apoyos

Sistema de gestión de apoyos estudiantiles desarrollado con Flask.

## 📁 Estructura del Proyecto

```
synapsis_apoyos/
├── 📁 app/                          # Aplicación principal
│   ├── 📁 blueprints/               # Módulos de la aplicación
│   │   ├── 📁 api/                  # API REST
│   │   ├── 📁 auth/                 # Autenticación
│   │   ├── 📁 lider/                # Módulo líder
│   │   ├── 📁 movil/                # Aplicación móvil
│   │   └── 📁 tecnico/              # Módulo técnico
│   ├── 📁 models/                   # Modelos de datos
│   ├── 📁 static/                   # Archivos estáticos
│   │   ├── 📁 css/                  # Estilos CSS
│   │   ├── 📁 js/                   # JavaScript
│   │   ├── 📁 img/                  # Imágenes
│   │   └── 📁 src/                  # Código fuente frontend
│   ├── 📁 templates/                # Plantillas HTML
│   └── 📁 utils/                    # Utilidades
├── 📁 deployment/                   # Configuración de deployment
│   ├── 📁 configs/                  # Archivos de configuración
│   ├── 📁 nginx/                    # Configuración Nginx
│   └── 📁 scripts/                  # Scripts de deployment
├── 📁 docs/                         # Documentación
├── 📁 migrations/                   # Migraciones de base de datos
├── 📁 tests/                        # Pruebas
├── 📁 venv/                         # Entorno virtual
├── 📄 config.py                     # Configuración principal
├── 📄 run.py                        # Punto de entrada
├── 📄 requirements.txt              # Dependencias Python
├── 📄 package.json                  # Dependencias Node.js
├── 📄 webpack.config.js             # Configuración Webpack
└── 📄 .gitignore                    # Archivos ignorados por Git
```

## 🚀 Inicio Rápido

### Prerrequisitos

- Python 3.8+
- Node.js 14+
- MySQL/PostgreSQL
- Git

### Instalación

1. **Clonar el repositorio**
   ```bash
   git clone <repository-url>
   cd synapsis_apoyos
   ```

2. **Configurar entorno virtual**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # o
   venv\Scripts\activate     # Windows
   ```

3. **Instalar dependencias Python**
   ```bash
   pip install -r requirements.txt
   ```

4. **Instalar dependencias Node.js**
   ```bash
   npm install
   ```

5. **Configurar variables de entorno**
   ```bash
   cp .env.example .env
   # Editar .env con tus configuraciones
   ```

6. **Configurar base de datos**
   ```bash
   flask db upgrade
   ```

7. **Compilar assets**
   ```bash
   npm run build
   ```

8. **Ejecutar la aplicación**
   ```bash
   python run.py
   ```

## 🛠️ Desarrollo

### Scripts Disponibles

- `npm run build` - Compilar assets para producción
- `npm run dev` - Compilar assets para desarrollo
- `npm run watch` - Compilar assets en modo watch
- `npm run lint` - Ejecutar linters
- `flask db migrate` - Crear nueva migración
- `flask db upgrade` - Aplicar migraciones

### Estructura de Desarrollo

- **Frontend**: SCSS + JavaScript ES6+ con Webpack
- **Backend**: Flask con Blueprint pattern
- **Base de datos**: SQLAlchemy ORM
- **Autenticación**: Flask-Login
- **API**: RESTful con Flask-RESTful

## 📚 Documentación

La documentación completa está disponible en el directorio `docs/`:

- [📖 Arquitectura del Sistema](docs/ARCHITECTURE.md)
- [🚀 Guía de Deployment](docs/DEPLOYMENT.md)
- [✅ Checklist de Producción](docs/PRODUCTION_CHECKLIST.md)
- [📋 Implementación de Rutas](docs/IMPLEMENTACION_RUTAS_INTERNAS.md)

## 🔧 Deployment

### Desarrollo

```bash
# Windows
deployment\scripts\start_development.bat

# Linux/Mac
./deployment/scripts/start_production.sh
```

### Producción

1. **Configurar servidor**
   ```bash
   # Seguir la guía en docs/DEPLOYMENT.md
   ./deployment/scripts/deploy.sh
   ```

2. **Configurar SSL**
   ```bash
   ./deployment/scripts/setup_ssl.sh tudominio.com
   ```

3. **Configurar monitoreo**
   ```bash
   ./deployment/scripts/setup_monitoring.sh
   ```

## 🔒 Seguridad

- Autenticación basada en sesiones
- Protección CSRF
- Rate limiting
- Headers de seguridad
- Validación de entrada
- Sanitización de datos

## 📊 Monitoreo

- Logging estructurado
- Métricas de performance
- Health checks
- Alertas automáticas
- Integración con Prometheus/Grafana

## 💾 Backup

Los scripts de backup están automatizados:

- **Backup diario**: Base de datos y archivos críticos
- **Backup semanal**: Backup completo del sistema
- **Backup mensual**: Archivo histórico
- **Restauración**: Scripts automatizados de restauración

## 🧪 Testing

```bash
# Ejecutar todas las pruebas
python -m pytest

# Ejecutar pruebas específicas
python -m pytest tests/unit/
python -m pytest tests/integration/

# Coverage
python -m pytest --cov=app
```

## 🤝 Contribución

1. Fork el proyecto
2. Crear una rama feature (`git checkout -b feature/AmazingFeature`)
3. Commit los cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

## 📞 Soporte

Para soporte técnico o consultas:

- 📧 Email: soporte@synapsis.com
- 📱 Teléfono: +1234567890
- 🌐 Web: https://synapsis.com

## 🔄 Changelog

Ver [CHANGELOG.md](CHANGELOG.md) para un historial detallado de cambios.

---

**Desarrollado con ❤️ por el equipo de Synapsis**