"""
Compliance app models — all unmanaged (managed=False).

Tables mapped:
  compliance_rules                  → ComplianceRule
  violationseveritylevels           → ViolationSeverityLevel
  fine_schedules                    → FineSchedule
  fine_tiers                        → FineTier
  checklist_item_compliance_rules   → ChecklistItemComplianceRule
  compliance_violations             → ComplianceViolation
"""
import uuid
from django.db import models
from apps.core.db_fields import GUIDField



class ComplianceRule(models.Model):
    """dbo.compliance_rules"""
    compliance_rule_id = GUIDField(primary_key=True, default=uuid.uuid4)
    code               = models.CharField(max_length=25, unique=True)
    name               = models.CharField(max_length=200)
    description        = models.TextField(null=True, blank=True)
    is_active          = models.BooleanField(default=True)
    created_date       = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "compliance_rules"
        managed  = False
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.name}"


class ViolationSeverityLevel(models.Model):
    """dbo.violationseveritylevels"""
    violation_severity_level_id = GUIDField(primary_key=True, default=uuid.uuid4)
    code                        = models.CharField(max_length=10)
    name                        = models.CharField(max_length=50)
    rank                        = models.IntegerField()

    class Meta:
        db_table = "violationseveritylevels"
        managed  = False
        ordering = ["rank"]

    def __str__(self):
        return f"{self.code} ({self.name})"


class FineSchedule(models.Model):
    """dbo.fine_schedules"""
    fine_schedule_id  = GUIDField(primary_key=True, default=uuid.uuid4)
    compliance_rule   = models.ForeignKey(
        ComplianceRule,
        on_delete=models.PROTECT,
        db_column="compliance_rule_id",
        related_name="fine_schedules",
    )
    schedule_name     = models.CharField(max_length=100)
    effective_date    = models.DateField()
    expiration_date   = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "fine_schedules"
        managed  = False
        ordering = ["-effective_date"]

    def __str__(self):
        return f"{self.schedule_name} ({self.effective_date})"

    @property
    def is_active(self):
        from django.utils import timezone
        today = timezone.now().date()
        if self.effective_date > today:
            return False
        if self.expiration_date and self.expiration_date < today:
            return False
        return True


class FineTier(models.Model):
    """dbo.fine_tiers"""
    fine_tier_id              = GUIDField(primary_key=True, default=uuid.uuid4)
    fine_schedule             = models.ForeignKey(
        FineSchedule,
        on_delete=models.CASCADE,
        db_column="fine_schedule_id",
        related_name="tiers",
    )
    offense_number            = models.IntegerField()
    violation_severity_level  = models.ForeignKey(
        ViolationSeverityLevel,
        on_delete=models.PROTECT,
        db_column="violation_severity_level_id",
        related_name="fine_tiers",
    )
    fine_amount               = models.DecimalField(max_digits=12, decimal_places=2)
    days_to_correct           = models.IntegerField(null=True, blank=True)
    suspension_required       = models.BooleanField(default=False)
    compliance_window         = models.IntegerField(
        null=True, blank=True,
        help_text="Number of days in the compliance range for this tier.",
    )

    class Meta:
        db_table        = "fine_tiers"
        managed         = False
        ordering        = ["offense_number"]
        unique_together = [("fine_schedule", "offense_number", "violation_severity_level")]

    def __str__(self):
        return f"Offense #{self.offense_number} — ${self.fine_amount}"


class ChecklistItemComplianceRule(models.Model):
    """dbo.checklist_item_compliance_rules — links checklist items to rules."""
    checklist_item_compliance_rule_id = models.CharField(primary_key=True, max_length=36)
    # FK to checklist_item — avoid circular import by using string reference
    checklist_item    = models.ForeignKey(
        "checklists.ChecklistItem",
        on_delete=models.SET_NULL,
        null=True,
        db_column="checklist_item_id",
        related_name="compliance_rules",
    )
    compliance_rule   = models.ForeignKey(
        ComplianceRule,
        on_delete=models.PROTECT,
        db_column="compliance_rule_id",
        related_name="checklist_item_links",
    )

    class Meta:
        db_table = "checklist_item_compliance_rules"
        managed  = False

    def __str__(self):
        return f"Rule {self.compliance_rule_id} ← Item {self.checklist_item_id}"


class ComplianceViolation(models.Model):
    """dbo.compliance_violations"""
    compliance_violation_id           = GUIDField(primary_key=True, default=uuid.uuid4)
    checklist_item_compliance_rule    = models.ForeignKey(
        ChecklistItemComplianceRule,
        on_delete=models.PROTECT,
        db_column="checklist_item_compliance_rule_id",
        related_name="violations",
    )
    violation_date                    = models.DateField()
    violation_severity_level          = models.ForeignKey(
        ViolationSeverityLevel,
        on_delete=models.PROTECT,
        db_column="violation_severity_level_id",
        related_name="violations",
    )
    violation_description             = models.TextField(null=True, blank=True)
    detected_by                       = models.BigIntegerField(null=True, blank=True)
    # FK to checklist_response — string ref to avoid circular import
    checklist_response                = models.ForeignKey(
        "checklists.ChecklistResponse",
        on_delete=models.PROTECT,
        db_column="checklist_response_id",
        related_name="violations",
    )

    class Meta:
        db_table = "compliance_violations"
        managed  = False
        ordering = ["-violation_date"]

    def __str__(self):
        return f"Violation {self.compliance_violation_id} on {self.violation_date}"
