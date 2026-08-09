import os
import django

# Configurar el entorno de Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "coredigital.settings")
django.setup()

from reldigital.models import User, Entity, Report, Notice, NoticeImage

def clear_db():
    print("Iniciando el proceso de limpieza de la base de datos...")

    # 1. Eliminar NoticeImages (si existen)
    deleted_images, _ = NoticeImage.objects.all().delete()
    print(f"🗑️  Imágenes de avisos eliminadas: {deleted_images}")

    # 2. Eliminar Notices
    deleted_notices, _ = Notice.objects.all().delete()
    print(f"🗑️  Avisos eliminados: {deleted_notices}")

    # 3. Eliminar Reportes
    deleted_reports, _ = Report.objects.all().delete()
    print(f"🗑️  Reportes eliminados: {deleted_reports}")

    # 4. Eliminar Entidades (Plantas, Áreas, Rutas, Equipos, etc.)
    deleted_entities, _ = Entity.objects.all().delete()
    print(f"🗑️  Entidades eliminadas: {deleted_entities}")

    # 5. Eliminar Usuarios excepto el que tiene id=1
    deleted_users, _ = User.objects.exclude(id=1).delete()
    print(f"🗑️  Usuarios eliminados: {deleted_users}")

    print("✅ ¡Base de datos vaciada con éxito! (El usuario con id=1 se ha mantenido intacto).")

if __name__ == "__main__":
    clear_db()
