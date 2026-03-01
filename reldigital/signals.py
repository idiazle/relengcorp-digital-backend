from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import User, Entity, Report, Notice


@receiver(pre_save, sender=User)
@receiver(pre_save, sender=Entity)
@receiver(pre_save, sender=Report)
@receiver(pre_save, sender=Notice)
def set_deleted_at(sender, instance, **kwargs):
    """
    Establece automáticamente deleted_at cuando deleted se marca como True.
    
    IMPORTANTE: 
    - Esto es una ELIMINACIÓN LÓGICA (soft-delete)
    - NO se elimina el registro de la base de datos
    - NO se eliminan archivos asociados (attachments, images)
    - Solo se marca el registro como eliminado y se registra la fecha
    - Los GET solo mostrarán registros con deleted=False
    """
    if instance.deleted and not instance.deleted_at:
        # Marcar la fecha de eliminación lógica
        instance.deleted_at = timezone.now()
    elif not instance.deleted and instance.deleted_at:
        # Si se restaura el registro, limpiar deleted_at
        instance.deleted_at = None
