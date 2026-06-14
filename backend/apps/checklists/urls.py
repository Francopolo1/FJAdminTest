from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChecklistTemplateViewSet, ChecklistItemViewSet, ChecklistRunViewSet
 
router = DefaultRouter()
router.register("templates", ChecklistTemplateViewSet, basename="checklist-templates")
router.register("items",     ChecklistItemViewSet,     basename="checklist-items")
router.register("runs",      ChecklistRunViewSet,      basename="checklist-runs")
 
urlpatterns = [path("", include(router.urls))]
