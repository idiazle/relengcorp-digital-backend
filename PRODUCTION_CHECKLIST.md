# 🔒 Checklist de Producción - RelengCorp Digital

Este documento contiene las configuraciones y mejoras necesarias antes de desplegar a producción.

---

## ⚠️ CRÍTICO - Seguridad

### 1. Variables de Entorno

Actualmente las credenciales están hardcodeadas. **Instalar y configurar:**

```bash
pip install python-decouple
```

**Crear archivo `.env` en la raíz del proyecto:**

```env
# Django
SECRET_KEY=tu-secret-key-super-segura-aqui
DEBUG=False
ALLOWED_HOSTS=tudominio.com,www.tudominio.com

# Base de datos
DB_ENGINE=mssql
DB_NAME=dp_reldigital
DB_USER=tu_usuario_db
DB_PASSWORD=tu_password_seguro
DB_HOST=tu_servidor_db
DB_PORT=1433

# CORS (solo orígenes específicos)
CORS_ALLOWED_ORIGINS=https://tudominio.com,https://app.tudominio.com
```

**Modificar `settings.py`:**

```python
from decouple import config, Csv

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())

DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE', default='mssql'),
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT', default='1433'),
        'OPTIONS': {
            'driver': 'ODBC Driver 17 for SQL Server'
        }
    }
}
```

**Agregar `.env` al `.gitignore`:**

```gitignore
.env
.env.local
.env.production
```

---

### 2. REST Framework - Autenticación

**Recomendación: Implementar JWT (JSON Web Tokens)**

```bash
pip install djangorestframework-simplejwt
```

**En `settings.py`:**

```python
INSTALLED_APPS = [
    # ...
    'rest_framework_simplejwt',
]

REST_FRAMEWORK = {
    # ... configuración existente ...
    
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',  # Cambiar de AllowAny
    ],
}

# Configuración JWT
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}
```

**En `urls.py`:**

```python
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    # ...
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
```

---

### 3. Grupos y Permisos Iniciales

**Crear grupos de usuarios (roles) en el sistema:**

Los usuarios se organizan mediante grupos que definen sus permisos. Es necesario crear los grupos antes de asignarlos a usuarios.

**Opción 1: Crear desde Django Admin**

1. Acceder al admin: `http://localhost:8000/api/admin/`
2. Ir a **Auth > Grupos**
3. Crear los siguientes grupos:
   - Superusuario
   - Editor PDM
   - Editor NTD
   - Usuario Final

**Opción 2: Usar el shell de Django**

```bash
python manage.py shell
```

```python
from django.contrib.auth.models import Group,Permission

# Crear grupos
superuser_group = Group.objects.create(name='Superusuario')
editor_pdm_group = Group.objects.create(name='Editor PDM')
editor_ntd_group = Group.objects.create(name='Editor NTD')
user_group = Group.objects.create(name='Usuario Final')

# Asignar permisos según sea necesario
# Ejemplo para Editor PDM (permisos completos sobre reports y entities)
pdm_permissions = Permission.objects.filter(
    content_type__app_label='reldigital',
    codename__in=['add_report', 'change_report', 'view_report', 'add_entity', 'change_entity', 'view_entity']
)
editor_pdm_group.permissions.set(pdm_permissions)
```

**Opción 3: Crear comando de inicialización (Recomendado)**

Crear archivo `reldigital/management/commands/init_groups.py` con un comando para automatizar:

```python
python manage.py init_groups
```

**Nota:** El endpoint `GET /api/groups/` permite listar los grupos disponibles.

---

### 4. HTTPS y Seguridad

**En `settings.py` para producción:**

```python
# Solo en producción
if not DEBUG:
    # HTTPS
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    
    # HSTS (HTTP Strict Transport Security)
    SECURE_HSTS_SECONDS = 31536000  # 1 año
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # Otras configuraciones de seguridad
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'
    
    # CORS estricto
    CORS_ALLOW_ALL_ORIGINS = False
    CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', cast=Csv())
```

---

## 📊 Optimizaciones de Base de Datos

### 1. Índices adicionales recomendados

Agregar a `models.py`:

```python
class Entity(models.Model):
    # ...
    class Meta:
        db_table = f'{project_name}entities'
        indexes = [
            models.Index(fields=['type', 'deleted']),
            models.Index(fields=['parent', 'deleted']),
            models.Index(fields=['tag']),
        ]

class Report(models.Model):
    # ...
    class Meta:
        db_table = f'{project_name}reports'
        indexes = [
            models.Index(fields=['entity', 'is_active', 'deleted']),
            models.Index(fields=['condition', 'deleted']),
            models.Index(fields=['execution_date']),
        ]

class Notice(models.Model):
    # ...
    class Meta:
        db_table = f'{project_name}notices'
        indexes = [
            models.Index(fields=['report', 'deleted']),
            models.Index(fields=['status', 'deleted']),
            models.Index(fields=['date']),
        ]
```

### 2. Optimizaciones de queries

En `views.py`, usar `select_related` y `prefetch_related`:

```python
# Ejemplo para ReportAPIView
reports = Report.objects.filter(deleted=False).select_related(
    'entity',
    'created_by'
).prefetch_related(
    'notices'
)

# Ejemplo para EntityAPIView
entities = Entity.objects.filter(deleted=False).select_related(
    'parent',
    'created_by'
).prefetch_related(
    'children'
)
```

---

## 🚀 Configuración de Servidor

### 1. Gunicorn (servidor WSGI)

```bash
pip install gunicorn
```

**Comando de inicio:**

```bash
gunicorn coredigital.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

### 2. Nginx (proxy inverso)

**Configuración `/etc/nginx/sites-available/relengcorp`:**

```nginx
server {
    listen 80;
    server_name tudominio.com;

    location /static/ {
        alias /ruta/a/tu/proyecto/static/;
    }

    location /media/ {
        alias /ruta/a/tu/proyecto/media/;
    }

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 📝 Logging en Producción

**En `settings.py`:**

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'maxBytes': 1024 * 1024 * 15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

---

## 🔄 Backups Automáticos

### Script de backup de base de datos

**`backup_db.sh`:**

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/ruta/a/backups"
DB_NAME="dp_reldigital"

sqlcmd -S localhost -U sa -P 'Admin_123' \
    -Q "BACKUP DATABASE [$DB_NAME] TO DISK='$BACKUP_DIR/backup_$DATE.bak'"

# Mantener solo últimos 7 días
find $BACKUP_DIR -name "backup_*.bak" -mtime +7 -delete
```

**Crontab (ejecutar diariamente a las 2 AM):**

```cron
0 2 * * * /ruta/a/backup_db.sh
```

---

## 📦 Archivos estáticos

**Comando antes de desplegar:**

```bash
python manage.py collectstatic --noinput
```

**Configurar en `settings.py`:**

```python
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
```

---

## 🧪 Testing antes de producción

```bash
# Ejecutar tests
python manage.py test

# Verificar configuración de seguridad
python manage.py check --deploy

# Verificar migraciones pendientes
python manage.py showmigrations

# Crear superusuario
python manage.py createsuperuser
```

---

## ✅ Checklist Final

- [ ] Variables de entorno configuradas (`.env`)
- [ ] `DEBUG = False` en producción
- [ ] `SECRET_KEY` única y segura
- [ ] `ALLOWED_HOSTS` configurado correctamente
- [ ] HTTPS habilitado (SSL/TLS)
- [ ] Autenticación JWT implementada
- [ ] CORS configurado (no `ALLOW_ALL_ORIGINS`)
- [ ] Índices de base de datos optimizados
- [ ] Gunicorn/uWSGI configurado
- [ ] Nginx configurado como proxy
- [ ] Logging en producción activado
- [ ] Backups automáticos configurados
- [ ] Archivos estáticos recolectados
- [ ] Tests ejecutados y pasando
- [ ] Firewall configurado (solo puertos necesarios)
- [ ] Monitoreo configurado (opcional: Sentry)
- [ ] Documentación actualizada

---

## 🆘 Seguridad Adicional Recomendada

### Rate Limiting

```bash
pip install django-ratelimit
```

### Monitoreo de Errores (Sentry)

```bash
pip install sentry-sdk
```

**En `settings.py`:**

```python
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn="tu-dsn-de-sentry",
    integrations=[DjangoIntegration()],
    traces_sample_rate=1.0,
    send_default_pii=True
)
```

---

**Fecha de este documento:** Febrero 2026
**Revisar y actualizar periódicamente**
