from django.utils import timezone
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
import django_filters

from .models import Notification
from .serializers import (
    NotificationSerializer, NotificationCreateSerializer, BroadcastSerializer,
)


class NotificationFilter(django_filters.FilterSet):
    instance  = django_filters.NumberFilter(field_name="instance_id")
    channel   = django_filters.MultipleChoiceFilter(choices=Notification.CHANNEL_CHOICES)
    is_sent   = django_filters.BooleanFilter()
    sent_after  = django_filters.DateTimeFilter(field_name="sent_at", lookup_expr="gte")
    sent_before = django_filters.DateTimeFilter(field_name="sent_at", lookup_expr="lte")

    class Meta:
        model  = Notification
        fields = ["instance", "channel", "is_sent"]


class NotificationViewSet(viewsets.ModelViewSet):
    """
    Endpoints:
      GET    /api/notifications/               — list (own notifs; admin sees all)
      GET    /api/notifications/{id}/          — detail
      POST   /api/notifications/               — create ad-hoc notification (admin)
      POST   /api/notifications/{id}/resend/   — retry a failed notification (admin)
      POST   /api/notifications/{id}/mark-sent/ — manually mark sent (admin)
      POST   /api/notifications/broadcast/     — send to all instance participants (admin)
      GET    /api/notifications/unread-count/  — count of unsent notifs for current user
    """
    serializer_class   = NotificationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class    = NotificationFilter
    search_fields      = ["subject", "instance__reference_no"]
    ordering_fields    = ["scheduled_at", "sent_at"]
    ordering           = ["-scheduled_at"]

    def get_queryset(self):
        qs = Notification.objects.select_related(
            "user", "instance__workflow"
        )
        if not self.request.user.is_staff:
            qs = qs.filter(user=self.request.user)
        return qs

    def get_serializer_class(self):
        if self.action == "create":
            return NotificationCreateSerializer
        return NotificationSerializer

    def get_permissions(self):
        if self.action in ("create", "resend", "mark_sent", "broadcast"):
            return [IsAdminUser()]
        return [IsAuthenticated()]

    # ── resend ─────────────────────────────────────────────────────────────
    @action(detail=True, methods=["post"])
    def resend(self, request, pk=None):
        """Reset retry counter and re-queue a failed notification."""
        notif = self.get_object()
        if notif.is_sent:
            return Response(
                {"detail": "Notification has already been sent successfully."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        notif.retry_count   = 0
        notif.error_message = None
        notif.save(update_fields=["retry_count", "error_message"])

        from .tasks import _route_notification
        _route_notification.delay(notif.pk)
        return Response(
            {"detail": f"Notification {notif.pk} re-queued for delivery."},
            status=status.HTTP_202_ACCEPTED,
        )

    # ── mark_sent ──────────────────────────────────────────────────────────
    @action(detail=True, methods=["post"], url_path="mark-sent")
    def mark_sent(self, request, pk=None):
        """Manually mark a notification as sent (useful for manual channels)."""
        notif         = self.get_object()
        notif.is_sent = True
        notif.sent_at = timezone.now()
        notif.save(update_fields=["is_sent", "sent_at"])
        return Response(NotificationSerializer(notif).data)

    # ── broadcast ──────────────────────────────────────────────────────────
    @action(detail=False, methods=["post"])
    def broadcast(self, request):
        """
        Send a message to every participant (initiator + task assignees)
        of a given workflow instance.

        Body:
          { "instance": <id>, "channel": "Email", "subject": "...", "body": "..." }
        """
        serializer = BroadcastSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        instance_id = request.data.get("instance")
        if not instance_id:
            return Response({"detail": "instance is required."}, status=status.HTTP_400_BAD_REQUEST)

        from workflows.models import WorkflowInstance
        try:
            instance = WorkflowInstance.objects.get(pk=instance_id)
        except WorkflowInstance.DoesNotExist:
            return Response({"detail": "Instance not found."}, status=status.HTTP_404_NOT_FOUND)

        # Collect unique participants
        from users.models import AppUser
        participant_ids = set()
        participant_ids.add(instance.initiated_by_id)
        participant_ids.update(
            instance.tasks.values_list("assigned_to_id", flat=True)
        )

        created = []
        for user_id in participant_ids:
            notif = Notification.objects.create(
                instance=instance,
                user_id=user_id,
                channel=serializer.validated_data["channel"],
                subject=serializer.validated_data["subject"],
                body=serializer.validated_data["body"],
            )
            created.append(notif)

        # Fire delivery tasks
        from .tasks import _route_notification
        for notif in created:
            _route_notification.delay(notif.pk)

        return Response(
            {
                "detail": f"Broadcast queued for {len(created)} recipients.",
                "notification_ids": [n.pk for n in created],
            },
            status=status.HTTP_202_ACCEPTED,
        )

    # ── unread_count ───────────────────────────────────────────────────────
    @action(detail=False, methods=["get"], url_path="unread-count")
    def unread_count(self, request):
        """Return count of unsent notifications for the requesting user."""
        count = Notification.objects.filter(
            user=request.user, is_sent=False
        ).count()
        return Response({"unread_count": count})
