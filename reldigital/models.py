from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
import os
import uuid

project_name = 'releng_'
class User(AbstractUser):
    code = models.CharField(max_length=12, unique=True)
    name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=150)
    username = models.CharField(max_length=150, unique=True)
    dui = models.CharField(max_length=20, unique=True)
    short_name = models.CharField(max_length=50)
    position = models.CharField(max_length=100)
    email = models.EmailField(max_length=150, unique=True)
    password = models.TextField()
    phone = models.TextField(max_length=150, null=True, blank=True, default=None)
    extra_emails = models.TextField(max_length=200, null=True, blank=True, default=None)
    deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    groups = models.ManyToManyField(
        Group,
        related_name='reldigital_users',  
        blank=True
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='reldigital_users_permissions',
        blank=True
    )

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        db_table = f'{project_name}users'

def get_upload_entity(instance, filename):
    ext = os.path.splitext(filename)[1]
    unique_name = f"{uuid.uuid4()}{ext}"

    type_map = {
        1: "plants",
        2: "areas",
        3: "routes",
        4: "equipments",
        5: "items",
        6: "components",
    }

    entity_type_folder = type_map.get(instance.type, "entities")
    entity_id = instance.id if instance.id else "temp"

    return os.path.join(
        entity_type_folder,
        str(entity_id),
        unique_name
    )

class Entity(models.Model):
    TYPE_CHOICES = [
        (1, 'Plant'),
        (2, 'Area'),
        (3, 'Route'),
        (4, 'Equipment'),
        (5, 'Item'),
        (6, 'Component'),
    ]
     
    name=models.CharField(max_length=200, default="")
    type = models.IntegerField(choices=TYPE_CHOICES, default=1)
    tag = models.CharField(max_length=100, null=True, blank=True, unique=True)
    attachment = models.FileField(upload_to=get_upload_entity, null=True, blank=True)
    parent=models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name="children")
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    extra_info = models.JSONField(default=dict, null=True, blank=True)
    deleted= models.BooleanField(default=False)
    created_at= models.DateTimeField(auto_now_add=True, blank=True, null=True)
    deleted_at=models.DateTimeField(blank=True, null=True)
    updated_at= models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = f'{project_name}entities'
        
    def __str__(self):
        return self.name
    
    def get_hierarchy(self):
        """
        Retorna la jerarquía completa desde la entidad actual hasta la raíz (planta)
        Retorna un diccionario con la estructura jerárquica completa
        """
        hierarchy = {
            'current': {
                'id': self.id,
                'name': self.name,
                'type': self.type,
                'type_name': self.get_type_display(),
                'tag': self.tag
            }
        }
        
        # Recorrer hacia arriba para obtener padres
        current = self.parent
        level = 0
        
        while current and level < 5:  # Máximo 5 niveles para evitar loops infinitos
            level += 1
            type_key = current.get_type_display().lower()
            
            hierarchy[type_key] = {
                'id': current.id,
                'name': current.name,
                'type': current.type,
                'type_name': current.get_type_display(),
                'tag': current.tag
            }
            
            current = current.parent
        
        return hierarchy

def get_upload_reports(instance, filename):
    ext = os.path.splitext(filename)[1]
    unique_name = f"{uuid.uuid4()}{ext}"

    entity_id = instance.entity.id if instance.entity else "unknown"

    return os.path.join(
        "reports",
        str(entity_id),
        unique_name
    )

class Report(models.Model):
    entity = models.ForeignKey(Entity, null=True, blank=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=250, null=True, blank=True)
    attachment = models.FileField(upload_to=get_upload_reports, null=True, blank=True)
    program = models.IntegerField(
        choices=[
            (1, 'Programado'),
            (2, 'No programado')
        ],
    default=1)
    work_type = models.IntegerField(
        choices=[
            (1, 'PDM'),
            (2, 'NDT')
        ],
        default=1
    )
    service_type = models.IntegerField(
        choices=[
            (1, 'Vibraciones y temperatura'),
            (2, 'Alineamiento de ejes'),
            (3, 'Termografía infrarroja'),
            (4, 'Ultrasonido convencional'),
            (5, 'Tintes Penetrantes'),
            (6, 'Ultrasonido avanzado'),
            (7, 'Metrología'),
            (8, 'Inspección visual'),
            (9, 'Otros')
        ],
        default=1
    )
    execution_status = models.IntegerField(
        choices=[
            (1, 'Ejecutado'),
            (2, 'No ejecutado')
        ],
    default=1)
    execution_date = models.DateTimeField(blank=True, null=True) 
    observations = models.TextField(null=True, blank=True)
    condition = models.IntegerField(
        choices=[
            (1, 'Normal'),
            (2, 'Tolerable'),
            (3, 'Precaución'),
            (4, 'Crítico')
        ],
    default=1)
    diagnostic = models.TextField(null=True, blank=True)    
    recomendations = models.TextField(null=True, blank=True)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    deleted= models.BooleanField(default=False)
    created_at= models.DateTimeField(auto_now_add=True, blank=True, null=True)
    deleted_at=models.DateTimeField(blank=True, null=True)
    updated_at= models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = f'{project_name}reports'
        indexes = [
            models.Index(fields=['entity', 'is_active']),
        ]
        
    def __str__(self):
        return self.name or f"Report {self.id}"
    
    def save(self, *args, **kwargs):
        from django.db import transaction
        
        # Verificar si está activando este reporte
        if self.is_active and self.entity:
            # Usar transacción para evitar race conditions
            with transaction.atomic():
                # Primero guardar este reporte
                super().save(*args, **kwargs)
                
                # Luego desactivar todos los demás reportes activos de la misma entidad
                Report.objects.filter(
                    entity=self.entity,
                    is_active=True,
                    deleted=False
                ).exclude(id=self.id).update(is_active=False)
        else:
            # Si no está activo o no tiene entidad, guardar normalmente
            super().save(*args, **kwargs)

class Notice(models.Model):
    report = models.ForeignKey(Report, null=True, blank=True, on_delete=models.CASCADE, related_name='notices')
    name = models.CharField(max_length=250)
    date = models.DateField()
    status = models.IntegerField(choices=[(1, 'Abierto'), (2, 'Cerrado')], default=1)
    ot_status = models.IntegerField(choices=[(1, 'Abierto'), (2, 'Cerrado')], default=1)
    ot_number = models.CharField(null=True, blank=True, max_length=250)
    ot_date = models.DateField(null=True, blank=True)
    status_real = models.IntegerField(choices=[(1, 'Atendido'), (2, 'No antendido')], default=1)
    comment = models.TextField(default=None, null=True, blank=True)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    deleted= models.BooleanField(default=False)
    created_at= models.DateTimeField(auto_now_add=True, blank=True, null=True)
    deleted_at=models.DateTimeField(blank=True, null=True)
    updated_at= models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = f'{project_name}notices'

class NoticeImage(models.Model):
    notice = models.ForeignKey(Notice, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='notice_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = f'{project_name}notice_images'