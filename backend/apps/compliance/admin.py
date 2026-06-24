from django.contrib import admin
from .models import (
    ComplianceRule, ViolationSeverityLevel,
    FineSchedule, FineTier,
    ChecklistItemComplianceRule, ComplianceViolation,
)


# ── Inlines ───────────────────────────────────────────────────────────────

class FineTierInline(admin.TabularInline):
    model   = FineTier
    extra   = 0
    fields  = ["offense_number", "violation_severity_level", "fine_amount",
                "days_to_correct", "suspension_required", "compliance_window"]
    exclude = ["fine_tier_id"]
    ordering = ["offense_number"]


class FineScheduleInline(admin.TabularInline):
    model   = FineSchedule
    extra   = 0
    fields  = ["schedule_name", "effective_date", "expiration_date"]
    exclude = ["fine_schedule_id"]
    show_change_link = True


class ChecklistItemLinkInline(admin.TabularInline):
    model            = ChecklistItemComplianceRule
    extra            = 0
    fields           = ["checklist_item"]
    exclude          = ["checklist_item_compliance_rule_id"]
    show_change_link = True
    verbose_name      = "Linked checklist item"
    verbose_name_plural = "Linked checklist items"


# ── ComplianceRule ────────────────────────────────────────────────────────

@admin.register(ComplianceRule)
class ComplianceRuleAdmin(admin.ModelAdmin):
    list_display    = ["code", "name", "is_active", "violation_count_display", "created_date"]
    list_filter     = ["is_active"]
    search_fields   = ["code", "name", "description"]
    ordering        = ["code"]
    readonly_fields = ["compliance_rule_id", "created_date"]
    inlines         = [FineScheduleInline, ChecklistItemLinkInline]
    fieldsets       = (
        (None,         {"fields": ("compliance_rule_id", "code", "name", "description")}),
        ("Status",     {"fields": ("is_active", "created_date")}),
    )

    @admin.display(description="Violations")
    def violation_count_display(self, obj):
        try:
            count = ComplianceViolation.objects.filter(
                checklist_item_compliance_rule__compliance_rule=obj
            ).count()
            return str(count) if count else "0"
        except Exception:
            return "—"


# ── ViolationSeverityLevel ────────────────────────────────────────────────

@admin.register(ViolationSeverityLevel)
class ViolationSeverityLevelAdmin(admin.ModelAdmin):
    list_display    = ["rank", "code", "name"]
    ordering        = ["rank"]
    readonly_fields = ["violation_severity_level_id"]


# ── FineSchedule ──────────────────────────────────────────────────────────

@admin.register(FineSchedule)
class FineScheduleAdmin(admin.ModelAdmin):
    list_display    = ["schedule_name", "compliance_rule", "effective_date",
                        "expiration_date", "is_active_display", "tier_count"]
    search_fields   = ["schedule_name", "compliance_rule__code", "compliance_rule__name"]
    ordering        = ["-effective_date"]
    readonly_fields = ["fine_schedule_id"]
    inlines         = [FineTierInline]

    @admin.display(description="Active", boolean=True)
    def is_active_display(self, obj):
        try:
            return obj.is_active
        except Exception:
            return False

    @admin.display(description="Tiers")
    def tier_count(self, obj):
        try:
            return obj.tiers.count()
        except Exception:
            return "—"


# ── FineTier ──────────────────────────────────────────────────────────────

@admin.register(FineTier)
class FineTierAdmin(admin.ModelAdmin):
    list_display    = ["fine_schedule", "offense_number", "violation_severity_level",
                        "fine_amount", "days_to_correct", "suspension_required"]
    list_filter     = ["suspension_required", "violation_severity_level"]
    ordering        = ["fine_schedule", "offense_number"]
    readonly_fields = ["fine_tier_id"]


# ── ChecklistItemComplianceRule ───────────────────────────────────────────

@admin.register(ChecklistItemComplianceRule)
class ChecklistItemComplianceRuleAdmin(admin.ModelAdmin):
    list_display    = ["compliance_rule", "checklist_item_text"]
    list_filter     = ["compliance_rule"]
    search_fields   = ["compliance_rule__code", "compliance_rule__name"]
    readonly_fields = ["checklist_item_compliance_rule_id"]

    @admin.display(description="Checklist Item")
    def checklist_item_text(self, obj):
        try:
            if obj.checklist_item:
                return obj.checklist_item.item_text[:60]
        except Exception:
            pass
        return "—"


# ── ComplianceViolation ───────────────────────────────────────────────────

@admin.register(ComplianceViolation)
class ComplianceViolationAdmin(admin.ModelAdmin):
    list_display    = ["compliance_violation_id", "rule_code", "violation_date",
                        "severity_name", "violation_description_short"]
    list_filter     = ["violation_severity_level", "violation_date"]
    search_fields   = [
        "checklist_item_compliance_rule__compliance_rule__code",
        "checklist_item_compliance_rule__compliance_rule__name",
        "violation_description",
    ]
    ordering        = ["-violation_date"]
    readonly_fields = ["compliance_violation_id"]
    date_hierarchy  = "violation_date"

    @admin.display(description="Rule")
    def rule_code(self, obj):
        try:
            return obj.checklist_item_compliance_rule.compliance_rule.code
        except Exception:
            return "—"

    @admin.display(description="Severity")
    def severity_name(self, obj):
        try:
            return obj.violation_severity_level.name
        except Exception:
            return "—"

    @admin.display(description="Description")
    def violation_description_short(self, obj):
        try:
            if obj.violation_description:
                return obj.violation_description[:60]
        except Exception:
            pass
        return "—"
