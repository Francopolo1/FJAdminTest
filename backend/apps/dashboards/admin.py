from django.contrib import admin
from .models import VWInstanceDashboard, VWPendingTask, VWChecklistProgress


@admin.register(VWInstanceDashboard)
class InstanceDashboardAdmin(admin.ModelAdmin):
    list_display   = ["reference_no","workflow_name","status","priority","initiated_by","started_at","due_date","checklist_pct_done"]
    list_filter    = ["status","category"]
    search_fields  = ["reference_no","workflow_name","initiated_by"]
    ordering       = ["-started_at"]
    readonly_fields = [f.name for f in VWInstanceDashboard._meta.get_fields()]

    def has_add_permission(self, request):    return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False


@admin.register(VWPendingTask)
class PendingTaskAdmin(admin.ModelAdmin):
    list_display  = ["reference_no","step_name","assigned_to","status","due_date","hours_remaining","priority"]
    list_filter   = ["status"]
    search_fields = ["reference_no","assigned_to","step_name"]
    ordering      = ["due_date"]
    readonly_fields = [f.name for f in VWPendingTask._meta.get_fields()]

    def has_add_permission(self, request):    return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False


@admin.register(VWChecklistProgress)
class ChecklistProgressAdmin(admin.ModelAdmin):
    list_display  = ["reference_no","checklist_title","run_status","pct_complete","blocks_advance","answered_required","required_items"]
    list_filter   = ["run_status","blocks_advance"]
    search_fields = ["reference_no","checklist_title"]
    readonly_fields = [f.name for f in VWChecklistProgress._meta.get_fields()]

    def has_add_permission(self, request):    return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False
