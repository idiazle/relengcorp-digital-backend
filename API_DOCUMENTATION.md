# Documentación API - RelengCorp Digital

## 📚 Acceso a la Documentación

Después de instalar las dependencias y ejecutar el servidor, puedes acceder a la documentación interactiva de la API en las siguientes URLs:

### 🔵 Swagger UI (Recomendado)
```
http://localhost:8000/api/docs/
```
**Características:**
- Interfaz interactiva para probar endpoints
- Puedes enviar peticiones directamente desde el navegador
- Visualización clara de parámetros, respuestas y modelos
- Persistencia de autenticación entre peticiones

### 🟢 ReDoc
```
http://localhost:8000/api/redoc/
```
**Características:**
- Documentación limpia y profesional
- Mejor para lectura y referencia
- Navegación por secciones y búsqueda
- Ideal para compartir con equipos externos

### 📄 Schema OpenAPI (JSON)
```
http://localhost:8000/api/schema/
```
**Características:**
- Especificación OpenAPI 3.0 en formato JSON
- Útil para herramientas de generación de código
- Compatible con Postman, Insomnia, etc.

---

## 🚀 Instalación y Configuración

### 1. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 2. Ejecutar Migraciones (si es necesario)
```bash
python manage.py migrate
```

### 3. Iniciar el Servidor
```bash
python manage.py runserver
```

### 4. Acceder a la Documentación
Abre tu navegador y ve a: `http://localhost:8000/api/docs/`

---

## 📖 Cómo Usar Swagger UI

### Probar un Endpoint

1. **Navega al endpoint** que deseas probar
2. Haz clic en el endpoint para expandirlo
3. Haz clic en **"Try it out"**
4. Completa los parámetros requeridos
5. Haz clic en **"Execute"**
6. Revisa la respuesta debajo

### Ejemplo: Listar Usuarios

```http
GET /api/users/
```

**Parámetros de consulta opcionales:**
- `page`: Número de página (default: 1)
- `page_size`: Elementos por página (max: 100, default: 20)
- `search`: Buscar por nombre de usuario, email, nombre o apellido
- `ordering`: Ordenar por campo (ej: `username`, `-username`)

**Respuesta exitosa (200):**
```json
{
  "count": 50,
  "next": "http://localhost:8000/api/users/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "username": "jperez",
      "email": "jperez@example.com",
      "name": "Juan",
      "last_name": "Pérez",
      "groups": [1, 2],
      "deleted": false
    }
  ]
}
```

### Ejemplo: Crear Usuario con Grupos

```http
POST /api/users/
Content-Type: application/json

{
  "username": "usuario1",
  "email": "usuario1@example.com",
  "password": "password123",
  "code": "USR002",
  "name": "María",
  "last_name": "López",
  "dui": "98765432-1",
  "short_name": "MLópez",
  "position": "Técnico Senior",
  "groups": [2, 3]
}
```

**Respuesta exitosa (201):**
```json
{
  "id": 2,
  "username": "usuario1",
  "email": "usuario1@example.com",
  "code": "USR002",
  "name": "María",
  "last_name": "López",
  "groups": [2, 3],
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Ejemplo: Listar Grupos Disponibles

```http
GET /api/groups/
```

**Respuesta exitosa (200):**
```json
[
  {
    "id": 1,
    "name": "Superusuario"
  },
  {
    "id": 2,
    "name": "Editor PDM"
  },
  {
    "id": 3,
    "name": "Editor NTD"
  },
  {
    "id": 4,
    "name": "Usuario Final"
  }
]
```

**Nota:** Los grupos deben crearse previamente en el sistema (vía Django Admin o comando de inicialización).

---

## 🏷️ Tags y Organización

La API está organizada en las siguientes secciones:

### 👥 Users
Gestión de usuarios del sistema
- `GET /api/users/` - Listar usuarios
- `POST /api/users/` - Crear usuario
- `GET /api/users/{id}/` - Obtener usuario
- `PUT /api/users/{id}/` - Actualizar usuario
- `DELETE /api/users/{id}/` - Eliminar usuario (soft delete)
- `GET /api/groups/` - Listar grupos disponibles (roles)

### 🏢 Entities
Gestión de entidades jerárquicas (plantas, áreas, rutas, equipos, items, componentes)
- `GET /api/entities/` - Listar entidades
- `POST /api/entities/` - Crear entidad
- `GET /api/entities/{id}/` - Obtener entidad
- `PUT /api/entities/{id}/` - Actualizar entidad
- `DELETE /api/entities/{id}/` - Eliminar entidad (soft delete)

**Tipos de entidades:**
- `1`: Planta
- `2`: Área
- `3`: Ruta
- `4`: Equipo
- `5`: Item
- `6`: Componente

### 📊 Reports
Gestión de reportes de mantenimiento
- `GET /api/reports/` - Listar reportes
- `POST /api/reports/` - Crear reporte
- `GET /api/reports/{id}/` - Obtener reporte
- `PUT /api/reports/{id}/` - Actualizar reporte
- `DELETE /api/reports/{id}/` - Eliminar reporte (soft delete)

**Campos importantes:**
- `entity`: ID de la entidad (equipo) asociada
- `execution_date`: Fecha de ejecución del mantenimiento
- `is_active`: Solo un reporte activo por equipo
- `service_type`: Tipo de servicio realizado
- `work_type`: Tipo de trabajo (predictivo, correctivo, etc.)

### 📝 Notices
Gestión de avisos y órdenes de trabajo
- `GET /api/notices/` - Listar avisos
- `POST /api/notices/` - Crear aviso
- `GET /api/notices/{id}/` - Obtener aviso
- `PUT /api/notices/{id}/` - Actualizar aviso
- `DELETE /api/notices/{id}/` - Eliminar aviso (soft delete)

**Campos de OT:**
- `ot_number`: Número de orden de trabajo
- `ot_date`: Fecha de la orden
- `comment`: Comentarios adicionales
- `images`: Múltiples imágenes asociadas

### 📈 Analytics
Endpoints de análisis y estadísticas
- `GET /api/equipment-condition-summary/` - Resumen de condiciones de equipos
- `GET /api/equipment-condition-by-month/` - Condición de equipos por mes

---

## 🔍 Filtros y Búsqueda

### Paginación
Todos los endpoints de listado soportan paginación:
```
GET /api/users/?page=2&page_size=50
```

### Búsqueda
Búsqueda de texto en múltiples campos:
```
GET /api/users/?search=admin
GET /api/entities/?search=turbina
GET /api/reports/?search=predictivo
```

### Filtros
Filtrar por campos específicos:
```
# Usuarios activos
GET /api/users/?is_active=true

# Entidades de tipo equipo (4) no eliminadas
GET /api/entities/?type=4&deleted=false

# Reportes por entidad específica
GET /api/reports/?entity=15

# Avisos con OT
GET /api/notices/?ot_number=OT-2024-001
```

### Ordenamiento
Ordenar resultados por campo (agregar `-` para descendente):
```
# Ordenar usuarios por username ascendente
GET /api/users/?ordering=username

# Ordenar reportes por fecha descendente
GET /api/reports/?ordering=-execution_date

# Ordenar entidades por nombre
GET /api/entities/?ordering=name
```

### Combinación de Parámetros
Puedes combinar múltiples parámetros:
```
GET /api/entities/?type=4&deleted=false&search=bomba&ordering=name&page_size=50
```

---

## 🗑️ Eliminación Lógica (Soft Delete)

Todos los modelos principales implementan soft delete:

### Comportamiento
- **DELETE** marca el registro como eliminado (`deleted=true`)
- Automáticamente se establece `deleted_at` con la fecha/hora
- **El archivo físico NO se elimina** si existe
- **GET** solo muestra registros con `deleted=false` por defecto

### Recuperar Registros Eliminados
Para ver todos los registros incluyendo eliminados, usa el filtro:
```
GET /api/entities/?deleted=true
```

---

## 📦 Modelos de Datos

### User
```json
{
  "id": 1,
  "code": "USR001",
  "name": "Juan",
  "last_name": "Pérez",
  "username": "jperez",
  "dui": "12345678-9",
  "short_name": "JPérez",
  "position": "Técnico",
  "email": "jperez@example.com",
  "phone": "7777-7777",
  "extra_emails": "jperez2@example.com",
  "groups": [1, 2],
  "deleted": false,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "deleted_at": null
}
```

**Nota sobre grupos:** Los usuarios pueden pertenecer a múltiples grupos (roles) que definen sus permisos. Los valores posibles dependen de los grupos creados en el sistema.

### Group (Rol)
```json
{
  "id": 1,
  "name": "Editor PDM"
}
```

### Entity (Jerárquica)
```json
{
  "id": 15,
  "name": "Turbina Principal",
  "type": 4,
  "extra_info": {"potencia": "500kW"},
  "parent": 3,
  "tag": "TRB-001",
  "deleted": false,
  "deleted_at": null
}
```

### Report
```json
{
  "id": 100,
  "name": "Inspección Mensual",
  "entity": 15,
  "entity_detail": {
    "id": 15,
    "name": "Turbina Principal",
    "hierarchy": "Planta Norte > Área Generación > Ruta A > Turbina Principal"
  },
  "execution_date": "2024-01-15",
  "is_active": true,
  "service_type": "Mantenimiento Predictivo",
  "work_type": "Análisis de Vibraciones",
  "diagnostic": "Equipo en condición normal",
  "observations": "Sin novedades",
  "recommendations": "Continuar monitoreo",
  "attachment": "/media/reports/1/reporte.pdf",
  "deleted": false,
  "deleted_at": null
}
```

### Notice (con OT)
```json
{
  "id": 50,
  "entity": 15,
  "condition": "Alerta",
  "ot_number": "OT-2024-001",
  "ot_date": "2024-01-15",
  "comment": "Requiere revisión de rodamientos",
  "images": [
    {
      "id": 1,
      "image": "/media/notices/rodamiento.jpg"
    }
  ],
  "deleted": false,
  "deleted_at": null
}
```

---

## 🔐 Autenticación (Futuro)

Actualmente la API está configurada con `AllowAny`, lo que significa que no requiere autenticación.

**Cuando se implemente autenticación:**
1. Obtener token de acceso
2. Incluir en headers: `Authorization: Bearer <token>`
3. Swagger UI guardará automáticamente la autenticación

---

## 🛠️ Herramientas Compatibles

### Importar Schema en Postman
1. Descarga el schema: `http://localhost:8000/api/schema/`
2. En Postman: Import > Link > Pegar URL
3. Postman generará automáticamente todas las peticiones

### Importar Schema en Insomnia
1. File > Import Data
2. From URL: `http://localhost:8000/api/schema/`
3. Insomnia creará las peticiones automáticamente

### Generar Cliente (TypeScript, Python, etc.)
Usa OpenAPI Generator con el schema:
```bash
# Descargar schema
curl http://localhost:8000/api/schema/ > openapi.json

# Generar cliente TypeScript
openapi-generator generate -i openapi.json -g typescript-axios -o ./api-client

# Generar cliente Python
openapi-generator generate -i openapi.json -g python -o ./api-client
```

---

## 📞 Soporte

Para dudas o problemas con la API:
- **Email:** soporte@relengcorp.com
- **Documentación interactiva:** http://localhost:8000/api/docs/

---

## 📝 Notas Adicionales

### Archivos de Configuración
- **settings.py:** Configuración de `REST_FRAMEWORK` y `SPECTACULAR_SETTINGS`
- **urls.py:** Rutas de documentación API
- **requirements.txt:** Incluye `drf-spectacular==0.27.0`

### Personalización
Para personalizar la documentación, modifica `SPECTACULAR_SETTINGS` en `settings.py`:
- Cambiar título, descripción, versión
- Agregar más tags personalizados
- Configurar componentes de seguridad
- Personalizar Swagger UI

### Producción
En producción, considera:
- Habilitar solo para usuarios autenticados
- Usar HTTPS para todas las peticiones
- Documentar políticas de rate limiting
- Agregar ejemplos de respuestas de error
