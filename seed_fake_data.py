import os
import django
import random
from datetime import datetime, timedelta

# Configurar el entorno de Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "coredigital.settings")
django.setup()

from reldigital.models import User, Entity, Report, Notice

def seed():
    print("Iniciando la carga de datos de prueba...")

    # 1. Crear Usuarios falsos
    users = []
    for i in range(5):
        username = f"user_{i}_{random.randint(1000, 9999)}"
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "code": f"C{random.randint(1000, 9999)}",
                "name": f"Nombre {i}",
                "last_name": f"Apellido {i}",
                "dui": f"{random.randint(10000000, 99999999)}-{random.randint(0, 9)}",
                "short_name": f"User {i}",
                "position": "Ingeniero",
                "email": f"{username}@ejemplo.com",
            }
        )
        if created:
            user.set_password("password123")
            user.save()
        users.append(user)
    
    print(f"✅ Se crearon/obtuvieron {len(users)} usuarios.")

    # 2. Crear Plantas (Type 1)
    plants = []
    for i in range(2):
        plant = Entity.objects.create(
            name=f"Planta {i+1}",
            type=1,
            tag=f"PLT-{random.randint(100, 999)}-{i+1}",
            created_by=random.choice(users)
        )
        plants.append(plant)

    # 3. Crear Áreas (Type 2)
    areas = []
    for plant in plants:
        for i in range(3):
            area = Entity.objects.create(
                name=f"Área {i+1} de {plant.name}",
                type=2,
                tag=f"AREA-{random.randint(100, 999)}",
                parent=plant,
                created_by=random.choice(users)
            )
            areas.append(area)

    # 4. Crear Rutas (Type 3) - PDM y NDT
    pdm_routes = []
    ndt_routes = []
    for area in areas:
        # 1 ruta PDM y 1 ruta NDT por área
        route_pdm = Entity.objects.create(
            name=f"Ruta PDM de {area.name}",
            type=3,
            tag=f"RT-PDM-{random.randint(100, 999)}",
            parent=area,
            created_by=random.choice(users)
        )
        pdm_routes.append(route_pdm)

        route_ndt = Entity.objects.create(
            name=f"Ruta NDT de {area.name}",
            type=3,
            tag=f"RT-NDT-{random.randint(100, 999)}",
            parent=area,
            created_by=random.choice(users)
        )
        ndt_routes.append(route_ndt)

    # 5. Jerarquía PDM: Equipo -> Componente
    equipments = []
    pdm_components = []
    for route in pdm_routes:
        for i in range(2):
            equip = Entity.objects.create(
                name=f"Equipo {i+1} - {route.name}",
                type=4,
                tag=f"EQ-{random.randint(1000, 9999)}",
                parent=route,
                created_by=random.choice(users)
            )
            equipments.append(equip)
            
            for j in range(2):
                comp = Entity.objects.create(
                    name=f"Componente PDM {j+1} de {equip.name}",
                    type=6,
                    tag=f"COMP-PDM-{random.randint(1000, 9999)}",
                    parent=equip,
                    created_by=random.choice(users)
                )
                pdm_components.append(comp)

    # 6. Jerarquía NDT: Item -> Componente
    items = []
    ndt_components = []
    for route in ndt_routes:
        for i in range(2):
            item = Entity.objects.create(
                name=f"Item {i+1} de {route.name}",
                type=5,
                tag=f"IT-{random.randint(1000, 9999)}",
                parent=route,
                created_by=random.choice(users)
            )
            items.append(item)
            
            for j in range(2):
                comp = Entity.objects.create(
                    name=f"Componente NDT {j+1} de {item.name}",
                    type=6,
                    tag=f"COMP-NDT-{random.randint(1000, 9999)}",
                    parent=item,
                    created_by=random.choice(users)
                )
                ndt_components.append(comp)
            
    print(f"✅ Se crearon Entidades jerárquicas: {len(plants)} plantas, {len(areas)} áreas, {len(pdm_routes)+len(ndt_routes)} rutas, {len(equipments)} equipos, {len(items)} items, {len(pdm_components)+len(ndt_components)} componentes.")

    # 7. Crear Reportes
    reports = []
    # Reportes para PDM (work_type=1)
    for equip in equipments:
        for _ in range(random.randint(1, 2)):
            report = Report.objects.create(
                entity=equip,
                name=f"Reporte PDM - {equip.name}",
                program=random.choice([1, 2]),
                work_type=1, # PDM
                service_type=random.randint(1, 9),
                execution_status=random.choice([1, 2]),
                condition=random.randint(1, 4),
                diagnostic="Diagnóstico PDM simulado.",
                recomendations="Recomendación PDM simulada.",
                created_by=random.choice(users)
            )
            reports.append(report)
            
    # Reportes para NDT (work_type=2)
    for item in items:
        for _ in range(random.randint(1, 2)):
            report = Report.objects.create(
                entity=item,
                name=f"Reporte NDT - {item.name}",
                program=random.choice([1, 2]),
                work_type=2, # NDT
                service_type=random.randint(1, 9),
                execution_status=random.choice([1, 2]),
                condition=random.randint(1, 4),
                diagnostic="Diagnóstico NDT simulado.",
                recomendations="Recomendación NDT simulada.",
                created_by=random.choice(users)
            )
            reports.append(report)
            
    print(f"✅ Se crearon {len(reports)} reportes.")

    # 8. Crear Avisos (Notices)
    notices = []
    for report in random.sample(reports, k=len(reports)//2):
        notice = Notice.objects.create(
            report=report,
            name=f"Aviso para {report.name}",
            date=datetime.now().date() - timedelta(days=random.randint(0, 60)),
            status=random.choice([1, 2]),
            ot_status=random.choice([1, 2]),
            ot_number=f"OT-{random.randint(10000, 99999)}",
            status_real=random.choice([1, 2]),
            comment="Comentario automático de aviso.",
            created_by=random.choice(users)
        )
        notices.append(notice)

    print(f"✅ Se crearon {len(notices)} avisos (notices).")
    print("🚀 ¡Carga de datos de prueba completada exitosamente!")

if __name__ == "__main__":
    seed()
