from django.apps import AppConfig


class AccommodationFacilitiesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accommodation_facilities'
    verbose_name = "Obiekty noclegowe i ich udogodnienia"
    label = "accommodation_facilities"

    def ready(self):
      from . import signals