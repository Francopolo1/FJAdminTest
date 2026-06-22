from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'

    def ready(self):
        """Register signals when app is ready."""
        try:
            from django.db.models.signals import post_save
            from .models import ProgramFacility
            from .signals import update_next_visit_date_on_save

            # Disconnect any existing connections to avoid duplicates
            post_save.disconnect(update_next_visit_date_on_save, sender=ProgramFacility)

            # Register the signal
            post_save.connect(update_next_visit_date_on_save, sender=ProgramFacility)
        except Exception as e:
            # Log but don't fail app startup
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to register next_visit_date signal: {e}")
