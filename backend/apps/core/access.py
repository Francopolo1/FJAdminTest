"""Shared helpers for scoping querysets to a user and their direct reports."""

from .models import UserProfile


def visible_user_ids(user):
    """Return the user's own id plus the ids of their direct reports.

    Used to scope dashboard/requests/tasks/checklists querysets so a
    supervisor sees their own records plus their direct reports' records.
    """
    profile = getattr(user, "profile", None)
    report_ids = (
        UserProfile.objects.filter(manager=profile).values_list("user_id", flat=True)
        if profile else []
    )
    return [user.id, *report_ids]
