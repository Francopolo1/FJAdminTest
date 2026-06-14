from rest_framework import serializers
from .models import (
    ComplianceRule, ViolationSeverityLevel,
    FineSchedule, FineTier,
    ChecklistItemComplianceRule, ComplianceViolation,
)


class ViolationSeverityLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ViolationSeverityLevel
        fields = ["violation_severity_level_id", "code", "name", "rank"]


class ComplianceRuleSerializer(serializers.ModelSerializer):
    violation_count = serializers.SerializerMethodField()

    class Meta:
        model  = ComplianceRule
        fields = [
            "compliance_rule_id", "code", "name", "description",
            "is_active", "created_date", "violation_count",
        ]

    def get_violation_count(self, obj):
        return ComplianceViolation.objects.filter(
            checklist_item_compliance_rule__compliance_rule=obj
        ).count()


class ComplianceRuleListSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ComplianceRule
        fields = ["compliance_rule_id", "code", "name", "is_active", "created_date"]


class FineTierSerializer(serializers.ModelSerializer):
    severity_name = serializers.CharField(
        source="violation_severity_level.name", read_only=True
    )
    severity_code = serializers.CharField(
        source="violation_severity_level.code", read_only=True
    )

    class Meta:
        model  = FineTier
        fields = [
            "fine_tier_id", "fine_schedule", "offense_number",
            "violation_severity_level", "severity_name", "severity_code",
            "fine_amount", "days_to_correct", "suspension_required",
        ]


class FineScheduleSerializer(serializers.ModelSerializer):
    rule_code    = serializers.CharField(source="compliance_rule.code", read_only=True)
    rule_name    = serializers.CharField(source="compliance_rule.name", read_only=True)
    is_active    = serializers.BooleanField(read_only=True)
    tiers        = FineTierSerializer(many=True, read_only=True)

    class Meta:
        model  = FineSchedule
        fields = [
            "fine_schedule_id", "compliance_rule", "rule_code", "rule_name",
            "schedule_name", "effective_date", "expiration_date",
            "is_active", "tiers",
        ]


class FineScheduleListSerializer(serializers.ModelSerializer):
    rule_code = serializers.CharField(source="compliance_rule.code", read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    tier_count = serializers.IntegerField(source="tiers.count", read_only=True)

    class Meta:
        model  = FineSchedule
        fields = [
            "fine_schedule_id", "compliance_rule", "rule_code",
            "schedule_name", "effective_date", "expiration_date",
            "is_active", "tier_count",
        ]


class ChecklistItemComplianceRuleSerializer(serializers.ModelSerializer):
    rule_code      = serializers.CharField(source="compliance_rule.code",       read_only=True)
    rule_name      = serializers.CharField(source="compliance_rule.name",       read_only=True)
    item_text      = serializers.CharField(source="checklist_item.item_text",   read_only=True, default=None)

    class Meta:
        model  = ChecklistItemComplianceRule
        fields = [
            "checklist_item_compliance_rule_id",
            "checklist_item", "item_text",
            "compliance_rule", "rule_code", "rule_name",
        ]


class ComplianceViolationSerializer(serializers.ModelSerializer):
    severity_name  = serializers.CharField(
        source="violation_severity_level.name", read_only=True
    )
    severity_code  = serializers.CharField(
        source="violation_severity_level.code", read_only=True
    )
    rule_code      = serializers.CharField(
        source="checklist_item_compliance_rule.compliance_rule.code",
        read_only=True,
    )
    rule_name      = serializers.CharField(
        source="checklist_item_compliance_rule.compliance_rule.name",
        read_only=True,
    )
    item_text      = serializers.SerializerMethodField()

    class Meta:
        model  = ComplianceViolation
        fields = [
            "compliance_violation_id",
            "checklist_item_compliance_rule",
            "rule_code", "rule_name",
            "item_text",
            "violation_date",
            "violation_severity_level", "severity_name", "severity_code",
            "violation_description",
            "detected_by",
            "checklist_response",
        ]

    def get_item_text(self, obj):
        try:
            return obj.checklist_item_compliance_rule.checklist_item.item_text
        except Exception:
            return None


class ComplianceViolationCreateSerializer(serializers.Serializer):
    """Validates input for creating a new violation."""
    checklist_item_compliance_rule_id = serializers.UUIDField()
    violation_date                    = serializers.DateField()
    violation_severity_level_id       = serializers.UUIDField()
    violation_description             = serializers.CharField(required=False, allow_blank=True)
    checklist_response_id             = serializers.UUIDField()


class ComplianceSummarySerializer(serializers.Serializer):
    """Shape for the /compliance/summary/ endpoint."""
    total_rules                = serializers.IntegerField()
    active_rules               = serializers.IntegerField()
    total_violations           = serializers.IntegerField()
    violations_last_30_days    = serializers.IntegerField()
    rules_with_violations      = serializers.IntegerField()
    top_violated_rules         = serializers.ListField(child=serializers.DictField())
    severity_breakdown         = serializers.ListField(child=serializers.DictField())
    active_fine_schedules      = serializers.IntegerField()
