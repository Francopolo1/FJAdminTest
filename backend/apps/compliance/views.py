"""
Compliance API views.

Endpoints
──────────────────────────────────────────────────────────────────────────
Rules
  GET    /api/compliance/rules/               list  (filterable)
  GET    /api/compliance/rules/{id}/          detail + violation count
  GET    /api/compliance/rules/{id}/violations/  violations for a rule
  GET    /api/compliance/rules/{id}/schedules/   fine schedules for a rule

Severity levels
  GET    /api/compliance/severity-levels/     list

Fine schedules
  GET    /api/compliance/fine-schedules/      list
  GET    /api/compliance/fine-schedules/{id}/ detail + tiers

Checklist-item ↔ rule links
  GET    /api/compliance/item-rules/          list (filter by checklist_item or rule)

Violations
  GET    /api/compliance/violations/          list (filterable)
  POST   /api/compliance/violations/          create new violation
  GET    /api/compliance/violations/{id}/     detail

Dashboard
  GET    /api/compliance/summary/             aggregated stats
"""

from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
import django_filters

from .models import (
    ComplianceRule, ViolationSeverityLevel,
    FineSchedule, FineTier,
    ChecklistItemComplianceRule, ComplianceViolation,
)
from .serializers import (
    ComplianceRuleSerializer, ComplianceRuleListSerializer,
    ViolationSeverityLevelSerializer,
    FineScheduleSerializer, FineScheduleListSerializer,
    FineTierSerializer,
    ChecklistItemComplianceRuleSerializer,
    ComplianceViolationSerializer, ComplianceViolationCreateSerializer,
    ComplianceSummarySerializer,
)


# ── Filters ───────────────────────────────────────────────────────────────

class ComplianceViolationFilter(django_filters.FilterSet):
    severity   = django_filters.UUIDFilter(field_name="violation_severity_level_id")
    rule       = django_filters.UUIDFilter(
        field_name="checklist_item_compliance_rule__compliance_rule_id"
    )
    date_after  = django_filters.DateFilter(field_name="violation_date", lookup_expr="gte")
    date_before = django_filters.DateFilter(field_name="violation_date", lookup_expr="lte")

    class Meta:
        model  = ComplianceViolation
        fields = ["severity", "rule", "date_after", "date_before"]


class FineScheduleFilter(django_filters.FilterSet):
    rule = django_filters.UUIDFilter(field_name="compliance_rule_id")

    class Meta:
        model  = FineSchedule
        fields = ["rule"]


# ── ComplianceRule ViewSet ────────────────────────────────────────────────

class ComplianceRuleViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List and retrieve compliance rules.
    Admins can also create / update / deactivate via the Django admin.
    """
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ["is_active"]
    search_fields      = ["code", "name", "description"]
    ordering_fields    = ["code", "name", "created_date"]
    ordering           = ["code"]

    def get_queryset(self):
        return ComplianceRule.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return ComplianceRuleListSerializer
        return ComplianceRuleSerializer

    @action(detail=True, methods=["get"])
    def violations(self, request, pk=None):
        """All violations linked to this rule (most recent first)."""
        rule = self.get_object()
        qs   = ComplianceViolation.objects.filter(
            checklist_item_compliance_rule__compliance_rule=rule
        ).select_related("violation_severity_level", "checklist_item_compliance_rule")
        return Response(ComplianceViolationSerializer(qs, many=True).data)

    @action(detail=True, methods=["get"])
    def schedules(self, request, pk=None):
        """Fine schedules for this rule."""
        rule = self.get_object()
        qs   = FineSchedule.objects.filter(compliance_rule=rule).prefetch_related("tiers")
        return Response(FineScheduleSerializer(qs, many=True).data)


# ── ViolationSeverityLevel ViewSet ────────────────────────────────────────

class ViolationSeverityLevelViewSet(viewsets.ReadOnlyModelViewSet):
    queryset           = ViolationSeverityLevel.objects.all()
    serializer_class   = ViolationSeverityLevelSerializer
    permission_classes = [IsAuthenticated]
    filter_backends    = [filters.OrderingFilter]
    ordering           = ["rank"]


# ── FineSchedule ViewSet ──────────────────────────────────────────────────

class FineScheduleViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class    = FineScheduleFilter
    search_fields      = ["schedule_name", "compliance_rule__code", "compliance_rule__name"]
    ordering_fields    = ["effective_date", "schedule_name"]
    ordering           = ["-effective_date"]

    def get_queryset(self):
        return (
            FineSchedule.objects
            .select_related("compliance_rule")
            .prefetch_related("tiers__violation_severity_level")
        )

    def get_serializer_class(self):
        if self.action == "list":
            return FineScheduleListSerializer
        return FineScheduleSerializer


# ── ChecklistItemComplianceRule ViewSet ───────────────────────────────────

class ChecklistItemComplianceRuleViewSet(viewsets.ReadOnlyModelViewSet):
    """Links between checklist items and compliance rules."""
    serializer_class   = ChecklistItemComplianceRuleSerializer
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend]
    filterset_fields   = ["compliance_rule", "checklist_item"]

    def get_queryset(self):
        return (
            ChecklistItemComplianceRule.objects
            .select_related("compliance_rule", "checklist_item")
        )


# ── ComplianceViolation ViewSet ───────────────────────────────────────────

class ComplianceViolationViewSet(viewsets.ModelViewSet):
    """
    List, retrieve, and create compliance violations.
    Update/delete is admin-only.
    """
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class    = ComplianceViolationFilter
    ordering_fields    = ["violation_date"]
    ordering           = ["-violation_date"]

    def get_queryset(self):
        return (
            ComplianceViolation.objects
            .select_related(
                "violation_severity_level",
                "checklist_item_compliance_rule__compliance_rule",
                "checklist_item_compliance_rule__checklist_item",
            )
        )

    def get_serializer_class(self):
        if self.action == "create":
            return ComplianceViolationCreateSerializer
        return ComplianceViolationSerializer

    def get_permissions(self):
        if self.action in ("update", "partial_update", "destroy"):
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        ser = ComplianceViolationCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data

        # Resolve FKs
        try:
            rule_link = ChecklistItemComplianceRule.objects.get(
                pk=d["checklist_item_compliance_rule_id"]
            )
        except ChecklistItemComplianceRule.DoesNotExist:
            return Response(
                {"detail": "checklist_item_compliance_rule not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            severity = ViolationSeverityLevel.objects.get(
                pk=d["violation_severity_level_id"]
            )
        except ViolationSeverityLevel.DoesNotExist:
            return Response(
                {"detail": "violation_severity_level not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        violation = ComplianceViolation(
            checklist_item_compliance_rule = rule_link,
            violation_date                 = d["violation_date"],
            violation_severity_level       = severity,
            violation_description          = d.get("violation_description"),
            detected_by                    = request.user.pk,
            checklist_response_id          = d["checklist_response_id"],
        )
        violation.save()
        return Response(
            ComplianceViolationSerializer(violation).data,
            status=status.HTTP_201_CREATED,
        )


# ── Summary view ──────────────────────────────────────────────────────────

class ComplianceSummaryView(APIView):
    """
    GET /api/compliance/summary/
    Returns aggregated compliance statistics.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        now     = timezone.now()
        cutoff  = (now - timedelta(days=30)).date()

        rules      = ComplianceRule.objects.all()
        violations = ComplianceViolation.objects.all()
        schedules  = FineSchedule.objects.all()

        # Top 5 most-violated rules
        top_violated = list(
            ChecklistItemComplianceRule.objects
            .values("compliance_rule__code", "compliance_rule__name")
            .annotate(count=Count("violations"))
            .order_by("-count")[:5]
        )

        # Violations by severity
        severity_breakdown = list(
            violations
            .values("violation_severity_level__code", "violation_severity_level__name")
            .annotate(count=Count("compliance_violation_id"))
            .order_by("-count")
        )

        # Active fine schedules (effective_date <= today, expiration_date is null or >= today)
        active_schedules = sum(1 for s in schedules if s.is_active)

        payload = {
            "total_rules":              rules.count(),
            "active_rules":             rules.filter(is_active=True).count(),
            "total_violations":         violations.count(),
            "violations_last_30_days":  violations.filter(violation_date__gte=cutoff).count(),
            "rules_with_violations":    (
                ChecklistItemComplianceRule.objects
                .annotate(v=Count("violations"))
                .filter(v__gt=0)
                .values("compliance_rule_id")
                .distinct()
                .count()
            ),
            "top_violated_rules":   top_violated,
            "severity_breakdown":   severity_breakdown,
            "active_fine_schedules": active_schedules,
        }
        serializer = ComplianceSummarySerializer(payload)
        return Response(serializer.data)
