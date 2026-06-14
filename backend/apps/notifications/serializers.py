from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    user_name        = serializers.CharField(source="user.full_name",           read_only=True)
    user_email       = serializers.CharField(source="user.email",               read_only=True)
    reference_no     = serializers.CharField(source="instance.reference_no",    read_only=True)
    workflow_name    = serializers.CharField(source="instance.workflow.name",    read_only=True)

    class Meta:
        model  = Notification
        fields = [
            "id", "instance", "reference_no", "workflow_name",
            "user", "user_name", "user_email",
            "channel", "subject", "body",
            "is_sent", "scheduled_at", "sent_at",
            "retry_count", "error_message",
        ]
        read_only_fields = ["is_sent", "scheduled_at", "sent_at", "retry_count", "error_message"]


class NotificationCreateSerializer(serializers.ModelSerializer):
    """Used internally (and by admin) to create ad-hoc notifications."""
    class Meta:
        model  = Notification
        fields = ["instance", "user", "channel", "subject", "body"]


class BroadcastSerializer(serializers.Serializer):
    """Broadcast a message to all participants of an instance."""
    channel = serializers.ChoiceField(choices=Notification.CHANNEL_CHOICES, default="Email")
    subject = serializers.CharField(max_length=500)
    body    = serializers.CharField()
