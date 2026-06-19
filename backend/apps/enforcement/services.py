"""
Enforcement service layer — pure functions that implement the fine/payment pipeline.

Pipeline:
  assess_fine()         Violation → FineAssessment (Issued)
  create_invoice()      FineAssessments → FineInvoice
  setup_payment_plan()  FineInvoice → PaymentPlan + installments
  receive_payment()     FineInvoice → FinePayment, updates paid_amount / status
  generate_receipt()    FinePayment → PaymentReceipt
  close_case()          Validates balance is zero, sets case status=Closed
"""

from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from django.db import models, transaction
from django.utils import timezone

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


# ── assess_fine ───────────────────────────────────────────────────────────────

@transaction.atomic
def assess_fine(
    case: FineCase,
    violation,
    assessed_amount: Decimal,
    fine_tier=None,
    notes: str | None = None,
    assessed_by=None,
) -> FineAssessment:
    """Create an Issued FineAssessment on an existing FineCase."""
    assessment = FineAssessment.objects.create(
        case=case,
        violation=violation,
        fine_tier=fine_tier,
        assessed_amount=assessed_amount,
        status="Issued",
        notes=notes,
        assessed_by=assessed_by,
        assessed_at=timezone.now(),
    )
    return assessment


# ── create_invoice ────────────────────────────────────────────────────────────

@transaction.atomic
def create_invoice(
    case: FineCase,
    due_date: date,
    notes: str | None = None,
) -> FineInvoice:
    """
    Aggregate all Issued assessments for the case into a new FineInvoice.
    Links each assessment to the invoice.
    """
    assessments = list(
        case.assessments.filter(status="Issued", invoice__isnull=True).select_for_update()
    )
    if not assessments:
        raise ValueError("No Issued assessments without an invoice found for this case.")

    total = sum(a.net_amount for a in assessments)
    invoice = FineInvoice.objects.create(
        case=case,
        due_date=due_date,
        total_amount=total,
        notes=notes,
    )
    FineAssessment.objects.filter(
        fine_assessment_id__in=[a.fine_assessment_id for a in assessments]
    ).update(invoice=invoice)
    return invoice


# ── setup_payment_plan ────────────────────────────────────────────────────────

@transaction.atomic
def setup_payment_plan(
    invoice: FineInvoice,
    number_of_installments: int,
    frequency: str,
    first_due_date: date,
    approved_by=None,
    notes: str | None = None,
) -> PaymentPlan:
    """
    Create a PaymentPlan and generate installment schedule.
    Updates case status to PaymentPlan.
    """
    if hasattr(invoice, "payment_plan"):
        raise ValueError("This invoice already has a payment plan.")

    balance = invoice.balance_due
    installment_amount = (balance / number_of_installments).quantize(Decimal("0.01"))

    plan = PaymentPlan.objects.create(
        invoice=invoice,
        total_amount=balance,
        number_of_installments=number_of_installments,
        installment_amount=installment_amount,
        frequency=frequency,
        first_due_date=first_due_date,
        approved_by=approved_by,
        approved_date=date.today() if approved_by else None,
        notes=notes,
    )

    due = first_due_date
    delta = _frequency_delta(frequency)
    for i in range(1, number_of_installments + 1):
        PaymentPlanInstallment.objects.create(
            plan=plan,
            installment_number=i,
            due_date=due,
            amount=installment_amount,
        )
        due = due + delta

    invoice.case.status = "PaymentPlan"
    invoice.case.save(update_fields=["status", "updated_at"])

    return plan


def _frequency_delta(frequency: str) -> timedelta:
    match frequency:
        case "Monthly":
            return timedelta(days=30)
        case "Bimonthly":
            return timedelta(days=15)
        case "Quarterly":
            return timedelta(days=90)
        case _:
            return timedelta(days=30)


# ── receive_payment ───────────────────────────────────────────────────────────

@transaction.atomic
def receive_payment(
    invoice: FineInvoice,
    amount: Decimal,
    payment_method: str,
    payment_date: date | None = None,
    reference_number: str | None = None,
    received_by=None,
    installment: PaymentPlanInstallment | None = None,
    notes: str | None = None,
) -> FinePayment:
    """
    Record a FinePayment and update the invoice's paid_amount and status.
    Optionally marks a plan installment as Paid.
    """
    invoice_qs = FineInvoice.objects.select_for_update().filter(pk=invoice.pk)
    invoice = invoice_qs.get()

    payment = FinePayment.objects.create(
        invoice=invoice,
        installment=installment,
        payment_date=payment_date or date.today(),
        amount=amount,
        payment_method=payment_method,
        reference_number=reference_number,
        received_by=received_by,
        notes=notes,
        status="Cleared",
    )

    invoice.paid_amount = invoice.paid_amount + amount
    balance = invoice.balance_due
    if balance <= Decimal("0"):
        invoice.status = "Paid"
        # Mark plan complete if applicable
        try:
            plan = invoice.payment_plan
            plan.status = "Completed"
            plan.save(update_fields=["status", "updated_at"])
        except PaymentPlan.DoesNotExist:
            pass
    elif invoice.paid_amount > Decimal("0"):
        invoice.status = "PartiallyPaid"
    invoice.save(update_fields=["paid_amount", "status", "updated_at"])

    if installment:
        installment.status = "Paid"
        installment.save(update_fields=["status"])

    # Refresh case status
    _sync_case_status(invoice.case)

    return payment


def _sync_case_status(case: FineCase) -> None:
    """Bump case to Paid if all invoices are Paid."""
    open_invoices = case.invoices.exclude(status__in=["Paid", "Voided", "Waived"]).count()
    if open_invoices == 0 and case.invoices.filter(status="Paid").exists():
        case.status = "Paid"
        case.save(update_fields=["status", "updated_at"])


# ── generate_receipt ──────────────────────────────────────────────────────────

@transaction.atomic
def generate_receipt(
    payment: FinePayment,
    issued_by=None,
    notes: str | None = None,
) -> PaymentReceipt:
    """Issue a PaymentReceipt for a Cleared payment."""
    if payment.status != "Cleared":
        raise ValueError("Receipts can only be issued for Cleared payments.")
    if hasattr(payment, "receipt"):
        raise ValueError("A receipt has already been issued for this payment.")
    receipt = PaymentReceipt.objects.create(
        payment=payment,
        issued_by=issued_by,
        notes=notes,
    )
    return receipt


# ── close_case ────────────────────────────────────────────────────────────────

@transaction.atomic
def close_case(
    case: FineCase,
    notes: str | None = None,
) -> FineCase:
    """
    Close a FineCase.
    Raises ValueError if any invoice remains Open or PartiallyPaid.
    """
    open_invoices = case.invoices.filter(status__in=["Open", "PartiallyPaid"])
    if open_invoices.exists():
        raise ValueError(
            f"Cannot close case {case.case_number}: {open_invoices.count()} invoice(s) still have balances due."
        )
    case.status = "Closed"
    case.closed_date = date.today()
    if notes:
        case.notes = f"{case.notes}\n\n{notes}".strip() if case.notes else notes
    case.save(update_fields=["status", "closed_date", "notes", "updated_at"])
    return case


# ── file_appeal ───────────────────────────────────────────────────────────────

@transaction.atomic
def file_appeal(
    assessment: FineAssessment,
    grounds: str,
    appeal_date: date | None = None,
    hearing_date: date | None = None,
    filed_by=None,
) -> FineAppeal:
    """
    File a new appeal against a FineAssessment.
    Sets assessment status to Appealed and case status to Appealed.
    """
    appeal = FineAppeal.objects.create(
        assessment=assessment,
        grounds=grounds,
        appeal_date=appeal_date or date.today(),
        hearing_date=hearing_date,
        filed_by=filed_by,
        status="Pending",
    )
    assessment.status = "Appealed"
    assessment.save(update_fields=["status", "updated_at"])
    assessment.case.status = "Appealed"
    assessment.case.save(update_fields=["status", "updated_at"])
    return appeal


# ── decide_appeal ─────────────────────────────────────────────────────────────

@transaction.atomic
def decide_appeal(
    appeal: FineAppeal,
    status: str,
    decided_by=None,
    decision_notes: str | None = None,
    decision_date: date | None = None,
    adjusted_amount: Decimal | None = None,
) -> FineAppeal:
    """
    Record the outcome of an appeal.

    - Upheld:    assessment stays Issued, case re-opens.
    - Reduced:   assessment.assessed_amount set to adjusted_amount, case re-opens.
    - Dismissed: assessment set to Cancelled, case re-evaluates status.
    - Withdrawn: assessment reverts to Issued, case re-opens.
    """
    if status not in ("Upheld", "Reduced", "Dismissed", "Withdrawn"):
        raise ValueError(f"Invalid terminal appeal status: {status}")
    if status == "Reduced" and adjusted_amount is None:
        raise ValueError("adjusted_amount is required when status is Reduced.")

    appeal.status         = status
    appeal.decided_by     = decided_by
    appeal.decision_notes = decision_notes
    appeal.decision_date  = decision_date or date.today()
    appeal.adjusted_amount = adjusted_amount
    appeal.save(update_fields=[
        "status", "decided_by", "decision_notes", "decision_date",
        "adjusted_amount", "updated_at",
    ])

    assessment = FineAssessment.objects.select_for_update().get(pk=appeal.assessment_id)

    if status == "Upheld":
        assessment.status = "Issued"
        assessment.save(update_fields=["status", "updated_at"])
    elif status == "Reduced":
        assessment.assessed_amount = adjusted_amount
        assessment.status = "Issued"
        assessment.save(update_fields=["assessed_amount", "status", "updated_at"])
    elif status == "Dismissed":
        assessment.status = "Cancelled"
        assessment.save(update_fields=["status", "updated_at"])
    elif status == "Withdrawn":
        assessment.status = "Issued"
        assessment.save(update_fields=["status", "updated_at"])

    _sync_case_status_after_appeal(assessment.case)
    return appeal


def _sync_case_status_after_appeal(case: FineCase) -> None:
    """Re-evaluate case status after an appeal is decided."""
    if case.assessments.filter(status="Appealed").exists():
        return  # other pending appeals remain
    # Fall back to standard sync
    _sync_case_status(case)


# ── apply_waiver ──────────────────────────────────────────────────────────────

@transaction.atomic
def apply_waiver(
    waived_amount: Decimal,
    reason: str,
    assessment: FineAssessment | None = None,
    invoice: FineInvoice | None = None,
    authorized_by=None,
    authorization_date: date | None = None,
    notes: str | None = None,
) -> FineWaiver:
    """
    Record a waiver and apply it to the assessment or invoice waived_amount field.
    Exactly one of assessment / invoice must be provided.
    """
    if not assessment and not invoice:
        raise ValueError("Provide either assessment or invoice.")
    if assessment and invoice:
        raise ValueError("Provide only one of assessment or invoice, not both.")

    waiver = FineWaiver.objects.create(
        assessment=assessment,
        invoice=invoice,
        waived_amount=waived_amount,
        reason=reason,
        authorized_by=authorized_by,
        authorization_date=authorization_date or date.today(),
        notes=notes,
    )

    if assessment:
        assessment = FineAssessment.objects.select_for_update().get(pk=assessment.pk)
        assessment.waived_amount = assessment.waived_amount + waived_amount
        assessment.status = "Waived" if assessment.net_amount <= Decimal("0") else assessment.status
        assessment.save(update_fields=["waived_amount", "status", "updated_at"])

    if invoice:
        invoice = FineInvoice.objects.select_for_update().get(pk=invoice.pk)
        invoice.waived_amount = invoice.waived_amount + waived_amount
        if invoice.balance_due <= Decimal("0"):
            invoice.status = "Waived"
        invoice.save(update_fields=["waived_amount", "status", "updated_at"])
        _sync_case_status(invoice.case)

    return waiver


# ── run_compliance_check ──────────────────────────────────────────────────────

@transaction.atomic
def run_compliance_check(instance, actor=None) -> list:
    """
    Automated compliance check triggered when a workflow instance enters a
    ComplianceCheck step.

    For every ComplianceViolation linked to this instance's checklist responses:
      1. Group violations by checklist_item_compliance_rule (one rule per group).
      2. Use the latest violation_date in the group as the reference date.
      3. Read compliance_window (days) from the rule's active FineTier schedule.
      4. Count *all* violations for that rule at this facility within
         [violation_date − compliance_window, violation_date] to get offense_number.
      5. Look up the FineTier whose offense_number matches (clamped to the
         highest tier if the count exceeds the schedule's maximum).
      6. Create a FineAssessment (with checklist item, rule, and violation
         dates in the notes field) under a FineCase keyed to instance.reference_no.

    Returns a list of created FineAssessment objects (empty if no violations).
    """
    from apps.compliance.models import ComplianceViolation, FineTier, FineSchedule

    violations = list(
        ComplianceViolation.objects.filter(
            checklist_response__run__instance=instance,
        ).select_related(
            "checklist_item_compliance_rule__checklist_item",
            "checklist_item_compliance_rule__compliance_rule",
            "violation_severity_level",
        ).order_by("violation_date")
    )

    if not violations:
        return []

    # Group by checklist_item_compliance_rule_id
    groups = defaultdict(list)
    for v in violations:
        groups[v.checklist_item_compliance_rule_id].append(v)

    case = _get_or_create_fine_case(instance, actor)
    assessments = []

    for rule_link_id, group_violations in groups.items():
        rule_link       = group_violations[0].checklist_item_compliance_rule
        compliance_rule = rule_link.compliance_rule
        checklist_item  = rule_link.checklist_item
        severity        = group_violations[0].violation_severity_level

        # Use the latest violation date in this group as the reference date
        current_date = max(v.violation_date for v in group_violations)

        # Find the active fine schedule for this compliance rule
        active_schedule = (
            FineSchedule.objects
            .filter(
                compliance_rule=compliance_rule,
                effective_date__lte=current_date,
            )
            .filter(
                models.Q(expiration_date__isnull=True) |
                models.Q(expiration_date__gte=current_date)
            )
            .order_by("-effective_date")
            .first()
        )
        if not active_schedule:
            continue

        # Retrieve all tiers for this schedule + severity, sorted by offense_number
        tiers = list(
            FineTier.objects.filter(
                fine_schedule=active_schedule,
                violation_severity_level=severity,
            ).order_by("offense_number")
        )
        if not tiers:
            continue

        # Derive compliance_window from the first tier (tier 1 defines the window)
        compliance_window = tiers[0].compliance_window or 365
        lookback_date     = current_date - timedelta(days=compliance_window)

        # Count all violations for this rule+item at this facility in the window
        offense_count = ComplianceViolation.objects.filter(
            checklist_item_compliance_rule_id=rule_link_id,
            checklist_response__run__instance__program_facility=instance.program_facility,
            violation_date__range=(lookback_date, current_date),
        ).count()

        # Match offense_count to a tier; clamp to the highest tier if exceeded
        tier = next(
            (t for t in tiers if t.offense_number == offense_count),
            tiers[-1],
        )

        # Build notes: checklist item, rule, violation date(s)
        violation_dates = sorted({v.violation_date.isoformat() for v in group_violations})
        item_text  = checklist_item.item_text if checklist_item else "N/A"
        rule_label = f"{compliance_rule.code} – {compliance_rule.name}" if compliance_rule else "N/A"
        notes = (
            f"Checklist Item: {item_text}\n"
            f"Compliance Rule: {rule_label}\n"
            f"Violation Date(s): {', '.join(violation_dates)}\n"
            f"Offense #{offense_count} within {compliance_window}-day window "
            f"({lookback_date} to {current_date})"
        )

        assessment = assess_fine(
            case=case,
            violation=group_violations[-1],   # most recent violation as the FK
            assessed_amount=tier.fine_amount,
            fine_tier=tier,
            notes=notes,
            assessed_by=actor,
        )
        assessments.append(assessment)

    return assessments


def _get_or_create_fine_case(instance, actor=None) -> FineCase:
    """Get or create a FineCase for a workflow instance, keyed by reference_no."""
    case, _ = FineCase.objects.get_or_create(
        case_number=instance.reference_no,
        defaults={
            "program_facility": instance.program_facility,
            "status": "Open",
            "opened_date": timezone.localdate(),
            "created_by": actor,
        },
    )
    return case
