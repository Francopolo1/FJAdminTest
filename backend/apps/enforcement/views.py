from django.db import models
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

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
from .serializers import (
    FineCaseListSerializer,
    FineCaseDetailSerializer,
    FineAssessmentSerializer,
    AssessFineInputSerializer,
    FineInvoiceSerializer,
    CreateInvoiceInputSerializer,
    PaymentPlanSerializer,
    SetupPaymentPlanInputSerializer,
    FinePaymentSerializer,
    ReceivePaymentInputSerializer,
    PaymentReceiptSerializer,
    FineAppealSerializer,
    AppealDecisionInputSerializer,
    FineWaiverSerializer,
)
from . import services


class FineCaseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = FineCase.objects.select_related(
        "program_facility__facility",
        "created_by",
    ).prefetch_related(
        "assessments__violation",
        "assessments__fine_tier",
        "assessments__assessed_by",
        "invoices__line_items",
        "invoices__payment_plan__installments",
        "invoices__payments__receipt",
        "invoices__payments__received_by",
    ).order_by("-opened_date")

    def get_serializer_class(self):
        if self.action == "retrieve":
            return FineCaseDetailSerializer
        return FineCaseListSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"], url_path="assess-fine")
    def assess_fine(self, request, pk=None):
        case = self.get_object()
        inp = AssessFineInputSerializer(data=request.data)
        inp.is_valid(raise_exception=True)
        d = inp.validated_data

        from apps.compliance.models import ComplianceViolation, FineTier
        try:
            violation = ComplianceViolation.objects.get(pk=d["violation_id"])
        except ComplianceViolation.DoesNotExist:
            return Response({"detail": "Violation not found."}, status=status.HTTP_404_NOT_FOUND)

        fine_tier = None
        if d.get("fine_tier_id"):
            try:
                fine_tier = FineTier.objects.get(pk=d["fine_tier_id"])
            except FineTier.DoesNotExist:
                return Response({"detail": "FineTier not found."}, status=status.HTTP_404_NOT_FOUND)

        assessment = services.assess_fine(
            case=case,
            violation=violation,
            assessed_amount=d["assessed_amount"],
            fine_tier=fine_tier,
            notes=d.get("notes"),
            assessed_by=request.user,
        )
        return Response(FineAssessmentSerializer(assessment).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="create-invoice")
    def create_invoice(self, request, pk=None):
        case = self.get_object()
        inp = CreateInvoiceInputSerializer(data=request.data)
        inp.is_valid(raise_exception=True)
        d = inp.validated_data
        try:
            invoice = services.create_invoice(case=case, due_date=d["due_date"], notes=d.get("notes"))
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(FineInvoiceSerializer(invoice).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="close")
    def close_case(self, request, pk=None):
        case = self.get_object()
        notes = request.data.get("notes")
        try:
            case = services.close_case(case=case, notes=notes)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(FineCaseDetailSerializer(case).data)


class FineInvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = FineInvoiceSerializer
    queryset = FineInvoice.objects.select_related("case").prefetch_related(
        "line_items",
        "payment_plan__installments",
        "payments__receipt",
        "payments__received_by",
    ).order_by("-invoice_date")

    def get_queryset(self):
        qs = super().get_queryset()
        case_id = self.request.query_params.get("case")
        if case_id:
            qs = qs.filter(case_id=case_id)
        return qs

    @action(detail=True, methods=["post"], url_path="setup-payment-plan")
    def setup_payment_plan(self, request, pk=None):
        invoice = self.get_object()
        inp = SetupPaymentPlanInputSerializer(data=request.data)
        inp.is_valid(raise_exception=True)
        d = inp.validated_data
        try:
            plan = services.setup_payment_plan(
                invoice=invoice,
                number_of_installments=d["number_of_installments"],
                frequency=d["frequency"],
                first_due_date=d["first_due_date"],
                approved_by=request.user,
                notes=d.get("notes"),
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(PaymentPlanSerializer(plan).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="receive-payment")
    def receive_payment(self, request, pk=None):
        invoice = self.get_object()
        inp = ReceivePaymentInputSerializer(data=request.data)
        inp.is_valid(raise_exception=True)
        d = inp.validated_data

        installment = None
        if d.get("installment_id"):
            try:
                installment = PaymentPlanInstallment.objects.get(pk=d["installment_id"])
            except PaymentPlanInstallment.DoesNotExist:
                return Response({"detail": "Installment not found."}, status=status.HTTP_404_NOT_FOUND)

        payment = services.receive_payment(
            invoice=invoice,
            amount=d["amount"],
            payment_method=d["payment_method"],
            payment_date=d.get("payment_date"),
            reference_number=d.get("reference_number"),
            received_by=request.user,
            installment=installment,
            notes=d.get("notes"),
        )
        return Response(FinePaymentSerializer(payment).data, status=status.HTTP_201_CREATED)


class FinePaymentViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = FinePaymentSerializer
    queryset = FinePayment.objects.select_related(
        "invoice__case", "installment", "received_by", "receipt",
    ).order_by("-payment_date")

    def get_queryset(self):
        qs = super().get_queryset()
        invoice_id = self.request.query_params.get("invoice")
        if invoice_id:
            qs = qs.filter(invoice_id=invoice_id)
        return qs

    @action(detail=True, methods=["post"], url_path="generate-receipt")
    def generate_receipt(self, request, pk=None):
        payment = self.get_object()
        notes = request.data.get("notes")
        try:
            receipt = services.generate_receipt(
                payment=payment,
                issued_by=request.user,
                notes=notes,
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(PaymentReceiptSerializer(receipt).data, status=status.HTTP_201_CREATED)


class FineAppealViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class   = FineAppealSerializer
    queryset = FineAppeal.objects.select_related(
        "assessment__case",
        "filed_by",
        "decided_by",
    ).order_by("-appeal_date")

    def get_queryset(self):
        qs = super().get_queryset()
        assessment_id = self.request.query_params.get("assessment")
        if assessment_id:
            qs = qs.filter(assessment_id=assessment_id)
        case_id = self.request.query_params.get("case")
        if case_id:
            qs = qs.filter(assessment__case_id=case_id)
        return qs

    def perform_create(self, serializer):
        assessment = serializer.validated_data["assessment"]
        grounds    = serializer.validated_data["grounds"]
        services.file_appeal(
            assessment=assessment,
            grounds=grounds,
            appeal_date=serializer.validated_data.get("appeal_date"),
            hearing_date=serializer.validated_data.get("hearing_date"),
            filed_by=self.request.user,
        )

    def create(self, request, *args, **kwargs):
        ser = FineAppealSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        assessment = ser.validated_data["assessment"]
        appeal = services.file_appeal(
            assessment=assessment,
            grounds=ser.validated_data["grounds"],
            appeal_date=ser.validated_data.get("appeal_date"),
            hearing_date=ser.validated_data.get("hearing_date"),
            filed_by=request.user,
        )
        return Response(FineAppealSerializer(appeal).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="decide")
    def decide(self, request, pk=None):
        appeal = self.get_object()
        if appeal.status in ("Upheld", "Reduced", "Dismissed", "Withdrawn"):
            return Response(
                {"detail": "This appeal has already been decided."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        inp = AppealDecisionInputSerializer(data=request.data)
        inp.is_valid(raise_exception=True)
        d = inp.validated_data
        try:
            appeal = services.decide_appeal(
                appeal=appeal,
                status=d["status"],
                decided_by=request.user,
                decision_notes=d.get("decision_notes"),
                decision_date=d.get("decision_date"),
                adjusted_amount=d.get("adjusted_amount"),
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(FineAppealSerializer(appeal).data)


class FineWaiverViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class   = FineWaiverSerializer
    queryset = FineWaiver.objects.select_related(
        "assessment__case",
        "invoice__case",
        "authorized_by",
    ).order_by("-authorization_date")

    def get_queryset(self):
        qs = super().get_queryset()
        if assessment_id := self.request.query_params.get("assessment"):
            qs = qs.filter(assessment_id=assessment_id)
        if invoice_id := self.request.query_params.get("invoice"):
            qs = qs.filter(invoice_id=invoice_id)
        if case_id := self.request.query_params.get("case"):
            qs = qs.filter(
                models.Q(assessment__case_id=case_id) | models.Q(invoice__case_id=case_id)
            )
        return qs

    def create(self, request, *args, **kwargs):
        ser = FineWaiverSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        try:
            waiver = services.apply_waiver(
                waived_amount=d["waived_amount"],
                reason=d["reason"],
                assessment=d.get("assessment"),
                invoice=d.get("invoice"),
                authorized_by=request.user,
                authorization_date=d.get("authorization_date"),
                notes=d.get("notes"),
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(FineWaiverSerializer(waiver).data, status=status.HTTP_201_CREATED)
