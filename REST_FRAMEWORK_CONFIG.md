# 🎯 REST Framework - Configuración Implementada

Este documento explica la configuración de Django REST Framework implementada en el proyecto.

---

## 📋 Configuración Actual

### 1. **Paginación**

```python
'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
'PAGE_SIZE': 20,
```

**¿Qué hace?**
- Pagina automáticamente todos los endpoints que devuelven listas
- Por defecto devuelve 20 elementos por página
- El cliente puede ajustar con `?page_size=50` (máximo 100)

**Beneficios:**
- ✅ Mejora el rendimiento (no carga todos los datos)
- ✅ Reduce uso de memoria y ancho de banda
- ✅ Mejor experiencia de usuario

---

### 2. **Filtros y Búsqueda**

```python
'DEFAULT_FILTER_BACKENDS': [
    'rest_framework.filters.SearchFilter',
    'rest_framework.filters.OrderingFilter',
]
```

**¿Qué hace?**
- `SearchFilter`: Permite búsquedas con `?search=texto`
- `OrderingFilter`: Permite ordenar con `?ordering=campo`

**Beneficios:**
- ✅ Búsquedas rápidas sin código adicional
- ✅ Ordenamiento flexible
- ✅ Ya implementado en todas las vistas

---

### 3. **Renderizado**

```python
'DEFAULT_RENDERER_CLASSES': [
    'rest_framework.renderers.JSONRenderer',
    'rest_framework.renderers.BrowsableAPIRenderer',
]
```

**¿Qué hace?**
- `JSONRenderer`: Devuelve respuestas en formato JSON
- `BrowsableAPIRenderer`: Interfaz web para probar la API en el navegador

**Cómo usarlo:**
- Visita `http://localhost:8000/api/users` en el navegador
- Verás una interfaz HTML bonita para probar la API
- Útil para desarrollo y pruebas

---

### 4. **Parsers**

```python
'DEFAULT_PARSER_CLASSES': [
    'rest_framework.parsers.JSONParser',
    'rest_framework.parsers.FormParser',
    'rest_framework.parsers.MultiPartParser',
]
```

**¿Qué hace?**
- Acepta datos en formato JSON
- Acepta formularios HTML
- Acepta archivos (para uploads de imágenes/PDFs)

**Beneficios:**
- ✅ Soporta múltiples tipos de contenido
- ✅ Upload de archivos funciona automáticamente

---

### 5. **Autenticación (Actual)**

```python
'DEFAULT_AUTHENTICATION_CLASSES': [
    'rest_framework.authentication.SessionAuthentication',
],
'DEFAULT_PERMISSION_CLASSES': [
    'rest_framework.permissions.AllowAny',
],
```

**⚠️ Estado actual:**
- API completamente abierta (sin autenticación)
- Cualquiera puede acceder a todos los endpoints
- **Recomendación:** Implementar JWT antes de producción

**Para producción (ver PRODUCTION_CHECKLIST.md):**
```python
'DEFAULT_AUTHENTICATION_CLASSES': [
    'rest_framework_simplejwt.authentication.JWTAuthentication',
],
'DEFAULT_PERMISSION_CLASSES': [
    'rest_framework.permissions.IsAuthenticated',
],
```

---

### 6. **Formato de Fechas**

```python
'DATETIME_FORMAT': '%Y-%m-%d %H:%M:%S',
'DATE_FORMAT': '%Y-%m-%d',
'TIME_FORMAT': '%H:%M:%S',
```

**Formato de salida:**
- Fechas: `2026-02-28`
- Fecha/Hora: `2026-02-28 14:30:00`

**Beneficio:**
- ✅ Formato consistente en toda la API
- ✅ Compatible con ISO 8601
- ✅ Fácil de parsear en frontend

---

### 7. **Opciones Adicionales**

```python
'UNICODE_JSON': True,           # Soporta caracteres especiales (ñ, é, ü)
'COMPACT_JSON': False,          # JSON formateado (más legible)
'COERCE_DECIMAL_TO_STRING': False,  # Números decimales como números
'PAGINATE_BY_PARAM': 'page_size',   # Parámetro para tamaño de página
'MAX_PAGINATE_BY': 100,         # Máximo 100 elementos por página
```

---

## 🌍 Internacionalización

```python
LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'America/El_Salvador'
```

**¿Qué cambió?**
- Idioma predeterminado: Español
- Zona horaria: América/El Salvador (GMT-6)
- Fechas y horas ajustadas a la zona local

**Beneficios:**
- ✅ Timestamps correctos para El Salvador
- ✅ Mensajes de error en español
- ✅ Formato de fechas regional

---

## 🔧 Cómo Personalizar

### Cambiar tamaño de página por defecto

En `settings.py`:
```python
REST_FRAMEWORK = {
    'PAGE_SIZE': 50,  # Cambiar de 20 a 50
}
```

### Agregar autenticación básica temporalmente

```python
'DEFAULT_AUTHENTICATION_CLASSES': [
    'rest_framework.authentication.BasicAuthentication',
    'rest_framework.authentication.SessionAuthentication',
],
```

### Deshabilitar Browsable API en producción

```python
'DEFAULT_RENDERER_CLASSES': [
    'rest_framework.renderers.JSONRenderer',
    # Quitar BrowsableAPIRenderer
]
```

---

## 📊 Cómo Probar

### 1. Paginación

```bash
# Primera página (20 elementos)
curl http://localhost:8000/api/users

# Página 2
curl http://localhost:8000/api/users?page=2

# 50 elementos por página
curl http://localhost:8000/api/users?page_size=50
```

### 2. Búsqueda

```bash
curl http://localhost:8000/api/users?search=juan
curl http://localhost:8000/api/entities?search=motor
```

### 3. Ordenamiento

```bash
# Más recientes primero
curl http://localhost:8000/api/reports?ordering=-created_at

# Alfabéticamente
curl http://localhost:8000/api/entities?ordering=name
```

### 4. Browsable API

Abre en tu navegador:
```
http://localhost:8000/api/users
http://localhost:8000/api/entities
http://localhost:8000/api/reports
```

---

## 🎨 Interfaz Browsable API

Al visitar los endpoints desde el navegador, verás:

- **GET**: Formulario de búsqueda y filtros
- **POST**: Formulario para crear nuevos registros
- **PUT/PATCH**: Formulario para editar
- **DELETE**: Botón para eliminar
- **Documentación**: Información de campos
- **Paginación**: Botones siguiente/anterior

**Muy útil para:**
- Desarrollo sin frontend
- Testing manual
- Demostración a clientes
- Documentación visual

---

## 🚀 Próximos Pasos Recomendados

1. **Implementar JWT** (Ver PRODUCTION_CHECKLIST.md)
2. **Throttling**: Limitar requests por IP
3. **Permisos granulares**: Por usuario/rol
4. **Versionamiento**: `/api/v1/`, `/api/v2/`
5. **Documentación automática**: Swagger/OpenAPI

---

## 📚 Recursos

- [DRF Settings](https://www.django-rest-framework.org/api-guide/settings/)
- [DRF Pagination](https://www.django-rest-framework.org/api-guide/pagination/)
- [DRF Filtering](https://www.django-rest-framework.org/api-guide/filtering/)
- [DRF Authentication](https://www.django-rest-framework.org/api-guide/authentication/)

---

**Configuración implementada:** ✅ Febrero 2026
**Listo para desarrollo:** ✅
**Listo para producción:** ⚠️ Revisar PRODUCTION_CHECKLIST.md primero
