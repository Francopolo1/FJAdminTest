from django.contrib import admin

from .models import (
    FineCase,
    FineAssessment,
    FineInvoice,
    PaymentPlan,
    PaymentPlanInstallment,
    FinePayment,
    PaymentReceipt,
)


class FineAssessmentInline(admin.TabularInline):
    model  = FineAssessment
    extra  = 0
    fields = ["violation", "fine_tier", "assessed_amount", "waived_amount", "status", "assessed_by"]
    readonly_fields = ["assessed_by"]


class FineInvoiceInline(admin.TabularInline):
    model  = FineInvoice
    extra  = 0
    fields = ["invoice_number", "due_date", "total_amount", "paid_amount", "waived_amount", "status"]
    readonly_fields = ["invoice_number", "total_amount", "paid_amount"]
    show_change_link = True


@admin.register(FineCase)
class FineCaseAdmin(admin.ModelAdmin):
    list_display  = ["case_number", "program_facility", "status", "opened_date", "closed_date", "created_by"]
    list_filter   = ["status", "opened_date"]
    search_fields = ["case_number", "program_facility__facility__name"]
    readonly_fields = ["fine_case_id", "case_number", "created_at", "updated_at"]
    inlines = [FineAssessmentInline, FineInvoiceInline]


class PaymentPlanInstallmentInline(admin.TabularInline):
    model  = PaymentPlanInstallment
    extra  = 0
    fields = ["installment_number", "due_date", "amount", "status"]
    readonly_fields = ["installment_number"]


@admin.register(PaymentPlan)
class PaymentPlanAdmin(admin.ModelAdmin):
    list_display   = ["payment_plan_id", "invoice", "status", "frequency", "number_of_installments"]
    list_filter    = ["status", "frequency"]
    readonly_fields = ["payment_plan_id", "created_at", "updated_at"]
    inlines = [PaymentPlanInstallmentInline]


class FinePaymentInline(admin.TabularInline):
    model  = FinePayment
    extra  = 0
    fields = ["payment_date", "amount", "payment_method", "reference_number", "status"]
    readonly_fields = []
    show_change_link = True


@admin.register(FineInvoice)
class FineInvoiceAdmin(admin.ModelAdmin):
    list_display  = ["invoice_number", "case", "due_date", "total_amount", "paid_amount", "status"]
    list_filter   = ["status"]
    search_fields = ["invoice_number", "case__case_number"]
    readonly_fields = ["fine_invoice_id", "invoice_number", "paid_amount", "created_at", "updated_at"]
    inlines = [FinePaymentInline]


@admin.register(FinePayment)
class FinePaymentAdmin(admin.ModelAdmin):
    list_display  = ["payment_id", "invoice", "payment_date", "amount", "payment_method", "status"]
    list_filter   = ["status", "payment_method"]
    readonly_fields = ["payment_id", "created_at", "updated_at"]


@admin.register(PaymentReceipt)
class PaymentReceiptAdmin(admin.ModelAdmin):
    list_display   = ["receipt_number", "payment", "issued_at", "issued_by"]
    readonly_fields = ["receipt_id", "receipt_number", "issued_at"]
