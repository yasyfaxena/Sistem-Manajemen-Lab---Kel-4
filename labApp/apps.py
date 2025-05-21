from django.apps import AppConfig

class LabAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'labApp'

    def ready(self):
        """
        Import signals when Django starts to ensure signals are registered.
        """
        try:
            import labApp.signals
        except Exception as e:
            print(f"Error importing signals: {e}")