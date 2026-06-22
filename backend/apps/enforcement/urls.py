from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import FineCaseViewSet, FineInvoiceViewSet, FinePaymentViewSet, FineAppealViewSet, FineWaiverViewSet

router = DefaultRouter()
router.register(r"cases",    FineCaseViewSet,    basename="finecase")
router.register(r"invoices", FineInvoiceViewSet, basename="fineinvoice")
router.register(r"payments", FinePaymentViewSet, basename="finepayment")
router.register(r"appeals",  FineAppealViewSet,  basename="fineappeal")
router.register(r"waivers",  FineWaiverViewSet,  basename="finewaiver")

urlpatterns = [
    path("", include(router.urls)),
]
