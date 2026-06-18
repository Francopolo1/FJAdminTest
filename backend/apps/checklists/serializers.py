
"""
Checklist serializers.

Hierarchy
──────────
  ChecklistTemplateSerializer
    └─ ChecklistItemSerializer  (nested, writable)

  ChecklistRunSerializer
    └─ ChecklistResponseSerializer  (nested, read-only)

  SubmitResponseSerializer    – validates a batch of item answers
  BulkCreateItemSerializer    – creates multiple items in one request
"""

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import ChecklistTemplate, ChecklistItem, ChecklistRun, ChecklistResponse


# ── ChecklistItem ─────────────────────────────────────────────────────────────

class ChecklistItemSerializer(serializers.ModelSerializer):
    """Full item serializer — used for nested writes inside a template."""
    example_file_url = serializers.SerializerMethodField()

    class Meta:
        model  = ChecklistItem
        fields = [
            "item_id", "template", "item_text", "help_text",
            "response_type", "category", "display_order", "is_required",
            "options", "default_value", "example_url", "example_file", "example_file_url",
            "created_at",
        ]
        read_only_fields = ["item_id", "example_file_url", "created_at"]

    def get_example_file_url(self, obj):
        if not obj.example_file:
            return None
        request = self.context.get("request")
        url = obj.example_file.url
        return request.build_absolute_uri(url) if request else url

    def validate(self, data):
        # Build a temporary model instance and run full_clean to trigger
        # the model-level validation (options required for choice types, etc.)
        instance = self.instance or ChecklistItem()
        for attr, value in data.items():
            setattr(instance, attr, value)
        try:
            instance.clean()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict if hasattr(exc, "message_dict") else exc.messages)
        return data


class ChecklistItemMinimalSerializer(serializers.ModelSerializer):
    """Lightweight serializer used in list views."""

    class Meta:
        model  = ChecklistItem
        fields = [
            "item_id", "item_text", "response_type",
            "category", "display_order", "is_required", "options",
        ]


# ── ChecklistTemplate ─────────────────────────────────────────────────────────

class ChecklistTemplateListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for template list views."""
    step_name  = serializers.CharField(source="step.step_name", read_only=True, default=None)
    item_count = serializers.IntegerField(read_only=True)

    class Meta:
        model  = ChecklistTemplate
        fields = [
            "template_id", "workflow", "step", "step_name",
            "title", "is_required", "blocks_advance",
            "display_order", "created_at", "item_count",
        ]


class ChecklistTemplateSerializer(serializers.ModelSerializer):
    """
    Full template serializer — supports nested item creation/update.

    On create: pass items[] to create items inline.
    On update: items[] replaces all existing items (full replace semantics).
               Omit items[] to leave items unchanged.
    """
    step_name  = serializers.CharField(source="step.step_name", read_only=True, default=None)
    item_count = serializers.SerializerMethodField()
    items      = ChecklistItemSerializer(many=True, required=False)

    class Meta:
        model  = ChecklistTemplate
        fields = [
            "template_id", "workflow", "step", "step_name",
            "title", "description",
            "is_required", "blocks_advance", "display_order",
            "created_at", "updated_at",
            "item_count", "items",
        ]
        read_only_fields = ["template_id", "created_at", "updated_at"]

    def get_item_count(self, obj):
        # Use cached annotation if available, otherwise hit DB
        return getattr(obj, "_item_count", obj.items.count())

    def validate(self, data):
        # Model-level clean (blocks_advance requires is_required)
        instance = self.instance or ChecklistTemplate()
        for attr, value in data.items():
            if attr != "items":
                setattr(instance, attr, value)
        try:
            instance.clean()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)
        return data

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        template   = ChecklistTemplate.objects.create(**validated_data)
        for item_data in items_data:
            ChecklistItem.objects.create(template=template, **item_data)
        return template

    def update(self, instance, validated_data):
        items_data = validated_data.pop("items", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if items_data is not None:
            # Full replace — delete existing and recreate
            instance.items.all().delete()
            for item_data in items_data:
                ChecklistItem.objects.create(template=instance, **item_data)

        return instance


# ── ChecklistResponse ─────────────────────────────────────────────────────────

class ChecklistResponseSerializer(serializers.ModelSerializer):
    """Read-only; responses are written via the respond action."""
    item_text         = serializers.CharField(source="item.item_text",          read_only=True)
    response_type     = serializers.CharField(source="item.response_type",       read_only=True)
    is_required       = serializers.BooleanField(source="item.is_required",      read_only=True)
    responded_by_name = serializers.CharField(source="responded_by.full_name",   read_only=True)

    class Meta:
        model  = ChecklistResponse
        fields = [
            "response_id", "run", "item", "item_text",
            "response_type", "is_required",
            "responded_by", "responded_by_name",
            "response_value", "notes", "box_folder_url", "responded_at",
        ]
        read_only_fields = fields  # entirely read-only; writes go via SubmitResponseSerializer


# ── ChecklistRun ──────────────────────────────────────────────────────────────

class ChecklistRunListSerializer(serializers.ModelSerializer):
    """Lightweight run serializer for list views."""
    template_title  = serializers.CharField(source="template.title",            read_only=True)
    blocks_advance  = serializers.BooleanField(source="template.blocks_advance", read_only=True)
    workflow_name   = serializers.CharField(source="instance.workflow.name",     read_only=True)
    reference_no    = serializers.CharField(source="instance.reference_no",      read_only=True)
    program_title   = serializers.CharField(
        source="instance.program_facility.program_facility_type.program.title", read_only=True, default=None,
    )
    activity        = serializers.CharField(
        source="instance.workflow.program_facility_type_activity.description", read_only=True, default=None,
    )
    facility_name   = serializers.CharField(
        source="instance.program_facility.facility.name", read_only=True, default=None,
    )

    class Meta:
        model  = ChecklistRun
        fields = [
            "run_id", "instance", "reference_no", "workflow_name",
            "task", "template", "template_title", "blocks_advance",
            "status",
            "total_items", "total_required",
            "answered_items", "answered_required",
            "completion_pct", "required_completion_pct",
            "started_at", "completed_at", "created_at",
            "program_title", "activity", "facility_name",
        ]


class ChecklistRunSerializer(serializers.ModelSerializer):
    """Full run serializer — includes all responses."""
    template_title        = serializers.CharField(source="template.title",            read_only=True)
    template_description  = serializers.CharField(source="template.description",       read_only=True)
    blocks_advance        = serializers.BooleanField(source="template.blocks_advance", read_only=True)
    workflow_name         = serializers.CharField(source="instance.workflow.name",     read_only=True)
    reference_no          = serializers.CharField(source="instance.reference_no",      read_only=True)
    completion_pct        = serializers.FloatField(read_only=True)
    required_completion_pct = serializers.FloatField(read_only=True)
    is_blocking           = serializers.BooleanField(read_only=True)
    responses             = ChecklistResponseSerializer(many=True, read_only=True)
    facility_name         = serializers.CharField(
        source="instance.program_facility.facility.name", read_only=True, default=None,
    )
    facility_address      = serializers.CharField(
        source="instance.program_facility.facility.location.addressline1", read_only=True, default=None,
    )
    facility_city_state_zip = serializers.CharField(
        source="instance.program_facility.facility.location.citystatezip", read_only=True, default=None,
    )
    facility_phone        = serializers.CharField(
        source="instance.program_facility.facility_phone", read_only=True, default=None,
    )
    license_number        = serializers.CharField(
        source="instance.program_facility.license_number", read_only=True, default=None,
    )
    license_expire_date   = serializers.DateTimeField(
        source="instance.program_facility.license_expire_date", read_only=True, default=None,
    )
    tracking_id           = serializers.CharField(
        source="instance.program_facility.tracking_id", read_only=True, default=None,
    )

    class Meta:
        model  = ChecklistRun
        fields = [
            "run_id", "instance", "reference_no", "workflow_name",
            "task", "template", "template_title", "template_description",
            "blocks_advance", "is_blocking",
            "status",
            "total_items", "total_required",
            "answered_items", "answered_required",
            "completion_pct", "required_completion_pct",
            "started_at", "completed_at", "created_at",
            "facility_name", "facility_address", "facility_city_state_zip",
            "facility_phone", "license_number", "license_expire_date", "tracking_id",
            "responses",
        ]
        read_only_fields = [
            "started_at", "completed_at", "created_at",
        ]


# ── Progress ──────────────────────────────────────────────────────────────────

class ChecklistItemComplianceRuleRefSerializer(serializers.Serializer):
    """A compliance rule that can be flagged against a checklist item."""
    checklist_item_compliance_rule_id = serializers.CharField()
    rule_code                         = serializers.CharField()
    rule_name                         = serializers.CharField()


class ChecklistProgressItemSerializer(serializers.Serializer):
    """One row in the /progress/ endpoint breakdown."""
    item_id          = serializers.CharField()
    item_text        = serializers.CharField()
    help_text        = serializers.CharField(allow_null=True)
    response_type    = serializers.CharField()
    category         = serializers.CharField(allow_null=True)
    is_required      = serializers.BooleanField()
    options          = serializers.ListField(child=serializers.CharField(), allow_null=True)
    default_value    = serializers.CharField(allow_null=True)
    example_url      = serializers.CharField(allow_null=True)
    example_file_url = serializers.CharField(allow_null=True)
    answered         = serializers.BooleanField()
    response_id      = serializers.CharField(allow_null=True)
    response_value   = serializers.CharField(allow_null=True)
    notes            = serializers.CharField(allow_null=True)
    box_folder_url   = serializers.CharField(allow_null=True)
    responded_by     = serializers.CharField(allow_null=True)
    responded_at     = serializers.DateTimeField(allow_null=True)
    compliance_rules = ChecklistItemComplianceRuleRefSerializer(many=True)


class ChecklistProgressSerializer(serializers.Serializer):
    """Full response shape for GET /runs/{id}/progress/"""
    run_id                  = serializers.CharField()
    status                  = serializers.CharField()
    blocks_advance          = serializers.BooleanField()
    completion_pct          = serializers.FloatField()
    required_completion_pct = serializers.FloatField()
    total_items             = serializers.IntegerField()
    answered_items          = serializers.IntegerField()
    total_required          = serializers.IntegerField()
    answered_required       = serializers.IntegerField()
    items                   = ChecklistProgressItemSerializer(many=True)
    violations              = serializers.SerializerMethodField()

    def get_violations(self, obj):
        from apps.compliance.serializers import ComplianceViolationSerializer
        return ComplianceViolationSerializer(obj["violations"], many=True).data


# ── Submit / batch respond ─────────────────────────────────────────────────────

class SubmitResponseSerializer(serializers.Serializer):
    """
    Validate a single item answer.  Used in a many=True list when the
    client POSTs an array to /runs/{id}/respond/.
    """
    item           = serializers.CharField(
        help_text="PK of the ChecklistItem being answered."
    )
    response_value = serializers.CharField(
        allow_blank=True, allow_null=True, required=False,
        help_text="The answer.  Validated against the item's response_type.",
    )
    notes          = serializers.CharField(
        allow_blank=True, allow_null=True, required=False,
        help_text="Optional free-text annotation.",
    )
    box_folder_url = serializers.CharField(
        allow_blank=True, allow_null=True, required=False,
        help_text="Link to the Box.com documents folder for this response.",
    )


# ── Bulk item creation ─────────────────────────────────────────────────────────

class BulkCreateItemSerializer(serializers.Serializer):
    """POST /templates/{id}/add-items/ — create multiple items at once."""
    items = ChecklistItemSerializer(many=True)

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Provide at least one item.")
        return value