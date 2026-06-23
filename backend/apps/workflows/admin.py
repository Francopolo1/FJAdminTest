from django.contrib import admin
from .models import (
    WorkflowAuditLog, WorkflowDefinition, WorkflowStep, WorkflowTransition,
    StepAction, WorkflowInstance, WorkflowTask,
)


@admin.register(WorkflowStep)
class WorkflowStepAdmin(admin.ModelAdmin):
    list_display  = ["step_name", "workflow", "step_type", "step_order", "is_initial", "is_final"]
    list_filter   = ["step_type", "workflow"]
    search_fields = ["step_name", "workflow__name"]
    ordering      = ["workflow", "step_order"]


class WorkflowStepInline(admin.TabularInline):
    model  = WorkflowStep
    extra  = 0
    fields = ["step_name", "step_type", "step_order", "is_initial", "is_final", "sla_hours"]
    exclude = ["step_id"]


class WorkflowTransitionInline(admin.TabularInline):
    model  = WorkflowTransition
    extra  = 0
    fields = ["from_step", "to_step", "trigger_event", "transition_name"]
    exclude = ["transition_id"]


@admin.register(WorkflowDefinition)
class WorkflowDefinitionAdmin(admin.ModelAdmin):
    list_display  = ["name", "version", "category", "is_active", "created_at"]
    list_filter   = ["category", "is_active"]
    search_fields = ["name"]
    exclude       = ["workflow_id"]
    autocomplete_fields = ["program_facility_type_activity"]
    inlines       = [WorkflowStepInline, WorkflowTransitionInline]


class WorkflowTaskInline(admin.TabularInline):
    model          = WorkflowTask
    extra          = 0
    can_delete     = False
    max_num        = 0  # No adding tasks via inline
    fields         = ["step", "assigned_to", "assigned_by", "status", "due_date", "completed_at", "assigned_at"]
    readonly_fields = ["step", "assigned_to", "assigned_by", "status", "due_date", "completed_at", "assigned_at"]

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(WorkflowInstance)
class WorkflowInstanceAdmin(admin.ModelAdmin):
    list_display   = ["reference_no", "workflow", "initiated_by", "status", "priority", "started_at", "due_date"]
    list_filter    = ["status", "priority", "workflow"]
    search_fields  = ["reference_no", "initiated_by__first_name", "initiated_by__last_name"]
    readonly_fields = ["instance_id", "started_at", "completed_at"]
    autocomplete_fields = ["workflow", "initiated_by", "program_facility", "current_step"]
    inlines        = [WorkflowTaskInline]
    fieldsets = (
        (None, {"fields": ("instance_id", "reference_no", "workflow", "program_facility", "initiated_by")}),
        ("Status", {"fields": ("status", "priority", "current_step")}),
        ("Dates", {"fields": ("started_at", "due_date", "completed_at")}),
        ("Data", {"fields": ("request_data",), "classes": ("collapse",)}),
    )


@admin.register(WorkflowTask)
class WorkflowTaskAdmin(admin.ModelAdmin):
    list_display  = ["pk", "instance", "step", "assigned_to", "status", "due_date"]
    list_filter   = ["status"]
    search_fields = ["instance__reference_no", "assigned_to__full_name"]


@admin.register(WorkflowAuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display  = ["instance", "actor", "action", "from_status", "to_status", "logged_at"]
    list_filter   = ["action"]
    search_fields = ["instance__reference_no", "actor__full_name"]
    readonly_fields = ["logged_at"]
