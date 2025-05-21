from django.apps import AppConfig

class MyLabAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mylabapp'

    def ready(self):
        """
        Import signals when Django starts to ensure signals are registered.
        """
        try:
            import mylabapp.signals  # noqa
        except Exception as e:
            print(f"Error importing signals: {e}")