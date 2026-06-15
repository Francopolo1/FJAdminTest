

"""
Checklist views.

Endpoints
──────────────────────────────────────────────────────────────────────────
Templates
  GET    /checklists/templates/                    list
  POST   /checklists/templates/                    create  (admin)
  GET    /checklists/templates/{id}/               detail
  PUT    /checklists/templates/{id}/               full update  (admin)
  PATCH  /checklists/templates/{id}/               partial update  (admin)
  DELETE /checklists/templates/{id}/               delete  (admin)
  POST   /checklists/templates/{id}/add-items/     bulk-create items  (admin)
  POST   /checklists/templates/{id}/reorder-items/ reorder items  (admin)
  GET    /checklists/templates/{id}/preview/       rendered item list

Items
  GET    /checklists/items/                        list
  POST   /checklists/items/                        create  (admin)
  GET    /checklists/items/{id}/                   detail
  PUT    /checklists/items/{id}/                   update  (admin)
  PATCH  /checklists/items/{id}/                   partial update  (admin)
  DELETE /checklists/items/{id}/                   delete  (admin)

Runs
  GET    /checklists/runs/                         list  (own runs; admin sees all)
  GET    /checklists/runs/{id}/                    detail
  POST   /checklists/runs/{id}/respond/            submit answers (batch)
  POST   /checklists/runs/{id}/skip/               skip non-blocking run
  POST   /checklists/runs/{id}/reopen/             reopen a completed run  (admin)
  GET    /checklists/runs/{id}/progress/           per-item breakdown
  GET    /checklists/runs/{id}/export/             CSV export of responses
"""

import csv
import io
import uuid
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.files.storage import default_storage
from django.http import StreamingHttpResponse
from django.utils import timezone
from rest_framework import serializers, viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
import django_filters

from apps.core.box_service import BoxConfigError, BoxAPIException, get_or_create_folder
from .models import ChecklistTemplate, ChecklistItem, ChecklistRun, ChecklistResponse
from .serializers import (
    ChecklistTemplateSerializer, ChecklistTemplateListSerializer,
    ChecklistItemSerializer,
    ChecklistRunSerializer, ChecklistRunListSerializer,
    ChecklistResponseSerializer,
    ChecklistProgressSerializer,
    SubmitResponseSerializer,
    BulkCreateItemSerializer,
)
from rest_framework import permissions

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        if request.user.is_staff:
            return True

        # Write permissions are only allowed to the owner of the run (if any).
        instance = getattr(obj, "instance", None)
        return instance is not None and instance.initiated_by == request.user


# ── Filters ───────────────────────────────────────────────────────────────────

class ChecklistTemplateFilter(django_filters.FilterSet):
    workflow       = django_filters.NumberFilter(field_name="workflow_id")
    step           = django_filters.NumberFilter(field_name="step_id")
    blocks_advance = django_filters.BooleanFilter()
    is_required    = django_filters.BooleanFilter()

    class Meta:
        model  = ChecklistTemplate
        fields = ["workflow", "step", "blocks_advance", "is_required"]


class ChecklistRunFilter(django_filters.FilterSet):
    instance  = django_filters.NumberFilter(field_name="instance_id")
    task      = django_filters.NumberFilter(field_name="task_id")
    template  = django_filters.NumberFilter(field_name="template_id")
    workflow  = django_filters.NumberFilter(field_name="instance__workflow_id")
    status    = django_filters.MultipleChoiceFilter(choices=ChecklistRun.STATUS_CHOICES)
    blocking  = django_filters.BooleanFilter(method="filter_blocking")
    completed_after  = django_filters.DateTimeFilter(field_name="completed_at", lookup_expr="gte")
    completed_before = django_filters.DateTimeFilter(field_name="completed_at", lookup_expr="lte")

    def filter_blocking(self, qs, name, value):
        """Filter runs that are currently blocking workflow advance."""
        if value:
            return qs.filter(
                template__blocks_advance=True,
            ).exclude(status__in=["Completed", "Skipped"])
        return qs.filter(
            template__blocks_advance=True,
            status__in=["Completed", "Skipped"],
        )

    class Meta:
        model  = ChecklistRun
        fields = ["instance", "task", "template", "workflow", "status"]


# ── ChecklistTemplateViewSet ──────────────────────────────────────────────────

class ChecklistTemplateViewSet(viewsets.ModelViewSet):
    """
    CRUD for checklist templates.
    Read access:   any authenticated user.
    Write access:  admin / staff only.
    """
    permission_classes = [IsAdminOrReadOnly]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class    = ChecklistTemplateFilter
    search_fields      = ["title", "description"]
    ordering_fields    = ["display_order", "created_at", "title"]
    ordering           = ["display_order"]

    def get_queryset(self):
        return (
            ChecklistTemplate.objects
            .select_related("workflow", "step")
            .prefetch_related("items")
            .all()
        )

    def get_serializer_class(self):
        if self.action == "list":
            return ChecklistTemplateListSerializer
        return ChecklistTemplateSerializer

    # ── POST /templates/{id}/add-items/ ──────────────────────────────────

    @action(
        detail=True, methods=["post"],
        url_path="add-items",
        permission_classes=[IsAdminUser],
    )
    def add_items(self, request, pk=None):
        """
        Bulk-create items for a template without replacing existing ones.

        Body:
          { "items": [ { "item_text": "...", "response_type": "YesNo", ... }, ... ] }
        """
        template   = self.get_object()
        serializer = BulkCreateItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        created = []
        for item_data in serializer.validated_data["items"]:
            item_data.setdefault("template", template)
            created.append(
                ChecklistItem.objects.create(template=template, **item_data)
            )

        return Response(
            ChecklistItemSerializer(created, many=True).data,
            status=status.HTTP_201_CREATED,
        )

    # ── POST /templates/{id}/reorder-items/ ──────────────────────────────

    @action(
        detail=True, methods=["post"],
        url_path="reorder-items",
        permission_classes=[IsAdminUser],
    )
    def reorder_items(self, request, pk=None):
        """
        Update display_order for multiple items in one request.

        Body:
          { "order": [ { "id": 1, "display_order": 1 }, ... ] }
        """
        template = self.get_object()
        order    = request.data.get("order", [])

        if not order:
            return Response(
                {"detail": "Provide a non-empty 'order' list."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        item_ids = {item["id"] for item in order if "id" in item}
        items    = {i.pk: i for i in template.items.filter(pk__in=item_ids)}

        updated = []
        for entry in order:
            item = items.get(entry.get("id"))
            if not item:
                return Response(
                    {"detail": f"Item {entry.get('id')} not found in this template."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            item.display_order = entry.get("display_order", item.display_order)
            item.save(update_fields=["display_order"])
            updated.append(item)

        return Response(ChecklistItemSerializer(updated, many=True).data)

    # ── GET /templates/{id}/preview/ ─────────────────────────────────────

    @action(detail=True, methods=["get"], url_path="preview")
    def preview(self, request, pk=None):
        """Return the ordered item list for a template — useful for UI preview."""
        template = self.get_object()
        items    = template.items.order_by("display_order")
        return Response({
            "template_id":   template.pk,
            "title":         template.title,
            "description":   template.description,
            "blocks_advance": template.blocks_advance,
            "items":         ChecklistItemSerializer(items, many=True).data,
        })


# ── ChecklistItemViewSet ──────────────────────────────────────────────────────

class ChecklistItemViewSet(viewsets.ModelViewSet):
    """
    CRUD for individual checklist items.
    Read:  authenticated users.
    Write: admin only.
    """
    serializer_class   = ChecklistItemSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ["template", "response_type", "is_required", "category"]
    search_fields      = ["item_text", "help_text"]
    ordering_fields    = ["category", "display_order", "created_at"]
    ordering           = ["category", "display_order"]

    def get_queryset(self):
        return (
            ChecklistItem.objects
            .select_related("template__workflow", "template__step")
            .all()
        )

    def perform_create(self, serializer):
        try:
            serializer.save()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)

    @action(detail=True, methods=["post"], url_path="upload-example", parser_classes=[MultiPartParser])
    def upload_example(self, request, pk=None):
        """Upload an example image/PDF/video for this item and set example_url."""
        item = self.get_object()
        upload = request.FILES.get("file")
        if not upload:
            return Response({"detail": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)

        allowed_types = {
            "image/png", "image/jpeg", "image/gif", "image/webp", "application/pdf",
            "video/mp4", "video/webm", "video/ogg", "video/quicktime",
        }
        if upload.content_type not in allowed_types:
            return Response(
                {"detail": "Only PNG, JPEG, GIF, WEBP, PDF, MP4, WEBM, OGG, and MOV files are allowed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ext = upload.name.rsplit(".", 1)[-1].lower() if "." in upload.name else ""
        filename = f"checklist_examples/{uuid.uuid4()}.{ext}" if ext else f"checklist_examples/{uuid.uuid4()}"
        saved_path = default_storage.save(filename, upload)

        item.example_url = request.build_absolute_uri(default_storage.url(saved_path))
        item.save(update_fields=["example_url"])
        return Response(ChecklistItemSerializer(item).data)


# ── ChecklistRunViewSet ───────────────────────────────────────────────────────

class ChecklistRunViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Runs are created automatically by the workflow engine; they are never
    created manually via the API.  This ViewSet exposes:

      • list / retrieve   (standard DRF)
      • respond           POST batch answers
      • skip              POST skip a non-blocking run
      • reopen            POST reopen a completed run (admin)
      • progress          GET per-item breakdown
      • export            GET CSV download
    """
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class    = ChecklistRunFilter
    ordering_fields    = ["created_at", "started_at", "completed_at", "status"]
    ordering           = ["-created_at"]

    def get_queryset(self):
        qs = (
            ChecklistRun.objects
            .select_related(
                "template__workflow",
                "instance__workflow",
                "instance__initiated_by",
                "instance__workflow__program_facility_type_activity",
                "instance__program_facility__program_facility_type__program",
                "task",
            )
            .prefetch_related(
                "responses__item",
                "responses__responded_by",
            )
        )
        if not self.request.user.is_staff:
            from apps.core.access import visible_user_ids

            user_ids = visible_user_ids(self.request.user)
            qs = (
                qs.filter(instance__initiated_by_id__in=user_ids)
                | qs.filter(task__assigned_to_id__in=user_ids)
                | qs.filter(instance__tasks__assigned_to_id__in=user_ids)
            )
        return qs.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return ChecklistRunListSerializer
        return ChecklistRunSerializer

    # ── POST /runs/{id}/respond/ ──────────────────────────────────────────

    @action(detail=True, methods=["post"])
    def respond(self, request, pk=None):
        """
        Submit answers for one or more checklist items in a single request.

        Accepts either a single object or a list:
          { "item": 1, "response_value": "Yes" }
          or
          [ { "item": 1, ... }, { "item": 2, ... } ]

        Rules
          • Run must not be Completed or Skipped.
          • Each item must belong to the run's template.
          • response_value is validated against the item's response_type.
          • Existing answers are overwritten (upsert).
          • Run auto-completes once all required items are answered.
        """
        run = self.get_object()

        if run.status == "Completed":
            return Response(
                {"detail": "This checklist run is already completed."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if run.status == "Skipped":
            return Response(
                {"detail": "This checklist run has been skipped."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Normalise input to a list
        raw  = request.data if isinstance(request.data, list) else [request.data]
        ser  = SubmitResponseSerializer(data=raw, many=True)
        ser.is_valid(raise_exception=True)

        errors  = []
        saved   = []
        item_map = {
            str(i.pk): i
            for i in run.template.items.all()
        }

        for entry in ser.validated_data:
            item_id = str(entry["item"])
            item    = item_map.get(item_id)

            if not item:
                errors.append({
                    "item":   item_id,
                    "detail": f"Item {item_id} does not belong to this checklist.",
                })
                continue

            raw_value = entry.get("response_value") or ""
            try:
                normalised = item.validate_response(raw_value) if raw_value else None
            except DjangoValidationError as exc:
                errors.append({
                    "item":   item_id,
                    "detail": exc.messages[0] if exc.messages else str(exc),
                })
                continue

            resp, _ = ChecklistResponse.objects.update_or_create(
                run=run,
                item=item,
                defaults={
                    "responded_by":   request.user,
                    "response_value": normalised,
                    "notes":          entry.get("notes"),
                    "box_folder_url": entry.get("box_folder_url"),
                },
            )
            saved.append(resp)

        if errors and not saved:
            return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        # Refresh from DB (signal has already updated counters & status)
        run.refresh_from_db()

        response_data = ChecklistRunSerializer(run).data
        if errors:
            response_data["warnings"] = errors

        return Response(response_data, status=status.HTTP_200_OK)

    # ── POST /runs/{id}/items/{item_id}/box-folder/ ───────────────────────

    @action(
        detail=True, methods=["post"],
        url_path=r"items/(?P<item_id>[^/.]+)/box-folder",
    )
    def create_box_folder(self, request, pk=None, item_id=None):
        """
        Create (or reuse) a Box.com folder for this item's response and
        store its URL on box_folder_url.
        """
        run  = self.get_object()
        item = run.template.items.filter(pk=item_id).first()
        if not item:
            return Response(
                {"detail": f"Item {item_id} does not belong to this checklist."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        folder_name = f"{run.instance.reference_no} - {item.item_text}"[:255]
        try:
            _, folder_url = get_or_create_folder(folder_name)
        except BoxConfigError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except BoxAPIException as exc:
            return Response({"detail": f"Box API error: {exc}"}, status=status.HTTP_502_BAD_GATEWAY)

        resp, _ = ChecklistResponse.objects.get_or_create(
            run=run, item=item,
            defaults={"responded_by": request.user},
        )
        resp.box_folder_url = folder_url
        resp.save(update_fields=["box_folder_url"])

        return Response(ChecklistResponseSerializer(resp).data)

    # ── POST /runs/{id}/skip/ ─────────────────────────────────────────────

    @action(detail=True, methods=["post"])
    def skip(self, request, pk=None):
        """
        Mark a non-blocking run as Skipped.

        Only non-blocking checklists (blocks_advance=False) may be skipped.
        Blocking ones must be completed before the instance can advance.
        """
        run = self.get_object()
        try:
            run.mark_skipped()
        except DjangoValidationError as exc:
            return Response(
                {"detail": exc.messages[0] if exc.messages else str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(ChecklistRunSerializer(run).data)

    # ── POST /runs/{id}/reopen/ ───────────────────────────────────────────

    @action(
        detail=True, methods=["post"],
        permission_classes=[IsAdminUser],
    )
    def reopen(self, request, pk=None):
        """
        Reopen a Completed or Skipped run so users can amend answers.
        Admin only — triggers audit note in request data.
        """
        run = self.get_object()

        if run.status not in ("Completed", "Skipped"):
            return Response(
                {"detail": f"Cannot reopen a run with status '{run.status}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        run.status       = "InProgress"
        run.completed_at = None
        run.save(update_fields=["status", "completed_at"])

        return Response(ChecklistRunSerializer(run).data)

    # ── GET /runs/{id}/progress/ ──────────────────────────────────────────

    @action(detail=True, methods=["get"])
    def progress(self, request, pk=None):
        """
        Return a per-item completion breakdown for this run.

        Response shape:  ChecklistProgressSerializer
        """
        run      = self.get_object()
        items    = run.template.items.prefetch_related(
            "compliance_rules__compliance_rule",
        ).order_by("category", "display_order")
        answered = {
            r.item_id: r
            for r in run.responses.select_related("responded_by", "item")
        }

        breakdown = []
        for item in items:
            resp = answered.get(item.pk)
            is_answered = resp is not None and resp.response_value not in (None, "")
            breakdown.append({
                "item_id":        item.pk,
                "item_text":      item.item_text,
                "help_text":      item.help_text,
                "response_type":  item.response_type,
                "category":       item.category,
                "is_required":    item.is_required,
                "options":        item.options,
                "default_value":  item.default_value,
                "example_url":    item.example_url,
                "answered":       is_answered,
                "response_id":    resp.pk if resp else None,
                "response_value": resp.response_value if resp else None,
                "notes":          resp.notes          if resp else None,
                "box_folder_url": resp.box_folder_url if resp else None,
                "responded_by":   resp.responded_by.full_name if resp else None,
                "responded_at":   resp.responded_at   if resp else None,
                "compliance_rules": [
                    {
                        "checklist_item_compliance_rule_id": link.pk,
                        "rule_code": link.compliance_rule.code,
                        "rule_name": link.compliance_rule.name,
                    }
                    for link in item.compliance_rules.all()
                ],
            })

        from apps.compliance.models import ComplianceViolation

        violations = ComplianceViolation.objects.filter(
            checklist_response__run=run,
        ).select_related(
            "violation_severity_level",
            "checklist_item_compliance_rule__compliance_rule",
            "checklist_item_compliance_rule__checklist_item",
        )

        payload = {
            "run_id":                  run.pk,
            "status":                  run.status,
            "blocks_advance":          run.template.blocks_advance,
            "completion_pct":          run.completion_pct,
            "required_completion_pct": run.required_completion_pct,
            "total_items":             run.total_items,
            "answered_items":          run.answered_items,
            "total_required":          run.total_required,
            "answered_required":       run.answered_required,
            "items":                   breakdown,
            "violations":              violations,
        }
        serializer = ChecklistProgressSerializer(payload)
        return Response(serializer.data)

    # ── GET /runs/{id}/export/ ────────────────────────────────────────────

    @action(detail=True, methods=["get"])
    def export(self, request, pk=None):
        """
        Download a CSV of all responses in this run.

        Columns: item_order, item_text, response_type, is_required,
                 response_value, notes, responded_by, responded_at
        """
        run   = self.get_object()
        items = run.template.items.order_by("category", "display_order")
        answered = {
            r.item_id: r
            for r in run.responses.select_related("responded_by")
        }

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "category", "order", "item_text", "response_type", "required",
            "response_value", "notes", "responded_by", "responded_at",
        ])
        for item in items:
            resp = answered.get(item.pk)
            writer.writerow([
                item.category or "",
                item.display_order,
                item.item_text,
                item.response_type,
                "Yes" if item.is_required else "No",
                resp.response_value if resp else "",
                resp.notes          if resp else "",
                resp.responded_by.full_name if resp else "",
                resp.responded_at.isoformat() if resp else "",
            ])

        filename = f"checklist_run_{run.pk}_{run.instance.reference_no}.csv"
        response = StreamingHttpResponse(
            iter([output.getvalue()]),
            content_type="text/csv",
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
