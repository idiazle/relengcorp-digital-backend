from django.apps import AppConfig


class ReldigitalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reldigital'

    def ready(self):
        import reldigital.signals
