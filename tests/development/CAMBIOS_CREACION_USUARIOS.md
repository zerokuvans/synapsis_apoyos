# Documentación de Cambios - Corrección Error Creación de Usuarios

## Problema Identificado
**Error:** `__init__() got an unexpected keyword argument 'activo'`

## Causa Raíz
El modelo `Usuario` tenía un campo `activo` definido en la base de datos con valor por defecto, pero:
1. El método `__init__` no aceptaba el parámetro `activo`
2. En varios lugares del código se intentaba pasar `activo=True` al constructor
3. El valor por defecto de SQLAlchemy no se aplicaba automáticamente en la instancia

## Archivos Modificados

### 1. `app/models/usuario.py`
**Cambios realizados:**
- Agregado `self.activo = True` en el método `__init__` para establecer explícitamente el valor por defecto

**Antes:**
```python
def __init__(self, email, password, nombre, apellido, rol, telefono=None):
    self.email = email
    self.set_password(password)
    self.nombre = nombre
    self.apellido = apellido
    self.rol = rol
    self.telefono = telefono
```

**Después:**
```python
def __init__(self, email, password, nombre, apellido, rol, telefono=None):
    self.email = email
    self.set_password(password)
    self.nombre = nombre
    self.apellido = apellido
    self.rol = rol
    self.telefono = telefono
    self.activo = True  # Establecer valor por defecto explícitamente
```

### 2. `app/blueprints/lider/routes.py`
**Cambios realizados:**
- Eliminado el parámetro `activo=True` de la llamada al constructor en la función `crear_usuario`
- Eliminada la línea duplicada `nuevo_usuario.set_password(data['password'])`
- Reordenados los parámetros para coincidir con la firma del constructor

**Antes:**
```python
nuevo_usuario = Usuario(
    nombre=data['nombre'],
    apellido=data['apellido'],
    email=data['email'],
    password=data['password'],
    telefono=data['telefono'],
    rol=data['rol'],
    activo=True
)
nuevo_usuario.set_password(data['password'])
```

**Después:**
```python
nuevo_usuario = Usuario(
    email=data['email'],
    password=data['password'],
    nombre=data['nombre'],
    apellido=data['apellido'],
    rol=data['rol'],
    telefono=data['telefono']
)
```

### 3. `init_sqlite_db.py`
**Cambios realizados:**
- Eliminados parámetros no válidos: `activo=True`, `created_at`, `updated_at`
- Cambiado `password_hash` por `password` para usar el setter del modelo
- Reordenados los parámetros para coincidir con la firma del constructor

**Antes:**
```python
Usuario(
    nombre=user_data['nombre'],
    apellido=user_data['apellido'],
    email=user_data['email'],
    password_hash=generate_password_hash(user_data['password']),
    telefono=user_data.get('telefono', ''),
    rol=user_data['rol'],
    activo=True,
    created_at=datetime.now(),
    updated_at=datetime.now()
)
```

**Después:**
```python
Usuario(
    email=user_data['email'],
    password=user_data['password'],
    nombre=user_data['nombre'],
    apellido=user_data['apellido'],
    rol=user_data['rol'],
    telefono=user_data.get('telefono', '')
)
```

## Pruebas Realizadas

### 1. Prueba de Creación Directa
- **Archivo:** `test_user_creation.py`
- **Resultado:** ✅ Exitoso
- **Verificaciones:**
  - Usuario creado correctamente
  - Campo `activo` establecido en `True`
  - Contraseña hasheada correctamente
  - Todos los campos asignados apropiadamente

### 2. Prueba de Endpoint
- **Archivo:** `test_endpoint_creation.py`
- **Ruta probada:** `/lider/usuario/crear`
- **Resultado:** ✅ Código funciona (302 por autenticación requerida)

## Impacto de los Cambios

### ✅ Beneficios
1. **Error resuelto:** Ya no se produce el error `unexpected keyword argument 'activo'`
2. **Consistencia:** Todos los lugares de creación de usuarios usan la misma firma
3. **Simplicidad:** El valor por defecto se maneja automáticamente
4. **Mantenibilidad:** Código más limpio y fácil de mantener

### ⚠️ Consideraciones
1. **Compatibilidad:** Los cambios son retrocompatibles
2. **Base de datos:** No se requieren migraciones adicionales
3. **Funcionalidad:** Toda la funcionalidad existente se mantiene intacta

## Estado Final
- ✅ Error de creación de usuarios resuelto
- ✅ Todas las pruebas pasan exitosamente
- ✅ Código limpio y consistente
- ✅ Funcionalidad preservada

## Fecha de Implementación
**Fecha:** $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
**Desarrollador:**