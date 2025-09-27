/**
 * Sistema de Permisos de Geolocalización
 * Maneja la solicitud obligatoria de permisos de ubicación
 * y bloquea la funcionalidad hasta que se otorguen
 */

class GeolocationPermissionManager {
    constructor() {
        this.permissionGranted = false;
        this.watchId = null;
        this.currentPosition = null;
        this.permissionCheckInterval = null;
        this.overlayElement = null;
        this.retryCount = 0;
        this.maxRetries = 5;
        this.isCheckingPermissions = false;
        this.permissionCache = {
            state: null,
            timestamp: null,
            cacheTimeout: 30000 // 30 segundos
        };
        
        // Cargar cache desde localStorage
        this.loadCacheFromStorage();
        
        // Inicializar inmediatamente
        this.init();
    }
    
    // Método para limpiar recursos cuando sea necesario
    cleanup() {
        if (this.permissionCheckInterval) {
            clearInterval(this.permissionCheckInterval);
            this.permissionCheckInterval = null;
        }
        
        // Remover event listeners
        window.removeEventListener('focus', this.handleWindowFocus);
        document.removeEventListener('visibilitychange', this.handleVisibilityChange);
    }
    
    // Métodos para manejar eventos (necesarios para poder removerlos)
    handleWindowFocus = () => {
        this.checkGeolocationPermission();
    }
    
    handleVisibilityChange = () => {
        if (!document.hidden) {
            this.checkGeolocationPermission();
        }
    }
    
    // Método para reiniciar la verificación de permisos
    restartPermissionChecking() {
        this.cleanup();
        this.retryCount = 0;
        this.init();
    }
    
    // Sistema de reintento automático con backoff exponencial
    retryPermissionCheck() {
        if (this.retryCount >= this.maxRetries) {
            this.showPermissionStatus('error', 'No se pudo verificar los permisos después de varios intentos. Por favor, recarga la página.');
            return;
        }
        
        this.retryCount++;
        const delay = Math.min(1000 * Math.pow(2, this.retryCount - 1), 30000); // Max 30 segundos
        
        console.log(`Reintentando verificación de permisos en ${delay}ms (intento ${this.retryCount}/${this.maxRetries})`);
        
        setTimeout(() => {
            this.checkGeolocationPermission();
        }, delay);
    }
    
    // Detectar si el usuario está en modo incógnito (puede afectar permisos)
    isIncognitoMode() {
        return new Promise((resolve) => {
            if ('storage' in navigator && 'estimate' in navigator.storage) {
                navigator.storage.estimate().then(estimate => {
                    resolve(estimate.quota < 120000000); // Menos de ~120MB sugiere modo incógnito
                });
            } else {
                resolve(false);
            }
        });
    }
    
    // Verificar conectividad de red
    checkNetworkStatus() {
        if ('onLine' in navigator) {
            if (!navigator.onLine) {
                this.showPermissionStatus('warning', 'Sin conexión a internet. Algunas funciones pueden no estar disponibles.');
                return false;
            }
        }
        return true;
    }
    
    async init() {
        console.log('Inicializando GeolocationPermissionManager...');
        
        // Verificar estado de permisos silenciosamente primero
        const permissionState = await this.checkPermissionStateQuietly();
        
        if (permissionState === 'granted') {
            // Si ya están otorgados, no mostrar overlay
            this.permissionGranted = true;
            this.startLocationTracking();
            console.log('Permisos ya otorgados, iniciando seguimiento silencioso');
            return;
        }
        
        // Solo crear y mostrar overlay si los permisos no están otorgados
        if (permissionState === 'denied' || permissionState === 'prompt' || permissionState === 'unknown') {
            this.createOverlay();
            // Verificar permisos con UI
            this.checkGeolocationPermission();
        } else {
            console.log('Permisos en estado:', permissionState, '- No se requiere overlay');
        }
        
        // Configurar verificación periódica solo si es necesario
        if (permissionState !== 'granted') {
            this.startBackgroundPermissionMonitoring();
        }
        
        // Verificar permisos cuando la ventana recupera el foco
        window.addEventListener('focus', this.handleWindowFocus);
        
        // Verificar permisos cuando cambia la visibilidad de la página
        document.addEventListener('visibilitychange', this.handleVisibilityChange);
    }
    
    createBlockingOverlay() {
        // Crear overlay que bloquea toda la interfaz
        this.overlayElement = document.createElement('div');
        this.overlayElement.id = 'geolocation-permission-overlay';
        this.overlayElement.innerHTML = `
            <div class="permission-modal">
                <div class="permission-content">
                    <div class="permission-icon">
                        <i class="fas fa-map-marker-alt"></i>
                    </div>
                    <h3>Permisos de Ubicación Requeridos</h3>
                    <p>Esta aplicación necesita acceso a su ubicación para funcionar correctamente.</p>
                    <p><strong>¿Por qué necesitamos su ubicación?</strong></p>
                    <ul>
                        <li>Mostrar técnicos y móviles cercanos</li>
                        <li>Calcular distancias y rutas óptimas</li>
                        <li>Asignar servicios basados en proximidad</li>
                        <li>Proporcionar navegación precisa</li>
                    </ul>
                    <div class="permission-buttons">
                        <button id="request-permission-btn" class="btn btn-primary">
                            <i class="fas fa-location-arrow me-2"></i>
                            Permitir Ubicación
                        </button>
                        <button id="refresh-permission-btn" class="btn btn-secondary" style="display: none;">
                            <i class="fas fa-refresh me-2"></i>
                            Verificar Permisos
                        </button>
                    </div>
                    <div id="permission-status" class="permission-status"></div>
                </div>
            </div>
        `;
        
        // Estilos CSS para el overlay
        const style = document.createElement('style');
        style.textContent = `
            #geolocation-permission-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.8);
                z-index: 9999;
                display: flex;
                align-items: center;
                justify-content: center;
                backdrop-filter: blur(5px);
            }
            
            .permission-modal {
                background: white;
                border-radius: 15px;
                padding: 0;
                max-width: 500px;
                width: 90%;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
                animation: slideIn 0.3s ease-out;
            }
            
            .permission-content {
                padding: 30px;
                text-align: center;
            }
            
            .permission-icon {
                font-size: 4rem;
                color: #2563EB;
                margin-bottom: 20px;
            }
            
            .permission-modal h3 {
                color: #1F2937;
                margin-bottom: 15px;
                font-weight: 600;
            }
            
            .permission-modal p {
                color: #6B7280;
                margin-bottom: 15px;
                line-height: 1.6;
            }
            
            .permission-modal ul {
                text-align: left;
                color: #6B7280;
                margin-bottom: 25px;
            }
            
            .permission-modal li {
                margin-bottom: 8px;
            }
            
            .permission-buttons {
                margin-bottom: 20px;
            }
            
            .permission-buttons .btn {
                margin: 5px;
                padding: 12px 24px;
                font-weight: 500;
            }
            
            .permission-status {
                padding: 10px;
                border-radius: 8px;
                font-weight: 500;
                display: none;
            }
            
            .permission-status.error {
                background-color: #FEE2E2;
                color: #991B1B;
                display: block;
            }
            
            .permission-status.success {
                background-color: #D1FAE5;
                color: #065F46;
                display: block;
            }
            
            .permission-status.warning {
                background-color: #FEF3C7;
                color: #92400E;
                display: block;
            }
            
            @keyframes slideIn {
                from {
                    opacity: 0;
                    transform: translateY(-50px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            @media (max-width: 768px) {
                .permission-modal {
                    width: 95%;
                }
                
                .permission-content {
                    padding: 20px;
                }
                
                .permission-icon {
                    font-size: 3rem;
                }
            }
        `;
        
        document.head.appendChild(style);
        document.body.appendChild(this.overlayElement);
        
        // Agregar event listeners
        document.getElementById('request-permission-btn').addEventListener('click', () => {
            this.requestGeolocationPermission();
        });
        
        document.getElementById('refresh-permission-btn').addEventListener('click', () => {
            this.checkGeolocationPermission();
        });
    }
    
    async checkPermissionStateQuietly() {
        // Verificar cache primero
        if (this.isCacheValid()) {
            console.log('Usando estado de permisos desde cache:', this.permissionCache.state);
            return this.permissionCache.state;
        }
        
        if (!navigator.geolocation) {
            return 'unsupported';
        }
        
        // Verificar usando permissions API si está disponible
        if (navigator.permissions && navigator.permissions.query) {
            try {
                const result = await navigator.permissions.query({name: 'geolocation'});
                this.updatePermissionCache(result.state);
                return result.state;
            } catch (error) {
                console.error('Error al verificar permisos silenciosamente:', error);
                return 'unknown';
            }
        }
        
        return 'unknown';
    }
    
    updatePermissionCache(state) {
        this.permissionCache.state = state;
        this.permissionCache.timestamp = Date.now();
        console.log('Cache de permisos actualizado:', state);
        
        // Guardar en localStorage para persistencia
        this.saveCacheToStorage();
    }
    
    loadCacheFromStorage() {
        try {
            const cachedData = localStorage.getItem('geolocation_permission_cache');
            if (cachedData) {
                const parsed = JSON.parse(cachedData);
                const cacheAge = Date.now() - parsed.timestamp;
                
                // Solo usar cache si no ha expirado
                if (cacheAge < this.permissionCache.cacheTimeout) {
                    this.permissionCache = parsed;
                    console.log('Cache de permisos cargado desde localStorage:', parsed.state);
                } else {
                    console.log('Cache de permisos expirado, limpiando localStorage');
                    this.clearCacheFromStorage();
                }
            }
        } catch (error) {
            console.error('Error al cargar cache desde localStorage:', error);
            this.clearCacheFromStorage();
        }
    }
    
    saveCacheToStorage() {
        try {
            localStorage.setItem('geolocation_permission_cache', JSON.stringify(this.permissionCache));
        } catch (error) {
            console.error('Error al guardar cache en localStorage:', error);
        }
    }
    
    clearCacheFromStorage() {
        try {
            localStorage.removeItem('geolocation_permission_cache');
            this.permissionCache = {
                state: null,
                timestamp: null,
                cacheTimeout: 30000
            };
        } catch (error) {
            console.error('Error al limpiar cache de localStorage:', error);
        }
    }
    
    isCacheValid() {
        if (!this.permissionCache.state || !this.permissionCache.timestamp) {
            return false;
        }
        
        const cacheAge = Date.now() - this.permissionCache.timestamp;
        return cacheAge < this.permissionCache.cacheTimeout;
    }
    
    checkGeolocationPermission() {
        // Evitar verificaciones concurrentes
        if (this.isCheckingPermissions) {
            console.log('Verificación de permisos ya en progreso, saltando...');
            return;
        }
        
        this.isCheckingPermissions = true;
        
        // Verificar conectividad de red
        if (!this.checkNetworkStatus()) {
            this.isCheckingPermissions = false;
            return;
        }
        
        if (!navigator.geolocation) {
            this.showPermissionStatus('error', 'Tu navegador no soporta geolocalización');
            this.isCheckingPermissions = false;
            return;
        }

        // Verificar usando permissions API si está disponible
        if (navigator.permissions && navigator.permissions.query) {
            navigator.permissions.query({name: 'geolocation'})
                .then((result) => {
                    console.log('Estado de permisos:', result.state);
                    this.updatePermissionCache(result.state);
                    this.retryCount = 0; // Reset retry count on successful check
                    
                    if (result.state === 'granted') {
                        this.handlePermissionGranted();
                    } else if (result.state === 'denied') {
                        this.handlePermissionDenied();
                    } else if (result.state === 'prompt') {
                        this.handlePermissionPrompt();
                    } else {
                        this.handleUnknownPermissionState();
                    }
                    
                    // Escuchar cambios en el estado de permisos
                    result.onchange = () => {
                        console.log('Cambio en permisos detectado:', result.state);
                        this.updatePermissionCache(result.state);
                        if (result.state === 'granted') {
                            this.handlePermissionGranted();
                        } else {
                            setTimeout(() => this.checkGeolocationPermission(), 100);
                        }
                    };
                    
                    this.isCheckingPermissions = false;
                })
                .catch((error) => {
                    console.error('Error al verificar permisos:', error);
                    this.isCheckingPermissions = false;
                    this.retryPermissionCheck();
                });
        } else {
            // Fallback para navegadores que no soportan permissions API
            this.fallbackPermissionCheck();
        }
    }
    
    fallbackPermissionCheck() {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                console.log('Ubicación obtenida exitosamente');
                this.currentPosition = position;
                this.retryCount = 0; // Reset retry count on success
                this.handlePermissionGranted();
                this.isCheckingPermissions = false;
            },
            (error) => {
                console.error('Error de geolocalización:', error);
                this.isCheckingPermissions = false;
                
                let message = 'No se pudo acceder a tu ubicación. ';
                let shouldRetry = false;
                
                switch(error.code) {
                    case error.PERMISSION_DENIED:
                        message += 'Permisos denegados. Por favor, habilita la ubicación en tu navegador.';
                        this.showRefreshButton();
                        break;
                    case error.POSITION_UNAVAILABLE:
                        message += 'Ubicación no disponible. Verifica tu conexión GPS.';
                        shouldRetry = true;
                        break;
                    case error.TIMEOUT:
                        message += 'Tiempo de espera agotado. Reintentando...';
                        shouldRetry = true;
                        break;
                    default:
                        message += 'Error desconocido. Reintentando...';
                        shouldRetry = true;
                        break;
                }
                
                this.showPermissionStatus('error', message);
                
                // Reintentar automáticamente para errores recuperables
                if (shouldRetry && this.retryCount < this.maxRetries) {
                    setTimeout(() => {
                        this.retryPermissionCheck();
                    }, 2000);
                }
            },
            {
                timeout: 15000,
                enableHighAccuracy: false,
                maximumAge: 300000
            }
        );
    }
    
    requestGeolocationPermission() {
        // Validar que geolocation esté disponible
        if (!navigator.geolocation) {
            console.error('Geolocation no está soportado por este navegador');
            this.showPermissionStatus('error', 
                'Tu navegador no soporta geolocalización.\n' +
                'Actualiza tu navegador o usa uno más moderno.');
            return;
        }

        // Validar que estemos en un contexto seguro (HTTPS o localhost)
        if (location.protocol !== 'https:' && location.hostname !== 'localhost' && location.hostname !== '127.0.0.1') {
            console.warn('Geolocation requiere HTTPS en producción');
            this.showPermissionStatus('warning', 
                'La geolocalización requiere una conexión segura (HTTPS).\n' +
                'Algunas funciones pueden no estar disponibles.');
        }

        this.showPermissionStatus('warning', 'Solicitando permisos de ubicación...');
        
        try {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    this.currentPosition = position;
                    this.handlePermissionGranted();
                },
                (error) => {
                    this.handleGeolocationError(error);
                },
                {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 60000
                }
            );
        } catch (error) {
            console.error('Error al solicitar permisos de geolocalización:', error);
            this.showPermissionStatus('error', 
                'Error al solicitar permisos de ubicación.\n' +
                'Intenta recargar la página.');
        }
    }
    
    handlePermissionGranted() {
        this.permissionGranted = true;
        
        // Actualizar cache con estado otorgado
        this.updatePermissionCache('granted');
        
        // Solo mostrar mensaje de éxito si hay overlay visible
        if (this.overlayElement && this.overlayElement.style.display !== 'none') {
            this.showPermissionStatus('success', '¡Permisos de ubicación otorgados! Cargando aplicación...');
            
            // Ocultar overlay después de un breve delay
            setTimeout(() => {
                this.hideOverlay();
            }, 1500);
        } else {
            console.log('Permisos otorgados silenciosamente');
        }
        
        // Iniciar seguimiento de ubicación
        this.startLocationTracking();
        
        // Limpiar verificación en segundo plano
        this.stopBackgroundPermissionMonitoring();
        
        // Disparar evento personalizado
        window.dispatchEvent(new CustomEvent('geolocationPermissionGranted', {
            detail: { position: this.currentPosition }
        }));
    }
    
    handlePermissionDenied() {
        this.updatePermissionCache('denied');
        this.showPermissionStatus('error', 
            'Permisos de ubicación denegados. Para habilitar:\n' +
            '1. Haz clic en el ícono de candado en la barra de direcciones\n' +
            '2. Selecciona "Permitir" para ubicación\n' +
            '3. Recarga la página');
        this.showRefreshButton();
    }
    
    handlePermissionPrompt() {
        this.showPermissionStatus('warning', 
            'Esta aplicación necesita acceso a tu ubicación para funcionar correctamente.\n' +
            'Haz clic en "Permitir Ubicación" para continuar.');
    }
    
    handleUnknownPermissionState() {
        this.showPermissionStatus('warning', 
            'No se pudo determinar el estado de los permisos de ubicación.\n' +
            'Haz clic en "Permitir Ubicación" para intentar obtener acceso.');
    }
    
    handleGeolocationError(error) {
        let message = '';
        let actionRequired = false;
        
        switch (error.code) {
            case error.PERMISSION_DENIED:
                this.handlePermissionDenied();
                return; // Ya manejado por handlePermissionDenied
            case error.POSITION_UNAVAILABLE:
                message = 'La información de ubicación no está disponible.\n' +
                         'Verifica que el GPS esté habilitado en tu dispositivo.';
                break;
            case error.TIMEOUT:
                message = 'La solicitud de ubicación ha expirado.\n' +
                         'Esto puede deberse a una señal GPS débil. Intenta nuevamente.';
                actionRequired = true;
                break;
            default:
                message = 'Error desconocido al obtener la ubicación.\n' +
                         'Intenta recargar la página.';
                actionRequired = true;
                break;
        }
        
        this.showPermissionStatus('error', message);
        
        if (actionRequired) {
            this.showRetryButton();
        }
    }

    handleLocationTrackingError(error) {
        console.error('Error específico en seguimiento de ubicación:', {
            code: error.code,
            message: error.message,
            timestamp: new Date().toISOString()
        });

        // Incrementar contador de errores consecutivos
        this.consecutiveErrors = (this.consecutiveErrors || 0) + 1;
        
        let message = '';
        let shouldStopTracking = false;
        let shouldRetry = false;
        let retryDelay = 3000;
        let useHighAccuracy = this.useHighAccuracy !== false; // Default true

        switch (error.code) {
            case error.PERMISSION_DENIED:
                message = 'Permisos de ubicación revocados durante el seguimiento.';
                this.permissionGranted = false;
                this.updatePermissionCache('denied');
                shouldStopTracking = true;
                this.consecutiveErrors = 0;
                this.handlePermissionDenied();
                return;
            
            case error.POSITION_UNAVAILABLE:
                message = 'Servicio de ubicación no disponible. Implementando fallback...';
                shouldRetry = true;
                retryDelay = Math.min(5000 + (this.consecutiveErrors * 2000), 15000);
                // Degradar precisión después de 2 errores consecutivos
                if (this.consecutiveErrors >= 2) {
                    useHighAccuracy = false;
                    message += ' (modo de baja precisión)';
                }
                break;
            
            case error.TIMEOUT:
                message = 'Timeout en seguimiento de ubicación. Optimizando configuración...';
                shouldRetry = true;
                retryDelay = Math.min(3000 + (this.consecutiveErrors * 1000), 10000);
                // Degradar precisión después de 3 timeouts consecutivos
                if (this.consecutiveErrors >= 3) {
                    useHighAccuracy = false;
                    message += ' (modo de baja precisión)';
                }
                break;
            
            default:
                message = 'Error en seguimiento de ubicación. Reintentando...';
                shouldRetry = true;
                retryDelay = Math.min(5000 + (this.consecutiveErrors * 1000), 12000);
                break;
        }

        // Mostrar notificación discreta para errores de seguimiento
        console.warn(`Seguimiento de ubicación (${this.consecutiveErrors} errores consecutivos):`, message);
        
        // Mostrar indicador visual al usuario después de varios errores
        if (this.consecutiveErrors >= 3) {
            this.showLocationStatus('warning', `Problemas de conectividad detectados. Intentando recuperar ubicación...`);
        }

        if (shouldStopTracking && this.watchId) {
            navigator.geolocation.clearWatch(this.watchId);
            this.watchId = null;
            this.consecutiveErrors = 0;
        }

        if (shouldRetry && this.consecutiveErrors < 10) { // Límite de reintentos
            // Reintentar con configuración optimizada
            setTimeout(() => {
                if (this.permissionGranted && !this.watchId) {
                    console.log(`Reintentando seguimiento de ubicación... (intento ${this.consecutiveErrors + 1}, alta precisión: ${useHighAccuracy})`);
                    this.startLocationTrackingWithConfig(useHighAccuracy);
                }
            }, retryDelay);
        } else if (this.consecutiveErrors >= 10) {
            console.error('Demasiados errores consecutivos. Deteniendo seguimiento automático.');
            this.showLocationStatus('error', 'No se puede obtener ubicación. Verifica tu conexión y permisos.');
            this.stopLocationTracking();
        }
     }

     stopLocationTracking() {
         if (this.watchId) {
             navigator.geolocation.clearWatch(this.watchId);
             this.watchId = null;
             this.consecutiveErrors = 0;
             console.log('Seguimiento de ubicación detenido');
             this.showLocationStatus('info', 'Seguimiento de ubicación detenido');
         }
     }
     
     startLocationTracking() {
        this.startLocationTrackingWithConfig(true); // Iniciar con alta precisión por defecto
     }
     
     startLocationTrackingWithConfig(enableHighAccuracy = true) {
        // Validar que geolocation esté disponible
        if (!navigator.geolocation) {
            console.error('Geolocation no está soportado por este navegador');
            this.showPermissionStatus('error', 'Tu navegador no soporta geolocalización.');
            return;
        }

        // Validar que los permisos estén otorgados
        if (!this.permissionGranted) {
            console.warn('Intentando iniciar seguimiento sin permisos otorgados');
            return;
        }

        // Configuración optimizada basada en errores previos
        const config = {
            enableHighAccuracy: enableHighAccuracy,
            timeout: enableHighAccuracy ? 20000 : 15000, // Timeout más largo
            maximumAge: enableHighAccuracy ? 60000 : 120000 // Cache más largo para baja precisión
        };
        
        // Guardar configuración actual
        this.useHighAccuracy = enableHighAccuracy;

        try {
            this.watchId = navigator.geolocation.watchPosition(
                (position) => {
                    // Reset contador de errores en éxito
                    this.consecutiveErrors = 0;
                    this.currentPosition = position;
                    
                    const accuracy = position.coords.accuracy;
                    console.log(`Ubicación actualizada: ${position.coords.latitude}, ${position.coords.longitude} (precisión: ${accuracy}m, alta precisión: ${enableHighAccuracy})`);
                    
                    // Mostrar estado de ubicación exitoso
                    this.showLocationStatus('success', `Ubicación actualizada (precisión: ${Math.round(accuracy)}m)`);
                    
                    // Disparar evento de actualización de posición
                    window.dispatchEvent(new CustomEvent('locationUpdated', {
                        detail: { 
                            position: position,
                            accuracy: accuracy,
                            highAccuracy: enableHighAccuracy
                        }
                    }));
                },
                (error) => {
                    console.error('Error en seguimiento de ubicación:', error);
                    this.handleLocationTrackingError(error);
                },
                config
            );
            
            console.log(`Seguimiento de ubicación iniciado con ID: ${this.watchId} (alta precisión: ${enableHighAccuracy}, timeout: ${config.timeout}ms)`);
            this.showLocationStatus('info', `Iniciando seguimiento de ubicación... (${enableHighAccuracy ? 'alta' : 'baja'} precisión)`);
            
        } catch (error) {
            console.error('Error al iniciar seguimiento de ubicación:', error);
            this.showPermissionStatus('error', 'Error al iniciar el seguimiento de ubicación.');
        }
    }
    
    showPermissionStatus(type, message) {
        const statusElement = document.getElementById('permission-status');
        if (statusElement) {
            statusElement.className = `permission-status ${type}`;
            statusElement.textContent = message;
            
            // Auto-hide success messages
            if (type === 'success') {
                setTimeout(() => {
                    this.hideOverlay();
                }, 2000);
            }
            
            // Para errores críticos, agregar botón de reintento
            if (type === 'error' && !statusElement.querySelector('.retry-button')) {
                const retryButton = document.createElement('button');
                retryButton.textContent = 'Reintentar';
                retryButton.className = 'retry-button';
                retryButton.style.cssText = `
                    margin-top: 10px;
                    padding: 8px 16px;
                    background-color: #007bff;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 14px;
                `;
                retryButton.onclick = () => {
                    this.restartPermissionChecking();
                };
                statusElement.appendChild(retryButton);
            }
        }
    }
    
    showLocationStatus(type, message) {
        // Crear o actualizar indicador de estado de ubicación
        let locationStatusElement = document.getElementById('location-status');
        
        if (!locationStatusElement) {
            locationStatusElement = document.createElement('div');
            locationStatusElement.id = 'location-status';
            locationStatusElement.style.cssText = `
                position: fixed;
                top: 10px;
                right: 10px;
                padding: 8px 12px;
                border-radius: 4px;
                font-size: 12px;
                z-index: 1001;
                max-width: 300px;
                word-wrap: break-word;
                transition: opacity 0.3s ease;
            `;
            document.body.appendChild(locationStatusElement);
        }
        
        // Configurar estilos según el tipo
        const styles = {
            success: 'background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb;',
            error: 'background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb;',
            warning: 'background-color: #fff3cd; color: #856404; border: 1px solid #ffeaa7;',
            info: 'background-color: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb;'
        };
        
        locationStatusElement.style.cssText += styles[type] || styles.info;
        locationStatusElement.textContent = message;
        locationStatusElement.style.opacity = '1';
        
        // Auto-hide después de un tiempo
        clearTimeout(this.locationStatusTimeout);
        this.locationStatusTimeout = setTimeout(() => {
            if (locationStatusElement) {
                locationStatusElement.style.opacity = '0';
                setTimeout(() => {
                    if (locationStatusElement && locationStatusElement.parentNode) {
                        locationStatusElement.parentNode.removeChild(locationStatusElement);
                    }
                }, 300);
            }
        }, type === 'success' ? 3000 : type === 'error' ? 8000 : 5000);
    }
    
    showRefreshButton() {
        const requestBtn = document.getElementById('request-permission-btn');
        const refreshBtn = document.getElementById('refresh-permission-btn');
        
        if (requestBtn) requestBtn.style.display = 'none';
        if (refreshBtn) refreshBtn.style.display = 'inline-block';
    }
    
    showRetryButton() {
        const statusElement = document.getElementById('permission-status');
        if (statusElement && !statusElement.querySelector('.retry-button')) {
            const retryButton = document.createElement('button');
            retryButton.textContent = 'Reintentar';
            retryButton.className = 'retry-button btn btn-primary';
            retryButton.style.cssText = `
                margin-top: 10px;
                padding: 8px 16px;
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
            `;
            retryButton.onclick = () => {
                this.requestGeolocationPermission();
            };
            statusElement.appendChild(retryButton);
        }
    }
    
    hideOverlay() {
        if (this.overlayElement) {
            this.overlayElement.style.display = 'none';
        }
    }
    
    showOverlay() {
        if (this.overlayElement) {
            this.overlayElement.style.display = 'flex';
            console.log('Overlay mostrado');
        }
    }
    
    shouldShowOverlay(permissionState) {
        // Solo mostrar overlay si:
        // 1. Los permisos están denegados
        // 2. Los permisos nunca han sido solicitados (prompt)
        // 3. El estado es desconocido y no tenemos cache válido
        return permissionState === 'denied' || 
               permissionState === 'prompt' || 
               (permissionState === 'unknown' && !this.isCacheValid());
    }
    
    getCurrentPosition() {
        return this.currentPosition;
    }
    
    isPermissionGranted() {
        return this.permissionGranted;
    }
    
    startBackgroundPermissionMonitoring() {
        // Verificación silenciosa cada 30 segundos
        this.permissionCheckInterval = setInterval(async () => {
            if (!this.permissionGranted) {
                await this.silentPermissionCheck();
            }
        }, 30000);
        
        console.log('Monitoreo silencioso de permisos iniciado');
    }
    
    stopBackgroundPermissionMonitoring() {
        if (this.permissionCheckInterval) {
            clearInterval(this.permissionCheckInterval);
            this.permissionCheckInterval = null;
            console.log('Monitoreo silencioso de permisos detenido');
        }
    }
    
    async silentPermissionCheck() {
        try {
            const currentState = await this.checkPermissionStateQuietly();
            
            // Solo actuar si el estado ha cambiado a 'granted'
            if (currentState === 'granted' && !this.permissionGranted) {
                console.log('Permisos otorgados detectados en verificación silenciosa');
                this.handlePermissionGranted();
            } else if (currentState === 'denied' && this.permissionGranted) {
                // Si los permisos fueron revocados
                console.log('Permisos revocados detectados');
                this.permissionGranted = false;
                this.updatePermissionCache('denied');
                
                // Mostrar overlay solo si es necesario
                if (this.shouldShowOverlay('denied')) {
                    this.showOverlay();
                }
            }
        } catch (error) {
            console.error('Error en verificación silenciosa:', error);
        }
    }
    
    destroy() {
        if (this.watchId) {
            navigator.geolocation.clearWatch(this.watchId);
        }
        
        this.stopBackgroundPermissionMonitoring();
        
        if (this.overlayElement) {
            this.overlayElement.remove();
        }
        
        // Limpiar cache
        this.clearCacheFromStorage();
    }
}

// Instancia global del gestor de permisos
let geolocationManager = null;

// Inicializar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        geolocationManager = new GeolocationPermissionManager();
    });
} else {
    geolocationManager = new GeolocationPermissionManager();
}

// Exportar para uso global
window.GeolocationPermissionManager = GeolocationPermissionManager;
window.geolocationManager = geolocationManager;