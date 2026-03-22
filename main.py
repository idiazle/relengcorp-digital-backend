import os
import django
import csv
import re

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "coredigital.settings")
django.setup()

from reldigital.models import Entity   # cambia "app" por tu app real

CSV_FILE = "reportes.csv"
PLANT_ID = 2


def component_code(name):

    name = name.upper()

    if "MOTOR" in name:
        return "MTR"

    if "BOMBA" in name:
        return "PMP"

    if "RODAM" in name:
        return "BRG"

    if "VENT" in name:
        return "FAN"

    if "ACOPLE" in name:
        return "CPL"

    letters = re.sub(r'[^A-Z]', '', name)

    return letters[:3] if letters else "CMP"


def run():

    plant = Entity.objects.get(id=PLANT_ID)

    routes_cache = {}
    equipment_cache = {}
    component_counter = {}

    with open(CSV_FILE, newline='', encoding='utf-8') as file:

        reader = csv.DictReader(file, delimiter=";")

        for row in reader:

            route_name = row["RUTA"].strip()
            equipment_name = row["EQUIPO"].strip()
            component_name = row["COMPONENTE"].strip()
            tag = row["TAG"].strip()

            # ----------------
            # ROUTE
            # ----------------

            if route_name not in routes_cache:

                route, created = Entity.objects.get_or_create(
                    name=route_name,
                    type=3,
                    parent=plant,
                    defaults={
                        "tag": route_name,
                        "extra_info": {}
                    }
                )

                routes_cache[route_name] = route

                if created:
                    print("Ruta creada:", route_name)

            route = routes_cache[route_name]

            # ----------------
            # EQUIPMENT
            # ----------------

            if tag not in equipment_cache:

                equipment, created = Entity.objects.get_or_create(
                    tag=tag,
                    type=4,
                    defaults={
                        "name": equipment_name,
                        "parent": route,
                        "extra_info": {}
                    }
                )

                equipment_cache[tag] = equipment

                if created:
                    print("Equipo creado:", tag)

            equipment = equipment_cache[tag]

            # ----------------
            # COMPONENT
            # ----------------

            code = component_code(component_name)

            key = (tag, code)

            if key not in component_counter:
                component_counter[key] = 1
            else:
                component_counter[key] += 1

            number = component_counter[key]

            component_tag = f"{tag}-{code}{number:02d}"

            exists = Entity.objects.filter(tag=component_tag, type=6).first()

            if not exists:

                component = Entity.objects.create(
                    name=component_name,
                    type=6,
                    tag=component_tag,
                    parent=equipment,
                    extra_info={}
                )

                print("Componente creado:", component_tag)


if __name__ == "__main__":
    run()