from celery import shared_task
from django.utils import timezone


@shared_task(bind=True, max_retries=3)
def mark_overdue_tasks(self):
    """Mark Pending tasks past their due date as Overdue."""
    from .models import WorkflowTask
    updated = WorkflowTask.objects.filter(
        status="Pending",
        due_date__lt=timezone.now(),
    ).update(status="Overdue")
    return f"Marked {updated} tasks as Overdue"


@shared_task(bind=True, max_retries=3)
def escalate_sla_breaches(self):
    """
    Create escalation notifications for instances whose due date
    is within the next 4 hours and still InProgress.
    """
    from .models import WorkflowInstance, AuditLog
    from django.apps import apps

    Notification = apps.get_model("notifications", "Notification")

    window = timezone.now() + timezone.timedelta(hours=4)
    at_risk = WorkflowInstance.objects.filter(
        status="InProgress",
        due_date__lte=window,
        due_date__gte=timezone.now(),
    ).select_related("initiated_by", "current_step", "workflow")

    created = 0
    for instance in at_risk:
        # Avoid duplicate escalation notifications
        already = Notification.objects.filter(
            instance=instance,
            subject__startswith="SLA Warning",
            is_sent=False,
        ).exists()
        if already:
            continue

        hours_left = max(0, int((instance.due_date - timezone.now()).total_seconds() / 3600))
        Notification.objects.create(
            instance=instance,
            user=instance.initiated_by,
            channel="Email",
            subject=f"SLA Warning – {instance.reference_no}",
            body=(
                f"Your request {instance.reference_no} "
                f"({instance.workflow.name}) is due in {hours_left} hour(s).\n"
                f"Current step: {instance.current_step.step_name if instance.current_step else 'N/A'}"
            ),
        )
        created += 1

    return f"Created {created} SLA-warning notifications"


@shared_task(bind=True, max_retries=3)
def run_step_actions(self, instance_id, step_id):
    """Execute automated StepActions for a given step on entry."""
    from .models import WorkflowInstance, StepAction
    try:
        instance = WorkflowInstance.objects.get(pk=instance_id)
        actions  = StepAction.objects.filter(step_id=step_id).order_by("execution_order")
        for action in actions:
            _dispatch_action(instance, action)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


def _dispatch_action(instance, action):
    """Route a StepAction to its handler."""
    import importlib

    config = action.action_config or {}
    notifications_tasks = importlib.import_module("notifications.tasks")

    if action.action_type == "SendEmail":
        notifications_tasks.send_email_notification.delay(
            instance_id=instance.pk,
            template=config.get("template", ""),
            to_role=config.get("to", ""),
        )
    elif action.action_type == "CallAPI":
        notifications_tasks.call_external_api.delay(
            instance_id=instance.pk,
            endpoint=config.get("endpoint", ""),
            method=config.get("method", "POST"),
        )
