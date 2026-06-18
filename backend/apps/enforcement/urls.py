from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import FineCaseViewSet, FineInvoiceViewSet, FinePaymentViewSet

router = DefaultRouter()
router.register(r"cases",    FineCaseViewSet,    basename="finecase")
router.register(r"invoices", FineInvoiceViewSet, basename="fineinvoice")
router.register(r"payments", FinePaymentViewSet, basename="finepayment")

urlpatterns = [
    path("", include(router.urls)),
]
