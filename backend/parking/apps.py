from django.apps import AppConfig


class ParkingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "parking"
    
    def ready(self):
        # Import signals for updating spot counts
        import parking.signals
