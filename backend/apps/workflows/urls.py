from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    WorkflowDefinitionViewSet,
    WorkflowInstanceViewSet,
    WorkflowTaskViewSet,
    AuditLogViewSet,
)

router = DefaultRouter()
router.register("definitions", WorkflowDefinitionViewSet, basename="workflow-definitions")
router.register("instances",   WorkflowInstanceViewSet,   basename="workflow-instances")
router.register("tasks",       WorkflowTaskViewSet,        basename="workflow-tasks")
router.register("audit-logs",  AuditLogViewSet,            basename="audit-logs")

urlpatterns = [path("", include(router.urls))]
