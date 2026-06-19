from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AuthUserViewSet,
    AuditLogViewSet,
    InspectorLandingAPIView,
    InspectorFacilityDetailAPIView,
    InspectorProgramFacilityProfileAPIView,
    InspectorStartActivityWorkflowAPIView,
    SupervisorLandingAPIView,
    SupervisorDirectReportProgramsAPIView,
    FacilityListAPIView,
    FacilityFilterOptionsAPIView,
    FacilityDetailAPIView,
    FacilityProgramFacilityProfileAPIView,
    FacilityStartActivityWorkflowAPIView,
    AddressValidationAPIView,
    ProgramFacilityTypeListAPIView,
    ProgramDistrictListAPIView,
    NextTrackingIdAPIView,
    FacilityCreateAPIView,
)

router = DefaultRouter()
router.register("users",     AuthUserViewSet, basename="users")
router.register("audit-logs", AuditLogViewSet, basename="audit-logs")
urlpatterns = [
    path("inspector/landing/", InspectorLandingAPIView.as_view(), name="inspector-landing"),
    path("inspector/facilities/<str:facility_id>/", InspectorFacilityDetailAPIView.as_view(), name="inspector-facility-detail"),
    path(
        "inspector/facilities/<str:facility_id>/activities/<str:activity_id>/start/",
        InspectorStartActivityWorkflowAPIView.as_view(),
        name="inspector-activity-start",
    ),
    path(
        "inspector/program-facilities/<str:program_facility_id>/profile/",
        InspectorProgramFacilityProfileAPIView.as_view(),
        name="inspector-program-facility-profile",
    ),
    path("supervisor/landing/", SupervisorLandingAPIView.as_view(), name="supervisor-landing"),
    path(
        "supervisor/direct-reports/<int:user_id>/programs/",
        SupervisorDirectReportProgramsAPIView.as_view(),
        name="supervisor-direct-report-programs",
    ),
    path("facilities/filters/", FacilityFilterOptionsAPIView.as_view(), name="facility-filters"),
    path("facilities/validate-address/", AddressValidationAPIView.as_view(), name="facility-validate-address"),
    path("facilities/program-facility-types/", ProgramFacilityTypeListAPIView.as_view(), name="facility-pft-list"),
    path("facilities/program-districts/", ProgramDistrictListAPIView.as_view(), name="facility-district-list"),
    path("facilities/next-tracking-id/", NextTrackingIdAPIView.as_view(), name="facility-next-tracking-id"),
    path("facilities/create/", FacilityCreateAPIView.as_view(), name="facility-create"),
    path(
        "facilities/program-facilities/<str:program_facility_id>/profile/",
        FacilityProgramFacilityProfileAPIView.as_view(),
        name="facility-program-facility-profile",
    ),
    path(
        "facilities/<str:facility_id>/activities/<str:activity_id>/start/",
        FacilityStartActivityWorkflowAPIView.as_view(),
        name="facility-activity-start",
    ),
    path("facilities/<str:facility_id>/", FacilityDetailAPIView.as_view(), name="facility-detail"),
    path("facilities/", FacilityListAPIView.as_view(), name="facility-list"),
    path("", include(router.urls)),
]
