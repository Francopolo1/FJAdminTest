from django.contrib import admin
from django.utils.html import format_html
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display   = [
        "pk", "instance", "user", "channel",
        "subject_short", "is_sent", "retry_count", "scheduled_at", "sent_at",
    ]
    list_filter    = ["channel", "is_sent"]
    search_fields  = ["instance__reference_no", "user__full_name", "user__email", "subject"]
    readonly_fields = ["scheduled_at", "sent_at", "retry_count", "error_message"]
    ordering       = ["-scheduled_at"]
    actions        = ["resend_selected"]

    def subject_short(self, obj):
        return (obj.subject or "")[:60]
    subject_short.short_description = "Subject"

    def resend_selected(self, request, queryset):
        from .tasks import _route_notification
        count = 0
        for notif in queryset.filter(is_sent=False):
            notif.retry_count   = 0
            notif.error_message = None
            notif.save(update_fields=["retry_count", "error_message"])
            _route_notification.delay(notif.pk)
            count += 1
        self.message_user(request, f"Re-queued {count} notification(s).")
    resend_selected.short_description = "Re-send selected unsent notifications"
