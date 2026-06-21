from decimal import Decimal

from rest_framework import serializers

from .models import (
    FineCase,
    FineAssessment,
    FineInvoice,
    PaymentPlan,
    PaymentPlanInstallment,
    FinePayment,
    PaymentReceipt,
    FineAppeal,
    FineWaiver,
)


# ── PaymentReceipt ────────────────────────────────────────────────────────────

class PaymentReceiptSerializer(serializers.ModelSerializer):
    issued_by_name = serializers.CharField(source="issued_by.get_full_name", read_only=True, default=None)

    class Meta:
        model  = PaymentReceipt
        fields = [
            "receipt_id", "receipt_number", "issued_at",
            "issued_by", "issued_by_name", "notes",
        ]
        read_only_fields = fields


# ── FinePayment ───────────────────────────────────────────────────────────────

class FinePaymentSerializer(serializers.ModelSerializer):
    received_by_name = serializers.CharField(source="received_by.get_full_name", read_only=True, default=None)
    receipt          = PaymentReceiptSerializer(read_only=True)

    class Meta:
        model  = FinePayment
        fields = [
            "payment_id", "invoice", "installment",
            "payment_date", "amount", "payment_method",
            "reference_number", "received_by", "received_by_name",
            "notes", "status", "receipt",
            "created_at", "updated_at",
        ]
        read_only_fields = ["payment_id", "receipt", "created_at", "updated_at"]


class ReceivePaymentInputSerializer(serializers.Serializer):
    amount           = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))
    payment_method   = serializers.ChoiceField(choices=FinePayment.METHOD_CHOICES)
    payment_date     = serializers.DateField(required=False, allow_null=True)
    reference_number = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    installment_id   = serializers.UUIDField(required=False, allow_null=True)
    notes            = serializers.CharField(required=False, allow_blank=True, allow_null=True)


# ── PaymentPlanInstallment ────────────────────────────────────────────────────

class PaymentPlanInstallmentSerializer(serializers.ModelSerializer):
    class Meta:
        model  = PaymentPlanInstallment
        fields = [
            "installment_id", "plan", "installment_number",
            "due_date", "amount", "status",
        ]
        read_only_fields = fields


# ── PaymentPlan ───────────────────────────────────────────────────────────────

class PaymentPlanSerializer(serializers.ModelSerializer):
    approved_by_name = serializers.CharField(source="approved_by.get_full_name", read_only=True, default=None)
    installments     = PaymentPlanInstallmentSerializer(many=True, read_only=True)

    class Meta:
        model  = PaymentPlan
        fields = [
            "payment_plan_id", "invoice",
            "plan_date", "total_amount",
            "number_of_installments", "installment_amount",
            "frequency", "first_due_date",
            "approved_by", "approved_by_name", "approved_date",
            "status", "notes",
            "installments",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "payment_plan_id", "installments", "created_at", "updated_at",
        ]


class SetupPaymentPlanInputSerializer(serializers.Serializer):
    number_of_installments = serializers.IntegerField(min_value=1)
    frequency              = serializers.ChoiceField(choices=PaymentPlan.FREQUENCY_CHOICES)
    first_due_date         = serializers.DateField()
    notes                  = serializers.CharField(required=False, allow_blank=True, allow_null=True)


# ── FineInvoice ───────────────────────────────────────────────────────────────

class FineInvoiceSerializer(serializers.ModelSerializer):
    balance_due  = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    payment_plan = PaymentPlanSerializer(read_only=True)
    payments     = FinePaymentSerializer(many=True, read_only=True)

    class Meta:
        model  = FineInvoice
        fields = [
            "fine_invoice_id", "case", "invoice_number",
            "invoice_date", "due_date",
            "total_amount", "paid_amount", "waived_amount", "balance_due",
            "status", "notes",
            "payment_plan", "payments",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "fine_invoice_id", "invoice_number", "invoice_date",
            "paid_amount", "balance_due", "payment_plan", "payments",
            "created_at", "updated_at",
        ]


class CreateInvoiceInputSerializer(serializers.Serializer):
    due_date = serializers.DateField()
    notes    = serializers.CharField(required=False, allow_blank=True, allow_null=True)


# ── FineAssessment ────────────────────────────────────────────────────────────

class FineAssessmentSerializer(serializers.ModelSerializer):
    assessed_by_name = serializers.CharField(source="assessed_by.get_full_name", read_only=True, default=None)
    net_amount       = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model  = FineAssessment
        fields = [
            "fine_assessment_id", "case", "violation",
            "fine_tier", "invoice",
            "assessed_amount", "waived_amount", "net_amount",
            "status", "notes",
            "assessed_by", "assessed_by_name", "assessed_at",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "fine_assessment_id", "net_amount",
            "assessed_by_name", "assessed_at",
            "created_at", "updated_at",
        ]


class AssessFineInputSerializer(serializers.Serializer):
    violation_id     = serializers.UUIDField()
    assessed_amount  = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))
    fine_tier_id     = serializers.UUIDField(required=False, allow_null=True)
    notes            = serializers.CharField(required=False, allow_blank=True, allow_null=True)


# ── FineCase ──────────────────────────────────────────────────────────────────

class FineCaseListSerializer(serializers.ModelSerializer):
    facility_name    = serializers.CharField(
        source="program_facility.facility.name", read_only=True, default=None
    )
    created_by_name  = serializers.CharField(source="created_by.get_full_name", read_only=True, default=None)
    total_assessed   = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_balance_due = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model  = FineCase
        fields = [
            "fine_case_id", "case_number", "status",
            "program_facility", "facility_name",
            "opened_date", "closed_date",
            "notes",
            "created_by", "created_by_name",
            "total_assessed", "total_balance_due",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "fine_case_id", "case_number",
            "facility_name", "created_by_name",
            "total_assessed", "total_balance_due",
            "created_at", "updated_at",
        ]


class FineCaseDetailSerializer(FineCaseListSerializer):
    assessments = FineAssessmentSerializer(many=True, read_only=True)
    invoices    = FineInvoiceSerializer(many=True, read_only=True)

    class Meta(FineCaseListSerializer.Meta):
        fields = FineCaseListSerializer.Meta.fields + ["assessments", "invoices"]


# ── FineAppeal ────────────────────────────────────────────────────────────────

class FineAppealSerializer(serializers.ModelSerializer):
    filed_by_name   = serializers.CharField(source="filed_by.get_full_name",   read_only=True, default=None)
    decided_by_name = serializers.CharField(source="decided_by.get_full_name", read_only=True, default=None)

    class Meta:
        model  = FineAppeal
        fields = [
            "appeal_id", "assessment",
            "filed_by", "filed_by_name", "appeal_date", "grounds",
            "status", "hearing_date",
            "decision_notes", "decision_date",
            "decided_by", "decided_by_name", "adjusted_amount",
            "created_at", "updated_at",
        ]
        read_only_fields = ["appeal_id", "filed_by_name", "decided_by_name", "created_at", "updated_at"]

    def validate_grounds(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Grounds for appeal cannot be empty.")
        if len(value) < 10:
            raise serializers.ValidationError("Grounds for appeal must be at least 10 characters.")
        if len(value) > 2000:
            raise serializers.ValidationError("Grounds for appeal cannot exceed 2000 characters.")
        return value.strip()


class AppealDecisionInputSerializer(serializers.Serializer):
    status          = serializers.ChoiceField(choices=FineAppeal.STATUS_CHOICES)
    decision_notes  = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    decision_date   = serializers.DateField(required=False, allow_null=True)
    adjusted_amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)


# ── FineWaiver ────────────────────────────────────────────────────────────────

class FineWaiverSerializer(serializers.ModelSerializer):
    authorized_by_name = serializers.CharField(source="authorized_by.get_full_name", read_only=True, default=None)

    class Meta:
        model  = FineWaiver
        fields = [
            "waiver_id", "assessment", "invoice",
            "waived_amount", "reason",
            "authorized_by", "authorized_by_name", "authorization_date",
            "notes", "created_at",
        ]
        read_only_fields = ["waiver_id", "authorized_by_name", "created_at"]

    def validate(self, data):
        if not data.get("assessment") and not data.get("invoice"):
            raise serializers.ValidationError("Provide either assessment or invoice.")
        if data.get("assessment") and data.get("invoice"):
            raise serializers.ValidationError("Provide only one of assessment or invoice, not both.")
        return data
