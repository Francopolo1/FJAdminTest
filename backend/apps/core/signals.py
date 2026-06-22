"""Signals for the core app."""
from django.db.models.signals import post_save
from django.dispatch import receiver


def update_next_visit_date_on_save(sender, instance, created, **kwargs):
    """Update next_visit_date whenever a ProgramFacility is saved.

    This signal recalculates next_visit_date based on:
    - Latest checklist_run.started_at (if exists)
    - last_visit_date field (fallback if no checklists)
    - risk_assessment_level.visit_frequency_days (if set)

    The next_visit_date = effective_last_visit_date + visit_frequency_days

    Note: This function is intentionally NOT decorated with @receiver to allow
    manual control over when it's registered. See apps.py for registration.
    """
    import logging
    logger = logging.getLogger(__name__)

    try:
        # Only attempt calculation if facility has risk assessment level
        if not instance.risk_assessment_level:
            return

        # Only attempt calculation if we can get an effective last visit date
        effective_date = instance.get_effective_last_visit_date()
        if not effective_date:
            return

        # Attempt to recalculate
        if instance.update_next_visit_date():
            # Only save if next_visit_date actually changed (avoid infinite recursion)
            # Use update() to avoid triggering the signal again
            from .models import ProgramFacility
            ProgramFacility.objects.filter(program_facility_id=instance.program_facility_id).update(
                next_visit_date=instance.next_visit_date
            )
    except Exception as e:
        # Log the error but don't fail the save operation
        logger.warning(
            f"Failed to update next_visit_date for facility {instance.program_facility_id}: {e}",
            exc_info=True
        )
