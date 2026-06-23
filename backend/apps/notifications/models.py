from django.db import models
from django.conf import settings
from apps.core.db_fields import new_guid_str
from ..workflows.models import WorkflowInstance


class Notification(models.Model):
    CHANNEL_CHOICES = [
        ("Email", "Email"),
        ("SMS", "SMS"),
        ("Push", "Push"),
        ("Teams", "Microsoft Teams"),
        ("Slack", "Slack"),
    ]

    notif_id     = models.CharField(primary_key=True, max_length=36, default=new_guid_str)
    instance     = models.ForeignKey(
        WorkflowInstance, on_delete=models.CASCADE,
        db_column="instance_id", related_name="notifications"
    )
    user         = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        db_column="user_Id", related_name="notifications"
    )
    channel      = models.CharField(max_length=50, choices=CHANNEL_CHOICES, default="Email")
    subject      = models.CharField(max_length=500, blank=True, null=True)
    body         = models.TextField()
    is_sent      = models.BooleanField(default=False, db_index=True)
    scheduled_at = models.DateTimeField(auto_now_add=True)
    sent_at      = models.DateTimeField(null=True, blank=True)
    retry_count  = models.SmallIntegerField(default=0)
    error_message = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "notification"
        managed  = False
        ordering = ["-scheduled_at"]

    def __str__(self):
        return f"[{self.channel}] {self.subject or 'No subject'} → {self.user}"
