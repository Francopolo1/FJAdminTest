from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import BasePermission, SAFE_METHODS, IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
import django_filters


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)

from .models import (
    WorkflowDefinition, WorkflowStep, WorkflowInstance,
    WorkflowTask, WorkflowAuditLog,
)
from .serializers import (
    WorkflowDefinitionSerializer, WorkflowDefinitionListSerializer,
    WorkflowStepSerializer, WorkflowInstanceSerializer,
    WorkflowInstanceListSerializer, WorkflowTaskSerializer,
    AdvanceInstanceSerializer, WorkflowAuditLogSerializer,
)
from .services import submit_instance, advance_instance
from django.contrib.auth import get_user_model

# ── Filters ───────────────────────────────────────────────────────────────
class WorkflowInstanceFilter(django_filters.FilterSet):
    status   = django_filters.MultipleChoiceFilter(choices=WorkflowInstance.STATUS_CHOICES)
    priority = django_filters.NumberFilter()
    workflow = django_filters.NumberFilter(field_name="workflow_id")
    started_after  = django_filters.DateTimeFilter(field_name="started_at", lookup_expr="gte")
    started_before = django_filters.DateTimeFilter(field_name="started_at", lookup_expr="lte")

    class Meta:
        model  = WorkflowInstance
        fields = ["status", "priority", "workflow", "started_after", "started_before"]


class WorkflowTaskFilter(django_filters.FilterSet):
    status      = django_filters.MultipleChoiceFilter(choices=WorkflowTask.STATUS_CHOICES)
    assigned_to = django_filters.NumberFilter(field_name="assigned_to_id")
    instance    = django_filters.NumberFilter(field_name="instance_id")
    overdue_only = django_filters.BooleanFilter(method="filter_overdue")

    def filter_overdue(self, qs, name, value):
        if value:
            return qs.filter(due_date__lt=timezone.now(), status__in=["Pending", "InProgress"])
        return qs

    class Meta:
        model  = WorkflowTask
        fields = ["status", "assigned_to", "instance"]


# ── ViewSets ──────────────────────────────────────────────────────────────
class WorkflowDefinitionViewSet(viewsets.ModelViewSet):
    queryset        = WorkflowDefinition.objects.prefetch_related("steps__actions", "transitions").all()
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["category", "is_active"]
    search_fields   = ["name", "description"]
    ordering_fields = ["name", "created_at"]

    def get_serializer_class(self):
        if self.action == "list":
            return WorkflowDefinitionListSerializer
        return WorkflowDefinitionSerializer


class WorkflowInstanceViewSet(viewsets.ModelViewSet):
    serializer_class   = WorkflowInstanceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class    = WorkflowInstanceFilter
    search_fields      = ["reference_no", "workflow__name"]
    ordering_fields    = ["started_at", "due_date", "priority"]
    ordering           = ["-started_at"]

    def get_queryset(self):
        from django.db.models import Q
        from apps.core.access import visible_user_ids

        qs = WorkflowInstance.objects.select_related(
            "workflow", "initiated_by", "current_step",
        ).prefetch_related("tasks", "checklist_runs__template")
        # Non-admins see instances initiated by, or with a task assigned to,
        # themselves or their direct reports
        if not self.request.user.is_staff:
            user_ids = visible_user_ids(self.request.user)
            qs = qs.filter(
                Q(initiated_by_id__in=user_ids) | Q(tasks__assigned_to_id__in=user_ids)
            ).distinct()
        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return WorkflowInstanceListSerializer
        return WorkflowInstanceSerializer

    def create(self, request, *args, **kwargs):
        workflow_id  = request.data.get("workflow")
        reference_no = request.data.get("reference_no")
        request_data = request.data.get("request_data")
        priority     = request.data.get("priority", 2)
        try:
            instance = submit_instance(
                workflow_id=workflow_id,
                initiated_by=request.user,
                reference_no=reference_no,
                request_data=request_data,
                priority=int(priority),
            )
        except (ValueError, WorkflowDefinition.DoesNotExist) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            WorkflowInstanceSerializer(instance).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="advance")
    def advance(self, request, pk=None):
        instance   = self.get_object()
        serializer = AdvanceInstanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            instance = advance_instance(
                instance=instance,
                actor=request.user,
                trigger_event=serializer.validated_data["trigger_event"],
                comments=serializer.validated_data.get("comments"),
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(WorkflowInstanceSerializer(instance).data)

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        instance = self.get_object()
        if instance.status in ("Approved", "Rejected", "Cancelled"):
            return Response(
                {"detail": "Instance is already finalized."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        from_status       = instance.status
        instance.status   = "Cancelled"
        instance.completed_at = timezone.now()
        instance.save()
        WorkflowAuditLog.objects.create(
            instance=instance, actor=request.user,
            action="Cancel", from_status=from_status, to_status="Cancelled",
            notes=request.data.get("notes"),
        )
        return Response(WorkflowInstanceSerializer(instance).data)

    @action(detail=True, methods=["get"], url_path="audit-log")
    def audit_log(self, request, pk=None):
        instance = self.get_object()
        logs     = instance.audit_logs.select_related("actor").order_by("-logged_at")
        return Response(WorkflowAuditLogSerializer(logs, many=True).data)

    @action(detail=True, methods=["get"], url_path="available-transitions")
    def available_transitions(self, request, pk=None):
        instance = self.get_object()
        if not instance.current_step:
            return Response([])
        from .models import WorkflowTransition
        transitions = WorkflowTransition.objects.filter(
            from_step=instance.current_step
        ).values("trigger_event", "transition_name", "to_step__step_name")
        return Response(list(transitions))

    @action(detail=False, methods=["get"], url_path="distributions")
    def distributions(self, request):
        from django.db.models import Count, F, Q
        from apps.core.access import visible_user_ids

        qs = WorkflowInstance.objects.all()
        if not request.user.is_staff:
            user_ids = visible_user_ids(request.user)
            qs = qs.filter(
                Q(initiated_by_id__in=user_ids) | Q(tasks__assigned_to_id__in=user_ids)
            )

        by_program = (
            qs.annotate(
                program_code=F("program_facility__program_facility_type__program__code"),
                program_title=F("program_facility__program_facility_type__program__title"),
            )
            .values("program_code", "program_title")
            .annotate(count=Count("instance_id", distinct=True))
            .order_by("-count")
        )
        by_activity = (
            qs.annotate(
                activity=F("workflow__program_facility_type_activity__description"),
            )
            .values("activity")
            .annotate(count=Count("instance_id", distinct=True))
            .order_by("-count")
        )
        return Response({
            "by_program": list(by_program),
            "by_activity": list(by_activity),
        })


class WorkflowTaskViewSet(viewsets.ModelViewSet):
    serializer_class   = WorkflowTaskSerializer
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class    = WorkflowTaskFilter
    ordering_fields    = ["assigned_at", "due_date"]
    ordering           = ["due_date"]

    def get_queryset(self):
        qs = WorkflowTask.objects.select_related(
            "instance", "step", "assigned_to", "assigned_by", "delegated_to"
        )
        if not self.request.user.is_staff:
            from apps.core.access import visible_user_ids

            qs = qs.filter(assigned_to_id__in=visible_user_ids(self.request.user))
        return qs

    @action(detail=True, methods=["post"], url_path="delegate")
    def delegate(self, request, pk=None):
        task = self.get_object()
        to_user_id = request.data.get("delegate_to")
        if not to_user_id:
            return Response({"detail": "delegate_to is required."}, status=400)
        User = get_user_model()
        try:
            delegate_user = User.objects.get(pk=to_user_id, is_active=True)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=404)
        task.delegated_to = delegate_user
        task.assigned_to  = delegate_user
        task.status       = "Delegated"
        task.save()
        WorkflowAuditLog.objects.create(
            instance=task.instance, task=task, actor=request.user,
            action="Delegate",
            notes=f"Delegated to {delegate_user.full_name}",
        )
        return Response(WorkflowTaskSerializer(task).data)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class   = WorkflowAuditLogSerializer
    permission_classes = [IsAdminUser]
    filter_backends    = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields   = ["instance", "actor", "action"]
    ordering           = ["-logged_at"]
    queryset           = WorkflowAuditLog.objects.select_related("instance", "actor", "task").all()
