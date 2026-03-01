# Guía de uso de la API - RelengCorp Digital

## 📄 Paginación

Todos los endpoints de listado ahora soportan paginación automática.

### Parámetros de paginación:
- `page` - Número de página (por defecto: 1)
- `page_size` - Elementos por página (por defecto: 20, máximo: 100)

### Ejemplos:
```bash
# Primera página (20 elementos)
GET /api/users

# Segunda página
GET /api/users?page=2

# 50 elementos por página
GET /api/users?page_size=50

# Página 3 con 10 elementos
GET /api/users?page=3&page_size=10
```

### Respuesta paginada:
```json
{
  "count": 145,
  "next": "http://localhost:8000/api/users?page=3",
  "previous": "http://localhost:8000/api/users?page=1",
  "results": [
    { "id": 1, "name": "..." },
    ...
  ]
}
```

---

## 🔍 Búsqueda

Busca por múltiples campos usando el parámetro `search`.

### Ejemplos:

#### Usuarios (`/api/users`)
Busca en: username, name, last_name, email, code, dui
```bash
GET /api/users?search=juan
GET /api/users?search=ingeniero
GET /api/users?search=123456789
```

#### Entidades (`/api/entities`)
Busca en: name, tag
```bash
GET /api/entities?search=motor
GET /api/entities?search=TAG-001
```

#### Reportes (`/api/reports`)
Busca en: name, observations, diagnostic, recomendations
```bash
GET /api/reports?search=vibración
GET /api/reports?search=crítico
```

#### Avisos (`/api/notices`)
Busca en: name, ot_number, comment
```bash
GET /api/notices?search=OT-2024-001
GET /api/notices?search=fuga
```

---

## 🎯 Filtros

Cada endpoint soporta filtros específicos según su modelo.

### Usuarios (`/api/users`)
```bash
# Por posición
GET /api/users?position=Ingeniero

# Combinando búsqueda y filtro
GET /api/users?position=Ingeniero&search=juan
```

### Entidades (`/api/entities`)
```bash
# Por tipo (1=Plant, 2=Area, 3=Route, 4=Equipment, 5=Item, 6=Component)
GET /api/entities?type=4

# Por padre específico
GET /api/entities?parent=5

# Entidades sin padre (nivel raíz)
GET /api/entities?parent=null

# Combinando tipo y búsqueda
GET /api/entities?type=4&search=motor
```

### Reportes (`/api/reports`)
```bash
# Por entidad
GET /api/reports?entity=10

# Por tipo de trabajo (1=PDM, 2=NDT)
GET /api/reports?work_type=1

# Por tipo de servicio (1-9)
GET /api/reports?service_type=1

# Por condición (1=Normal, 2=Tolerable, 3=Precaución, 4=Crítico)
GET /api/reports?condition=4

# Por programa (1=Programado, 2=No programado)
GET /api/reports?program=1

# Por estado de ejecución (1=Ejecutado, 2=No ejecutado)
GET /api/reports?execution_status=1

# Solo reportes activos
GET /api/reports?is_active=true

# Combinando múltiples filtros
GET /api/reports?entity=10&condition=4&is_active=true
```

### Avisos (`/api/notices`)
```bash
# Por reporte
GET /api/notices?report=5

# Por estado (1=Abierto, 2=Cerrado)
GET /api/notices?status=1

# Por estado OT (1=Abierto, 2=Cerrado)
GET /api/notices?ot_status=1

# Por estado real (1=Atendido, 2=No atendido)
GET /api/notices?status_real=1

# Combinando filtros
GET /api/notices?report=5&status=1&ot_status=1
```

### Avisos por Reporte (`/api/notices-by-report/{id}`)
```bash
# Avisos de un reporte específico
GET /api/notices-by-report/5

# Con filtros adicionales
GET /api/notices-by-report/5?status=1
GET /api/notices-by-report/5?ot_status=2
```

---

## 📊 Ordenamiento

Usa el parámetro `ordering` para ordenar resultados.

### Parámetros:
- Campo sin prefijo: orden ascendente
- Campo con `-`: orden descendente

### Campos comunes ordenables:
- `created_at` - Fecha de creación
- `updated_at` - Fecha de actualización
- `name` - Nombre
- `id` - ID

### Ejemplos:
```bash
# Por fecha de creación (más antiguos primero)
GET /api/users?ordering=created_at

# Por fecha de creación (más recientes primero) - DEFAULT
GET /api/users?ordering=-created_at

# Por nombre alfabéticamente
GET /api/entities?ordering=name

# Por nombre inverso
GET /api/entities?ordering=-name

# Reportes por condición (críticos primero)
GET /api/reports?ordering=-condition
```

---

## 🔗 Combinando todo

Puedes combinar paginación, búsqueda, filtros y ordenamiento:

```bash
# Equipos (type=4) con "motor" en el nombre, 
# ordenados alfabéticamente, página 2, 30 por página
GET /api/entities?type=4&search=motor&ordering=name&page=2&page_size=30

# Reportes críticos activos de una entidad,
# ordenados por fecha de ejecución reciente
GET /api/reports?entity=10&condition=4&is_active=true&ordering=-execution_date

# Avisos abiertos con OT cerrado, buscando "fuga",
# ordenados por fecha, 50 por página
GET /api/notices?status=1&ot_status=2&search=fuga&ordering=-date&page_size=50
```

---

## 📝 Notas importantes

1. **Eliminación lógica**: Los GET solo devuelven registros con `deleted=False`
2. **Paginación por defecto**: Si no se especifica, se usa página 1 con 20 elementos
3. **Ordenamiento por defecto**: `-created_at` (más recientes primero)
4. **Búsqueda case-insensitive**: No distingue mayúsculas/minúsculas
5. **Filtros booleanos**: Acepta `true`, `1`, `yes` para verdadero, cualquier otro valor es falso

---

## 🧪 Ejemplos de uso completo

### Frontend - JavaScript/Fetch
```javascript
// Obtener usuarios con búsqueda y paginación
const getUsers = async (page = 1, search = '') => {
  const url = `/api/users?page=${page}&search=${search}`;
  const response = await fetch(url);
  const data = await response.json();
  return data;
};

// Obtener equipos de una planta
const getEquipments = async (plantId) => {
  const url = `/api/entities?type=4&parent=${plantId}&ordering=name`;
  const response = await fetch(url);
  const data = await response.json();
  return data.results;
};

// Obtener reportes críticos
const getCriticalReports = async () => {
  const url = `/api/reports?condition=4&is_active=true&ordering=-execution_date`;
  const response = await fetch(url);
  const data = await response.json();
  return data.results;
};
```

### cURL
```bash
# Listar usuarios
curl "http://localhost:8000/api/users?page=1&page_size=10"

# Buscar entidades
curl "http://localhost:8000/api/entities?search=motor&type=4"

# Reportes críticos
curl "http://localhost:8000/api/reports?condition=4"
```
