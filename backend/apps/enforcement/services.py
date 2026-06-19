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

from datetime import date, timedelta
from decimal import Decimal

from django.db import transaction
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
