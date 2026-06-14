from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ComplianceRuleViewSet,
    ViolationSeverityLevelViewSet,
    FineScheduleViewSet,
    ChecklistItemComplianceRuleViewSet,
    ComplianceViolationViewSet,
    ComplianceSummaryView,
)

router = DefaultRouter()
router.register("rules",          ComplianceRuleViewSet,               basename="compliance-rules")
router.register("severity-levels",ViolationSeverityLevelViewSet,       basename="severity-levels")
router.register("fine-schedules", FineScheduleViewSet,                  basename="fine-schedules")
router.register("item-rules",     ChecklistItemComplianceRuleViewSet,   basename="item-rules")
router.register("violations",     ComplianceViolationViewSet,           basename="violations")

urlpatterns = [
    path("",         include(router.urls)),
    path("summary/", ComplianceSummaryView.as_view(), name="compliance-summary"),
]
