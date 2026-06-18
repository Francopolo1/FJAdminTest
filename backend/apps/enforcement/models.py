"""
Enforcement app models — managed=True (Django owns these tables).

Pipeline:
  ComplianceViolation
       ↓
  FineCase          – groups violations for one facility into a case
       ↓
  FineAssessment    – fine assessed against a specific violation
       ↓
  FineInvoice       – receivable/invoice aggregating assessed amounts
       ↓
  PaymentPlan       – optional installment schedule (one per invoice)
  PaymentPlanInstallment
       ↓
  FinePayment       – individual payment received
       ↓
  PaymentReceipt    – receipt issued for a cleared payment
"""
import uuid
from decimal import Decimal
from django.conf import settings
from django.db import models
from django.utils import timezone


# ── FineCase ──────────────────────────────────────────────────────────────────

class FineCase(models.Model):
    STATUS_CHOICES = [
        ("Open",        "Open"),
        ("PaymentPlan", "Payment Plan"),
        ("Paid",        "Paid"),
        ("Appealed",    "Appealed"),
        ("Waived",      "Waived"),
        ("Closed",      "Closed"),
    ]

    fine_case_id     = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    program_facility = models.ForeignKey(
        "core.ProgramFacility",
        on_delete=models.PROTECT,
        db_column="program_facility_id",
        related_name="fine_cases",
    )
    case_number      = models.CharField(max_length=40, unique=True, editable=False)
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Open")
    opened_date      = models.DateField(default=timezone.localdate)
    closed_date      = models.DateField(null=True, blank=True)
    notes            = models.TextField(null=True, blank=True)
    created_by       = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "enforcement_fine_cases"
        ordering = ["-opened_date", "-created_at"]

    def save(self, *args, **kwargs):
        if not self.case_number:
            year = timezone.localdate().year
            self.case_number = f"ENF-{year}-{str(self.fine_case_id).replace('-','')[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.case_number} ({self.status})"

    @property
    def total_assessed(self):
        return self.assessments.filter(
            status__in=["Issued", "Appealed"]
        ).aggregate(t=models.Sum("assessed_amount"))["t"] or Decimal("0")

    @property
    def total_balance_due(self):
        return sum(inv.balance_due for inv in self.invoices.all())


# ── FineAssessment ────────────────────────────────────────────────────────────

class FineAssessment(models.Model):
    STATUS_CHOICES = [
        ("Draft",     "Draft"),
        ("Issued",    "Issued"),
        ("Appealed",  "Appealed"),
        ("Waived",    "Waived"),
        ("Cancelled", "Cancelled"),
    ]

    fine_assessment_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case               = models.ForeignKey(
        FineCase,
        on_delete=models.PROTECT,
        related_name="assessments",
    )
    violation          = models.ForeignKey(
        "compliance.ComplianceViolation",
        on_delete=models.PROTECT,
        related_name="fine_assessments",
    )
    fine_tier          = models.ForeignKey(
        "compliance.FineTier",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="assessments",
        help_text="The schedule tier that determined the base amount.",
    )
    invoice            = models.ForeignKey(
        "enforcement.FineInvoice",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="line_items",
        help_text="Populated when the assessment is included on an invoice.",
    )
    assessed_amount    = models.DecimalField(max_digits=12, decimal_places=2)
    waived_amount      = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    status             = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Draft")
    notes              = models.TextField(null=True, blank=True)
    assessed_by        = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    assessed_at        = models.DateTimeField(null=True, blank=True)
    created_at         = models.DateTimeField(auto_now_add=True)
    updated_at         = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "enforcement_fine_assessments"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Assessment {self.fine_assessment_id} — ${self.assessed_amount} ({self.status})"

    @property
    def net_amount(self):
        return self.assessed_amount - self.waived_amount


# ── FineInvoice ───────────────────────────────────────────────────────────────

class FineInvoice(models.Model):
    STATUS_CHOICES = [
        ("Open",          "Open"),
        ("PartiallyPaid", "Partially Paid"),
        ("Paid",          "Paid"),
        ("Voided",        "Voided"),
        ("Waived",        "Waived"),
    ]

    fine_invoice_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case            = models.ForeignKey(
        FineCase,
        on_delete=models.PROTECT,
        related_name="invoices",
    )
    invoice_number  = models.CharField(max_length=40, unique=True, editable=False)
    invoice_date    = models.DateField(default=timezone.localdate)
    due_date        = models.DateField()
    total_amount    = models.DecimalField(max_digits=12, decimal_places=2)
    paid_amount     = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    waived_amount   = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Open")
    notes           = models.TextField(null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "enforcement_fine_invoices"
        ordering = ["-invoice_date"]

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = f"INV-{self.case.case_number}-{str(self.fine_invoice_id).replace('-','')[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.invoice_number} — ${self.total_amount} ({self.status})"

    @property
    def balance_due(self):
        return self.total_amount - self.paid_amount - self.waived_amount


# ── PaymentPlan ───────────────────────────────────────────────────────────────

class PaymentPlan(models.Model):
    FREQUENCY_CHOICES = [
        ("Monthly",    "Monthly"),
        ("Bimonthly",  "Bimonthly"),
        ("Quarterly",  "Quarterly"),
        ("Custom",     "Custom"),
    ]
    STATUS_CHOICES = [
        ("Active",    "Active"),
        ("Completed", "Completed"),
        ("Defaulted", "Defaulted"),
        ("Cancelled", "Cancelled"),
    ]

    payment_plan_id        = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice                = models.OneToOneField(
        FineInvoice,
        on_delete=models.PROTECT,
        related_name="payment_plan",
    )
    plan_date              = models.DateField(default=timezone.localdate)
    total_amount           = models.DecimalField(max_digits=12, decimal_places=2)
    number_of_installments = models.PositiveIntegerField()
    installment_amount     = models.DecimalField(max_digits=12, decimal_places=2)
    frequency              = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    first_due_date         = models.DateField()
    approved_by            = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    approved_date          = models.DateField(null=True, blank=True)
    status                 = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Active")
    notes                  = models.TextField(null=True, blank=True)
    created_at             = models.DateTimeField(auto_now_add=True)
    updated_at             = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "enforcement_payment_plans"
        ordering = ["-plan_date"]

    def __str__(self):
        return f"Plan {self.payment_plan_id} — {self.number_of_installments}×${self.installment_amount} ({self.status})"


# ── PaymentPlanInstallment ────────────────────────────────────────────────────

class PaymentPlanInstallment(models.Model):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Paid",    "Paid"),
        ("Overdue", "Overdue"),
        ("Waived",  "Waived"),
    ]

    installment_id     = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plan               = models.ForeignKey(
        PaymentPlan,
        on_delete=models.CASCADE,
        related_name="installments",
    )
    installment_number = models.PositiveIntegerField()
    due_date           = models.DateField()
    amount             = models.DecimalField(max_digits=12, decimal_places=2)
    status             = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")

    class Meta:
        db_table        = "enforcement_payment_plan_installments"
        ordering        = ["installment_number"]
        unique_together = [("plan", "installment_number")]

    def __str__(self):
        return f"#{self.installment_number} due {self.due_date} — ${self.amount} ({self.status})"


# ── FinePayment ───────────────────────────────────────────────────────────────

class FinePayment(models.Model):
    METHOD_CHOICES = [
        ("Check",      "Check"),
        ("ACH",        "ACH"),
        ("CreditCard", "Credit Card"),
        ("Cash",       "Cash"),
        ("Wire",       "Wire"),
        ("Other",      "Other"),
    ]
    STATUS_CHOICES = [
        ("Pending",  "Pending"),
        ("Cleared",  "Cleared"),
        ("Returned", "Returned"),
        ("Voided",   "Voided"),
    ]

    payment_id       = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice          = models.ForeignKey(
        FineInvoice,
        on_delete=models.PROTECT,
        related_name="payments",
    )
    installment      = models.ForeignKey(
        PaymentPlanInstallment,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="payments",
        help_text="Link to the installment this payment satisfies (if on a plan).",
    )
    payment_date     = models.DateField(default=timezone.localdate)
    amount           = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method   = models.CharField(max_length=20, choices=METHOD_CHOICES)
    reference_number = models.CharField(max_length=100, null=True, blank=True)
    received_by      = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    notes            = models.TextField(null=True, blank=True)
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "enforcement_fine_payments"
        ordering = ["-payment_date", "-created_at"]

    def __str__(self):
        return f"Payment {self.payment_id} — ${self.amount} via {self.payment_method} ({self.status})"


# ── PaymentReceipt ────────────────────────────────────────────────────────────

class PaymentReceipt(models.Model):
    receipt_id     = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment        = models.OneToOneField(
        FinePayment,
        on_delete=models.PROTECT,
        related_name="receipt",
    )
    receipt_number = models.CharField(max_length=40, unique=True, editable=False)
    issued_at      = models.DateTimeField(auto_now_add=True)
    issued_by      = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    notes          = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "enforcement_payment_receipts"
        ordering = ["-issued_at"]

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            self.receipt_number = (
                f"RCT-{self.payment.invoice.case.case_number}"
                f"-{str(self.payment.payment_id).replace('-','')[:8].upper()}"
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Receipt {self.receipt_number}"
