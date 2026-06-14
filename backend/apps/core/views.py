import json
import uuid

from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from apps.workflows.models import WorkflowDefinition
from apps.workflows.serializers import WorkflowInstanceListSerializer
from apps.workflows.services import generate_reference_no, submit_instance
from apps.financials.models import Program
from .models import (
    AuthUser, AuditLog, FacilityType, ProgramFacility, UserProfile, UserProgram, UserProgramDistrict,
)
from .serializers import (
    AuthUserSerializer,
    AuditLogSerializer,
    InspectorLandingSerializer,
    InspectorProgramSerializer,
    InspectorFacilityDetailSerializer,
    FacilityListItemSerializer,
    FacilityFilterOptionsSerializer,
    FacilityDetailSerializer,
    SupervisorLandingSerializer,
)


class AuthUserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset         = AuthUser.objects.all()
    serializer_class = AuthUserSerializer
    filter_backends  = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["is_active", "is_staff"]
    search_fields    = ["username", "first_name", "last_name", "email"]

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        return Response(AuthUserSerializer(request.user).data)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset         = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    filter_backends  = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["table_name", "action"]
    ordering         = ["-changed_at"]
    permission_classes = [IsAuthenticated]


def _assigned_program_district_ids(user):
    return list(
        UserProgramDistrict.objects.filter(user=user).values_list("program_district_id", flat=True)
    )


class InspectorLandingAPIView(APIView):
    """Role-specific landing data for inspectors: their assigned programs,
    program districts, and the program facilities within those districts."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        programs = [
            {"program_id": up.program.program_id, "code": up.program.code, "title": up.program.title}
            for up in UserProgram.objects.filter(user=user).select_related("program")
        ]

        districts_qs = (
            UserProgramDistrict.objects.filter(user=user)
            .select_related("program_district__program")
        )
        program_districts = [
            {
                "program_district_id": upd.program_district.program_district_id,
                "program_code":  upd.program_district.program.code if upd.program_district.program else "",
                "program_title": upd.program_district.program.title if upd.program_district.program else "",
                "district":      upd.program_district.district,
                "description":   upd.program_district.description,
            }
            for upd in districts_qs
        ]

        district_ids = _assigned_program_district_ids(user)
        facilities_qs = (
            ProgramFacility.objects.filter(program_district_id__in=district_ids)
            .select_related("facility", "program_district__program", "program_facility_type__facility_type")
        )
        program_facilities = [
            {
                "program_facility_id": pf.program_facility_id,
                "facility_id":         pf.facility_id,
                "facility_name":       pf.facility.name if pf.facility else None,
                "program_district_id": pf.program_district_id,
                "program_code":        pf.program_district.program.code if pf.program_district and pf.program_district.program else "",
                "district":            pf.program_district.district if pf.program_district else None,
                "facility_type":       (pf.program_facility_type.facility_type.description or "").strip() or None
                                        if pf.program_facility_type and pf.program_facility_type.facility_type else None,
                "license_number":      pf.license_number,
                "risk_assessment":     pf.risk_assessment,
                "activity_flag":       pf.activity_flag,
                "last_visit_date":     pf.last_visit_date,
                "next_visit_date":     pf.next_visit_date,
            }
            for pf in facilities_qs
        ]

        data = {
            "programs": programs,
            "program_districts": program_districts,
            "program_facilities": program_facilities,
        }
        return Response(InspectorLandingSerializer(data).data)


class SupervisorLandingAPIView(APIView):
    """Role-specific landing data for supervisors: their assigned programs
    and the profiles of users who report to them."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        assigned_programs = [
            {"program_id": up.program.program_id, "code": up.program.code, "title": up.program.title}
            for up in UserProgram.objects.filter(user=user).select_related("program")
        ]

        profile = getattr(user, "profile", None)
        reports_qs = (
            UserProfile.objects.filter(manager=profile).select_related("user")
            if profile else UserProfile.objects.none()
        )
        report_user_ids = [report.user_id for report in reports_qs]
        programs_by_user = {}
        for up in UserProgram.objects.filter(user_id__in=report_user_ids).select_related("program"):
            programs_by_user.setdefault(up.user_id, []).append(
                {"program_id": up.program.program_id, "code": up.program.code, "title": up.program.title}
            )

        direct_reports = [
            {
                "user_id":    report.user.id,
                "full_name":  report.user.full_name,
                "email":      report.user.email,
                "job_title":  report.job_title,
                "department": report.department,
                "role":       report.role,
                "is_active":  report.user.is_active,
                "assigned_programs": programs_by_user.get(report.user_id, []),
            }
            for report in reports_qs
        ]

        data = {
            "assigned_programs": assigned_programs,
            "direct_reports": direct_reports,
        }
        return Response(SupervisorLandingSerializer(data).data)


class SupervisorDirectReportProgramsAPIView(APIView):
    """Assign or remove a program for one of the requesting supervisor's
    direct reports. Only programs assigned to the supervisor themselves
    may be granted."""

    permission_classes = [IsAuthenticated]

    def _get_report_profile(self, request, user_id):
        profile = getattr(request.user, "profile", None)
        if not profile:
            raise NotFound("Direct report not found.")
        report_profile = UserProfile.objects.filter(user_id=user_id, manager=profile).first()
        if not report_profile:
            raise NotFound("Direct report not found.")
        return report_profile

    def post(self, request, user_id):
        report_profile = self._get_report_profile(request, user_id)

        program_id = request.data.get("program_id")
        if not program_id:
            return Response({"detail": "program_id is required."}, status=400)

        if not UserProgram.objects.filter(user=request.user, program_id=program_id).exists():
            return Response({"detail": "You can only assign programs that are assigned to you."}, status=400)

        UserProgram.objects.get_or_create(user_id=report_profile.user_id, program_id=program_id)

        return self._programs_response(report_profile.user_id)

    def delete(self, request, user_id):
        report_profile = self._get_report_profile(request, user_id)

        program_id = request.data.get("program_id")
        if not program_id:
            return Response({"detail": "program_id is required."}, status=400)

        UserProgram.objects.filter(user_id=report_profile.user_id, program_id=program_id).delete()

        return self._programs_response(report_profile.user_id)

    def _programs_response(self, user_id):
        assigned_programs = [
            {"program_id": up.program.program_id, "code": up.program.code, "title": up.program.title}
            for up in UserProgram.objects.filter(user_id=user_id).select_related("program")
        ]
        return Response(InspectorProgramSerializer(assigned_programs, many=True).data)


class InspectorFacilityDetailAPIView(APIView):
    """Detail view for a single facility: every program_facility assignment
    (within the inspector's assigned districts) and its workflow instances."""

    permission_classes = [IsAuthenticated]

    def get(self, request, facility_id):
        try:
            uuid.UUID(facility_id)
        except ValueError:
            raise NotFound("Facility not found in your assigned districts.")

        district_ids = _assigned_program_district_ids(request.user)

        assignments_qs = (
            ProgramFacility.objects.filter(facility_id=facility_id, program_district_id__in=district_ids)
            .select_related("facility__location", "program_district__program", "program_facility_type__facility_type")
            .prefetch_related(
                "instances__workflow",
                "instances__current_step",
                "program_facility_type__programfacilitytypeactivity_set__specialtracking",
                "program_facility_type__programfacilitytypeactivity_set__workflowdefinition_set",
            )
        )

        if not assignments_qs.exists():
            raise NotFound("Facility not found in your assigned districts.")

        facility = assignments_qs[0].facility
        assignments = []
        for pf in assignments_qs:
            assignments.append({
                "program_facility_id": pf.program_facility_id,
                "program_code":  pf.program_district.program.code if pf.program_district and pf.program_district.program else "",
                "district":      pf.program_district.district if pf.program_district else None,
                "facility_type": (pf.program_facility_type.facility_type.description or "").strip() or None
                                  if pf.program_facility_type and pf.program_facility_type.facility_type else None,
                "profile":            pf.profile,
                "license_number":     pf.license_number,
                "risk_assessment":    pf.risk_assessment,
                "activity_flag":      pf.activity_flag,
                "last_visit_date":    pf.last_visit_date,
                "next_visit_date":    pf.next_visit_date,
                "instances":          WorkflowInstanceListSerializer(
                    pf.instances.all().order_by("-started_at"), many=True
                ).data,
                "activities": [
                    {
                        "program_facility_type_activity_id": act.program_facility_type_activity_id,
                        "description": act.description,
                        "specialtracking": act.specialtracking.trackingdescription if act.specialtracking else None,
                        "workflows": [
                            {"workflow_id": wf.workflow_id, "name": wf.name, "category": wf.category}
                            for wf in act.workflowdefinition_set.filter(is_active=True)
                        ],
                    }
                    for act in (
                        pf.program_facility_type.programfacilitytypeactivity_set.all()
                        if pf.program_facility_type else []
                    )
                ],
            })

        location = facility.location
        data = {
            "facility_id":   facility.facility_id,
            "facility_name": facility.name,
            "location": {
                "address_line1": (location.addressline1 or "").strip() or None,
                "address_line2": (location.addressline2 or "").strip() or None,
                "city": (location.city or "").strip() or None,
                "state": (location.stateprovince or "").strip() or None,
                "postal_code": (location.postalcode or "").strip() or None,
                "city_state_zip": (location.citystatezip or "").strip() or None,
                "latitude": location.latitude,
                "longitude": location.longitude,
            } if location else None,
            "assignments":   assignments,
        }
        return Response(InspectorFacilityDetailSerializer(data).data)


class InspectorProgramFacilityProfileAPIView(APIView):
    """Update the `profile` JSON field of a program_facility assignment."""

    permission_classes = [IsAuthenticated]

    def patch(self, request, program_facility_id):
        try:
            uuid.UUID(program_facility_id)
        except ValueError:
            raise NotFound("Assignment not found in your assigned districts.")

        district_ids = _assigned_program_district_ids(request.user)

        program_facility = ProgramFacility.objects.filter(
            program_facility_id=program_facility_id,
            program_district_id__in=district_ids,
        ).first()
        if not program_facility:
            raise NotFound("Assignment not found in your assigned districts.")

        profile = request.data.get("profile")
        if not isinstance(profile, dict):
            return Response({"detail": "profile must be a JSON object."}, status=400)

        profile_json = json.dumps(profile)
        if len(profile_json) > 4000:
            return Response({"detail": "profile is too large."}, status=400)

        program_facility.profile = profile_json
        program_facility.save(update_fields=["profile"])

        return Response({"profile": program_facility.profile})


class InspectorStartActivityWorkflowAPIView(APIView):
    """Start a new workflow instance for a program_facility's activity."""

    permission_classes = [IsAuthenticated]

    def post(self, request, facility_id, activity_id):
        try:
            uuid.UUID(facility_id)
            uuid.UUID(activity_id)
        except ValueError:
            raise NotFound("Facility or activity not found in your assigned districts.")

        workflow_id = request.data.get("workflow_id")
        if not workflow_id:
            return Response({"detail": "workflow_id is required."}, status=400)

        district_ids = _assigned_program_district_ids(request.user)

        program_facility = (
            ProgramFacility.objects.filter(
                facility_id=facility_id,
                program_district_id__in=district_ids,
                program_facility_type__programfacilitytypeactivity__program_facility_type_activity_id=activity_id,
            )
            .first()
        )
        if not program_facility:
            raise NotFound("Facility or activity not found in your assigned districts.")

        try:
            workflow = WorkflowDefinition.objects.get(
                pk=workflow_id, is_active=True, program_facility_type_activity_id=activity_id,
            )
        except WorkflowDefinition.DoesNotExist:
            raise NotFound("Workflow not found for this activity.")

        try:
            instance = submit_instance(
                workflow_id=workflow.workflow_id,
                initiated_by=request.user,
                reference_no=generate_reference_no(workflow),
                program_facility=program_facility,
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=400)

        return Response(WorkflowInstanceListSerializer(instance).data, status=201)


# ── Facility directory (search / filter / detail) ───────────────────────────

class FacilityListAPIView(APIView):
    """Search all facilities, optionally filtered by program and/or facility type."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = (
            ProgramFacility.objects.select_related(
                "facility__location", "program_district__program",
                "program_facility_type__facility_type",
            )
        )

        search = request.query_params.get("search", "").strip()
        program_id = request.query_params.get("program")
        facility_type_id = request.query_params.get("facility_type")

        if search:
            qs = qs.filter(
                Q(facility__name__icontains=search) | Q(license_number__icontains=search)
            )
        if program_id:
            qs = qs.filter(program_district__program_id=program_id)
        if facility_type_id:
            qs = qs.filter(program_facility_type__facility_type_id=facility_type_id)

        qs = qs.order_by("facility__name")[:200]

        results = [
            {
                "facility_id":         pf.facility_id,
                "facility_name":       pf.facility.name if pf.facility else None,
                "program_facility_id": pf.program_facility_id,
                "program_id":          pf.program_district.program_id if pf.program_district else "",
                "program_code":        pf.program_district.program.code if pf.program_district and pf.program_district.program else "",
                "facility_type_id":    pf.program_facility_type.facility_type_id if pf.program_facility_type else None,
                "facility_type":       (pf.program_facility_type.facility_type.description or "").strip() or None
                                        if pf.program_facility_type and pf.program_facility_type.facility_type else None,
                "district":            pf.program_district.district if pf.program_district else None,
                "city":                (pf.facility.location.city or "").strip() or None
                                        if pf.facility and pf.facility.location else None,
                "state":               (pf.facility.location.stateprovince or "").strip() or None
                                        if pf.facility and pf.facility.location else None,
                "license_number":      pf.license_number,
                "activity_flag":       pf.activity_flag,
            }
            for pf in qs
        ]
        return Response(FacilityListItemSerializer(results, many=True).data)


class FacilityFilterOptionsAPIView(APIView):
    """Programs and facility types available for the facility search filters."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        programs = [
            {"program_id": p.program_id, "code": p.code, "title": p.title}
            for p in Program.objects.filter(is_active=True).order_by("title")
        ]
        facility_types = [
            {"facility_type_id": ft.facility_type_id, "code": ft.code, "description": ft.description}
            for ft in FacilityType.objects.order_by("description")
        ]
        data = {"programs": programs, "facility_types": facility_types}
        return Response(FacilityFilterOptionsSerializer(data).data)


class FacilityDetailAPIView(APIView):
    """General facility detail: every program_facility assignment for this facility."""

    permission_classes = [IsAuthenticated]

    def get(self, request, facility_id):
        try:
            uuid.UUID(facility_id)
        except ValueError:
            raise NotFound("Facility not found.")

        assignments_qs = (
            ProgramFacility.objects.filter(facility_id=facility_id)
            .select_related("facility__location", "program_district__program", "program_facility_type__facility_type")
            .prefetch_related(
                "instances__workflow",
                "instances__current_step",
                "program_facility_type__programfacilitytypeactivity_set__specialtracking",
                "program_facility_type__programfacilitytypeactivity_set__workflowdefinition_set",
            )
        )

        if not assignments_qs.exists():
            raise NotFound("Facility not found.")

        facility = assignments_qs[0].facility
        assignments = [
            {
                "program_facility_id": pf.program_facility_id,
                "program_code":  pf.program_district.program.code if pf.program_district and pf.program_district.program else "",
                "district":      pf.program_district.district if pf.program_district else None,
                "facility_type": (pf.program_facility_type.facility_type.description or "").strip() or None
                                  if pf.program_facility_type and pf.program_facility_type.facility_type else None,
                "profile":         pf.profile,
                "license_number":  pf.license_number,
                "risk_assessment": pf.risk_assessment,
                "activity_flag":   pf.activity_flag,
                "last_visit_date": pf.last_visit_date,
                "next_visit_date": pf.next_visit_date,
                "instances":       WorkflowInstanceListSerializer(
                    pf.instances.all().order_by("-started_at"), many=True
                ).data,
                "activities": [
                    {
                        "program_facility_type_activity_id": act.program_facility_type_activity_id,
                        "description": act.description,
                        "specialtracking": act.specialtracking.trackingdescription if act.specialtracking else None,
                        "workflows": [
                            {"workflow_id": wf.workflow_id, "name": wf.name, "category": wf.category}
                            for wf in act.workflowdefinition_set.filter(is_active=True)
                        ],
                    }
                    for act in (
                        pf.program_facility_type.programfacilitytypeactivity_set.all()
                        if pf.program_facility_type else []
                    )
                ],
            }
            for pf in assignments_qs
        ]

        location = facility.location
        data = {
            "facility_id":   facility.facility_id,
            "facility_name": facility.name,
            "location": {
                "address_line1": (location.addressline1 or "").strip() or None,
                "address_line2": (location.addressline2 or "").strip() or None,
                "city": (location.city or "").strip() or None,
                "state": (location.stateprovince or "").strip() or None,
                "postal_code": (location.postalcode or "").strip() or None,
                "city_state_zip": (location.citystatezip or "").strip() or None,
                "latitude": location.latitude,
                "longitude": location.longitude,
            } if location else None,
            "assignments": assignments,
        }
        return Response(FacilityDetailSerializer(data).data)


class FacilityProgramFacilityProfileAPIView(APIView):
    """Update the `profile` JSON field of a program_facility assignment (no district restriction)."""

    permission_classes = [IsAuthenticated]

    def patch(self, request, program_facility_id):
        try:
            uuid.UUID(program_facility_id)
        except ValueError:
            raise NotFound("Assignment not found.")

        program_facility = ProgramFacility.objects.filter(program_facility_id=program_facility_id).first()
        if not program_facility:
            raise NotFound("Assignment not found.")

        profile = request.data.get("profile")
        if not isinstance(profile, dict):
            return Response({"detail": "profile must be a JSON object."}, status=400)

        profile_json = json.dumps(profile)
        if len(profile_json) > 4000:
            return Response({"detail": "profile is too large."}, status=400)

        program_facility.profile = profile_json
        program_facility.save(update_fields=["profile"])

        return Response({"profile": program_facility.profile})


class FacilityStartActivityWorkflowAPIView(APIView):
    """Start a new workflow instance for a program_facility's activity (no district restriction)."""

    permission_classes = [IsAuthenticated]

    def post(self, request, facility_id, activity_id):
        try:
            uuid.UUID(facility_id)
            uuid.UUID(activity_id)
        except ValueError:
            raise NotFound("Facility or activity not found.")

        workflow_id = request.data.get("workflow_id")
        if not workflow_id:
            return Response({"detail": "workflow_id is required."}, status=400)

        program_facility = (
            ProgramFacility.objects.filter(
                facility_id=facility_id,
                program_facility_type__programfacilitytypeactivity__program_facility_type_activity_id=activity_id,
            )
            .first()
        )
        if not program_facility:
            raise NotFound("Facility or activity not found.")

        try:
            workflow = WorkflowDefinition.objects.get(
                pk=workflow_id, is_active=True, program_facility_type_activity_id=activity_id,
            )
        except WorkflowDefinition.DoesNotExist:
            raise NotFound("Workflow not found for this activity.")

        try:
            instance = submit_instance(
                workflow_id=workflow.workflow_id,
                initiated_by=request.user,
                reference_no=generate_reference_no(workflow),
                program_facility=program_facility,
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=400)

        return Response(WorkflowInstanceListSerializer(instance).data, status=201)