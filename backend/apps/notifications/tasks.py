"""
Celery tasks for the notifications app.

Dispatch pipeline:
  Celery beat calls dispatch_pending_notifications() every 5 min.
  That task fans out to channel-specific tasks (_send_email, _send_sms, …).
  Each delivery task marks the Notification is_sent=True on success,
  or increments retry_count and stores error_message on failure.

  Maximum retries = 3  (configurable via MAX_RETRIES).
  After 3 failures the notification is abandoned but left in the DB
  for audit purposes (error_message contains the last exception).
"""
import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)
MAX_RETRIES = 3


# ── Main dispatcher ────────────────────────────────────────────────────────
@shared_task(bind=True)
def dispatch_pending_notifications(self):
    """
    Fetch every unsent notification whose scheduled_at <= now
    and hand it off to a channel-specific delivery task.
    Skips notifications that have already exceeded MAX_RETRIES.
    """
    from .models import Notification

    pending = Notification.objects.filter(
        is_sent=False,
        scheduled_at__lte=timezone.now(),
        retry_count__lt=MAX_RETRIES,
    ).select_related("user", "instance")

    dispatched = 0
    for notif in pending:
        _route_notification.delay(notif.pk)
        dispatched += 1

    logger.info("Dispatched %d notifications", dispatched)
    return f"Dispatched {dispatched} notifications"


@shared_task(bind=True, max_retries=MAX_RETRIES, default_retry_delay=60)
def _route_notification(self, notif_id):
    """Route a single Notification to the correct channel sender."""
    from .models import Notification
    try:
        notif = Notification.objects.select_related("user", "instance").get(pk=notif_id)
    except Notification.DoesNotExist:
        return

    if notif.is_sent:
        return  # Already handled (race condition guard)

    try:
        _deliver(notif)
        notif.is_sent = True
        notif.sent_at = timezone.now()
        notif.save(update_fields=["is_sent", "sent_at"])
        logger.info("Sent notification %d via %s", notif_id, notif.channel)
    except Exception as exc:
        notif.retry_count   += 1
        notif.error_message  = str(exc)
        notif.save(update_fields=["retry_count", "error_message"])
        logger.warning("Notification %d failed (attempt %d): %s", notif_id, notif.retry_count, exc)
        if notif.retry_count < MAX_RETRIES:
            raise self.retry(exc=exc, countdown=60 * notif.retry_count)


def _deliver(notif):
    """Route to the right transport based on channel."""
    handlers = {
        "Email":  _send_email,
        "SMS":    _send_sms,
        "Push":   _send_push,
        "Teams":  _send_teams,
        "Slack":  _send_slack,
    }
    handler = handlers.get(notif.channel)
    if handler:
        handler(notif)
    else:
        raise ValueError(f"Unknown notification channel: {notif.channel}")


# ── Channel handlers ───────────────────────────────────────────────────────
def _send_email(notif):
    """
    Send via Django's email backend.
    In production replace with SendGrid / SES / Postmark SDK.
    """
    from django.core.mail import send_mail
    from django.conf import settings

    send_mail(
        subject      = notif.subject or "(no subject)",
        message      = notif.body,
        from_email   = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@workflow.app"),
        recipient_list = [notif.user.email],
        fail_silently = False,
    )


def _send_sms(notif):
    """
    Stub for SMS delivery (e.g. Twilio).
    Replace the body of this function with your Twilio client call.
    """
    phone = getattr(notif.user, "phone_number", None)
    if not phone:
        raise ValueError(f"User {notif.user.pk} has no phone_number for SMS delivery.")
    # Example Twilio stub (uncomment and configure):
    # from twilio.rest import Client
    # client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    # client.messages.create(body=notif.body, from_=settings.TWILIO_FROM, to=phone)
    logger.info("[SMS stub] To: %s | Body: %s", phone, notif.body[:80])


def _send_push(notif):
    """
    Stub for push notifications (e.g. Firebase FCM).
    Replace with your FCM / APNs SDK call.
    """
    logger.info("[Push stub] To user %d | Subject: %s", notif.user.pk, notif.subject)


def _send_teams(notif):
    """
    Post to a Microsoft Teams Incoming Webhook.
    Set TEAMS_WEBHOOK_URL in settings / .env.
    """
    import requests
    from django.conf import settings

    webhook_url = getattr(settings, "TEAMS_WEBHOOK_URL", None)
    if not webhook_url:
        raise ValueError("TEAMS_WEBHOOK_URL is not configured.")

    payload = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "summary": notif.subject,
        "themeColor": "0076D7",
        "sections": [{"activityTitle": notif.subject, "activityText": notif.body}],
    }
    resp = requests.post(webhook_url, json=payload, timeout=10)
    resp.raise_for_status()


def _send_slack(notif):
    """
    Post to a Slack Incoming Webhook.
    Set SLACK_WEBHOOK_URL in settings / .env.
    """
    import requests
    from django.conf import settings

    webhook_url = getattr(settings, "SLACK_WEBHOOK_URL", None)
    if not webhook_url:
        raise ValueError("SLACK_WEBHOOK_URL is not configured.")

    payload = {"text": f"*{notif.subject}*\n{notif.body}"}
    resp = requests.post(webhook_url, json=payload, timeout=10)
    resp.raise_for_status()


# ── Action-triggered helpers (called from workflows.tasks) ─────────────────
@shared_task(bind=True, max_retries=3)
def send_email_notification(self, instance_id, template, to_role):
    """
    Create + dispatch an email notification from a StepAction config.
    to_role: 'manager' | 'submitter' | 'finance' — resolved to a real user here.
    """
    from workflows.models import WorkflowInstance
    from .models import Notification

    try:
        instance = WorkflowInstance.objects.select_related(
            "initiated_by", "current_step", "workflow"
        ).get(pk=instance_id)
    except WorkflowInstance.DoesNotExist:
        return

    recipient = _resolve_role(instance, to_role)
    if not recipient:
        logger.warning("Could not resolve role '%s' for instance %d", to_role, instance_id)
        return

    subject, body = _render_template(template, instance)
    notif = Notification.objects.create(
        instance=instance,
        user=recipient,
        channel="Email",
        subject=subject,
        body=body,
    )
    _route_notification.delay(notif.pk)


@shared_task(bind=True, max_retries=3)
def call_external_api(self, instance_id, endpoint, method="POST"):
    """Fire a webhook / internal API call from a StepAction."""
    import requests
    from workflows.models import WorkflowInstance

    try:
        instance = WorkflowInstance.objects.select_related("workflow").get(pk=instance_id)
    except WorkflowInstance.DoesNotExist:
        return

    from django.conf import settings
    base_url = getattr(settings, "INTERNAL_API_BASE_URL", "http://127.0.0.1:8000/")
    url      = f"{base_url}{endpoint}"

    payload = {
        "instance_id":  instance.pk,
        "reference_no": instance.reference_no,
        "status":       instance.status,
        "workflow":     instance.workflow.name,
    }

    try:
        resp = requests.request(method, url, json=payload, timeout=15)
        resp.raise_for_status()
        logger.info("API call %s %s -> %d", method, url, resp.status_code)
    except Exception as exc:
        logger.error("API call failed: %s", exc)
        raise self.retry(exc=exc, countdown=120)


# ── Helpers ────────────────────────────────────────────────────────────────
def _resolve_role(instance, role):
    """Map a role string to an AppUser."""
    if role == "submitter":
        return instance.initiated_by
    if role == "manager":
        return instance.initiated_by.manager
    # Extend with more roles (e.g. finance team) as needed
    return None


def _render_template(template_name, instance):
    """
    Minimal template renderer.
    In production swap this for Django templates or a transactional email service.
    """
    ref  = instance.reference_no
    wf   = instance.workflow.name
    user = instance.initiated_by.full_name

    templates = {
        "claim_submitted": (
            f"Expense claim submitted – {ref}",
            f"Hi,\n\n{user} has submitted expense claim {ref} ({wf}) for your review.\n\nPlease log in to action it.",
        ),
        "claim_approved": (
            f"Expense claim approved – {ref}",
            f"Hi {user},\n\nYour expense claim {ref} has been approved. Reimbursement will follow shortly.",
        ),
        "claim_rejected": (
            f"Expense claim rejected – {ref}",
            f"Hi {user},\n\nUnfortunately your expense claim {ref} has been rejected. Please contact your manager for details.",
        ),
    }
    return templates.get(
        template_name,
        (f"Workflow update – {ref}", f"Your workflow request {ref} ({wf}) has been updated."),
    )
