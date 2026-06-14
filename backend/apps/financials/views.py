from decimal import Decimal
from django.db.models import Count, Sum
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
import django_filters

from .models import (Fund, Org, Account, Program, Activity, Location,
                     FoapalString, Transaction, TransactionSplit)
from .serializers import (
    FundSerializer, FundListSerializer,
    OrgSerializer, OrgListSerializer,
    AccountSerializer, AccountListSerializer,
    ActivitySerializer, LocationSerializer,
    FoapalStringSerializer, FoapalStringListSerializer,
    TransactionSerializer, TransactionListSerializer,
    TransactionSplitSerializer, FinancialsSummarySerializer, ProgramSerializer, ProgramListSerializer
)


class TransactionFilter(django_filters.FilterSet):
    status      = django_filters.MultipleChoiceFilter(choices=Transaction.STATUS_CHOICES)
    fund        = django_filters.UUIDFilter(field_name="fund_id")
    org         = django_filters.UUIDFilter(field_name="org_id")
    account     = django_filters.UUIDFilter(field_name="account_id")
    currency    = django_filters.CharFilter(field_name="currency")
    date_after  = django_filters.DateFilter(field_name="transaction_date", lookup_expr="gte")
    date_before = django_filters.DateFilter(field_name="transaction_date", lookup_expr="lte")
    amount_min  = django_filters.NumberFilter(field_name="amount", lookup_expr="gte")
    amount_max  = django_filters.NumberFilter(field_name="amount", lookup_expr="lte")
    class Meta:
        model  = Transaction
        fields = ["status", "fund", "org", "account", "currency",
                  "date_after", "date_before", "amount_min", "amount_max"]


class FoapalFilter(django_filters.FilterSet):
    fund     = django_filters.UUIDFilter(field_name="fund_id")
    org      = django_filters.UUIDFilter(field_name="org_id")
    account  = django_filters.UUIDFilter(field_name="account_id")
    is_active = django_filters.BooleanFilter()
    class Meta:
        model  = FoapalString
        fields = ["fund", "org", "account", "is_active"]


class FundViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ["is_active", "fund_type"]
    search_fields      = ["code", "title"]
    ordering           = ["code"]

    def get_queryset(self):         return Fund.objects.all()
    def get_serializer_class(self): return FundListSerializer if self.action == "list" else FundSerializer


class OrgViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ["is_active"]
    search_fields      = ["code", "title"]
    ordering           = ["code"]

    def get_queryset(self):         return Org.objects.select_related("parent_org").all()
    def get_serializer_class(self): return OrgListSerializer if self.action == "list" else OrgSerializer

    @action(detail=True, methods=["get"])
    def children(self, request, pk=None):
        return Response(OrgListSerializer(Org.objects.filter(parent_org=self.get_object()), many=True).data)


class AccountViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ["is_active", "account_type", "normal_balance"]
    search_fields      = ["code", "title"]
    ordering           = ["code"]

    def get_queryset(self):         return Account.objects.all()
    def get_serializer_class(self): return AccountListSerializer if self.action == "list" else AccountSerializer

class ProgramViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ["is_active"]
    search_fields      = ["code", "title"]
    ordering           = ["code"]

    def get_queryset(self):         return Program.objects.all()
    def get_serializer_class(self): return ProgramListSerializer if self.action == "list" else ProgramSerializer    

class ActivityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset           = Activity.objects.all()
    serializer_class   = ActivitySerializer
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields   = ["is_active"]
    search_fields      = ["code", "title"]


class LocationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset           = Location.objects.all()
    serializer_class   = LocationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields   = ["is_active", "campus"]
    search_fields      = ["code", "title", "building", "campus"]


class FoapalStringViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class    = FoapalFilter
    search_fields      = ["foapal_code", "description", "fund__code", "org__code", "account__code"]
    ordering           = ["foapal_code"]

    def get_queryset(self):
        return FoapalString.objects.select_related("fund", "org", "account", "program", "activity", "location")

    def get_serializer_class(self):
        return FoapalStringListSerializer if self.action == "list" else FoapalStringSerializer

    @action(detail=True, methods=["get"])
    def transactions(self, request, pk=None):
        qs = Transaction.objects.filter(foapal_string=self.get_object()).select_related("fund", "org", "account")
        return Response(TransactionListSerializer(qs, many=True).data)


class TransactionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class    = TransactionFilter
    search_fields      = ["reference_number", "description", "coded_by", "approved_by",
                          "foapal_string__foapal_code"]
    ordering_fields    = ["transaction_date", "amount", "status", "created_at"]
    ordering           = ["-transaction_date"]

    def get_queryset(self):
        return Transaction.objects.select_related(
            "foapal_string", "fund", "org", "account", "activity", "location"
        ).prefetch_related("splits__foapal_string")

    def get_serializer_class(self):
        return TransactionListSerializer if self.action == "list" else TransactionSerializer

    def get_permissions(self):
        if self.action in ("create", "destroy", "update", "partial_update", "approve", "void"):
            return [IsAdminUser()]
        return [IsAuthenticated()]

    @action(detail=True, methods=["get"])
    def splits(self, request, pk=None):
        qs = self.get_object().splits.select_related("foapal_string")
        return Response(TransactionSplitSerializer(qs, many=True).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAdminUser])
    def approve(self, request, pk=None):
        txn = self.get_object()
        if txn.status != "Coded":
            return Response({"detail": f"Cannot approve — status is '{txn.status}', expected 'Coded'."},
                            status=status.HTTP_400_BAD_REQUEST)
        from django.utils import timezone
        txn.status = "Approved"
        txn.approved_by = request.user.get_full_name() or request.user.username
        txn.approved_at = timezone.now()
        txn.save(update_fields=["status", "approved_by", "approved_at", "updated_at"])
        return Response(TransactionSerializer(txn).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAdminUser])
    def void(self, request, pk=None):
        txn = self.get_object()
        if txn.status == "Voided":
            return Response({"detail": "Already voided."}, status=status.HTTP_400_BAD_REQUEST)
        reason  = request.data.get("reason", "")
        txn.status = "Voided"
        txn.notes  = (txn.notes or "") + f"\nVoided by {request.user.username}: {reason}"
        txn.save(update_fields=["status", "notes", "updated_at"])
        return Response(TransactionSerializer(txn).data)


class TransactionSplitViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class   = TransactionSplitSerializer
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields   = ["transaction", "foapal_string"]
    ordering           = ["-created_at"]

    def get_queryset(self):
        return TransactionSplit.objects.select_related("foapal_string", "transaction")


class FinancialsSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        txns = Transaction.objects.all()

        def _agg(s):
            qs = txns.filter(status=s)
            return {"count": qs.count(), "amount": qs.aggregate(t=Sum("amount"))["t"] or Decimal("0.00")}

        pending  = _agg("Pending")
        approved = _agg("Approved")
        posted   = _agg("Posted")
        voided   = _agg("Voided")

        payload = {
            "total_transactions":    txns.count(),
            "total_amount":          txns.aggregate(t=Sum("amount"))["t"] or Decimal("0.00"),
            "pending_count":         pending["count"],
            "pending_amount":        pending["amount"],
            "approved_count":        approved["count"],
            "approved_amount":       approved["amount"],
            "posted_count":          posted["count"],
            "posted_amount":         posted["amount"],
            "voided_count":          voided["count"],
            "status_breakdown":      list(
                txns.values("status").annotate(count=Count("id"), total=Sum("amount")).order_by("status")
            ),
            "top_funds": list(
                txns.exclude(fund__isnull=True)
                .values("fund__code", "fund__title")
                .annotate(count=Count("id"), total=Sum("amount"))
                .order_by("-total")[:5]
            ),
            "top_accounts": list(
                txns.exclude(account__isnull=True)
                .values("account__code", "account__title", "account__account_type")
                .annotate(count=Count("id"), total=Sum("amount"))
                .order_by("-total")[:5]
            ),
            "active_foapal_strings": FoapalString.objects.filter(is_active=True).count(),
            "total_splits":          TransactionSplit.objects.count(),
        }
        return Response(FinancialsSummarySerializer(payload).data)
