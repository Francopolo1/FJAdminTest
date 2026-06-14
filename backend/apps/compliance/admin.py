from django.contrib import admin
from django.utils.html import format_html
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
                "days_to_correct", "suspension_required"]
    ordering = ["offense_number"]


class FineScheduleInline(admin.TabularInline):
    model   = FineSchedule
    extra   = 0
    fields  = ["schedule_name", "effective_date", "expiration_date"]
    show_change_link = True


class ChecklistItemLinkInline(admin.TabularInline):
    model            = ChecklistItemComplianceRule
    extra            = 0
    fields           = ["checklist_item"]
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

    def violation_count_display(self, obj):
        count = ComplianceViolation.objects.filter(
            checklist_item_compliance_rule__compliance_rule=obj
        ).count()
        if count:
            return format_html('<span style="color:#E11D48;font-weight:700">{}</span>', count)
        return "0"
    violation_count_display.short_description = "Violations"


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
                        "expiration_date", "active_badge", "tier_count"]
    list_filter     = ["compliance_rule"]
    search_fields   = ["schedule_name", "compliance_rule__code", "compliance_rule__name"]
    ordering        = ["-effective_date"]
    readonly_fields = ["fine_schedule_id"]
    inlines         = [FineTierInline]

    def active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color:#059669;font-weight:600">● Active</span>')
        return format_html('<span style="color:#ADB5BD">● Inactive</span>')
    active_badge.short_description = "Active"

    def tier_count(self, obj):
        return obj.tiers.count()
    tier_count.short_description = "Tiers"


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

    def checklist_item_text(self, obj):
        if obj.checklist_item:
            return obj.checklist_item.item_text[:60]
        return "—"
    checklist_item_text.short_description = "Checklist Item"


# ── ComplianceViolation ───────────────────────────────────────────────────

@admin.register(ComplianceViolation)
class ComplianceViolationAdmin(admin.ModelAdmin):
    list_display    = ["compliance_violation_id", "rule_code", "violation_date",
                        "severity_badge", "violation_description_short"]
    list_filter     = ["violation_severity_level", "violation_date"]
    search_fields   = [
        "checklist_item_compliance_rule__compliance_rule__code",
        "checklist_item_compliance_rule__compliance_rule__name",
        "violation_description",
    ]
    ordering        = ["-violation_date"]
    readonly_fields = ["compliance_violation_id"]
    date_hierarchy  = "violation_date"

    def rule_code(self, obj):
        try:
            return obj.checklist_item_compliance_rule.compliance_rule.code
        except Exception:
            return "—"
    rule_code.short_description = "Rule"

    def severity_badge(self, obj):
        sev = obj.violation_severity_level
        colors = {"CRIT": "#E11D48", "HIGH": "#F97316", "MED": "#F59E0B", "LOW": "#6C757D"}
        color  = colors.get(sev.code.upper(), "#6C757D")
        return format_html(
            '<span style="color:{};font-weight:600">{}</span>', color, sev.name
        )
    severity_badge.short_description = "Severity"

    def violation_description_short(self, obj):
        if obj.violation_description:
            return obj.violation_description[:60]
        return "—"
    violation_description_short.short_description = "Description"
