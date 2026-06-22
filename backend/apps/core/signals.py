"""Signals for the core app."""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import ProgramFacility


@receiver(post_save, sender=ProgramFacility)
def update_next_visit_date_on_save(sender, instance, created, **kwargs):
    """Update next_visit_date whenever a ProgramFacility is saved.

    This signal recalculates next_visit_date based on:
    - last_visit_date (if set)
    - risk_assessment_level.visit_frequency_days (if set)

    The next_visit_date = last_visit_date + visit_frequency_days
    """
    if instance.update_next_visit_date():
        # Only save if next_visit_date actually changed (avoid infinite recursion)
        # Use update() to avoid triggering the signal again
        ProgramFacility.objects.filter(program_facility_id=instance.program_facility_id).update(
            next_visit_date=instance.next_visit_date
        )
