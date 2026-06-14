from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    FundViewSet, OrgViewSet, AccountViewSet,
    ActivityViewSet, LocationViewSet,
    FoapalStringViewSet,
    TransactionViewSet, TransactionSplitViewSet,
    FinancialsSummaryView,
)

router = DefaultRouter()
router.register("funds",        FundViewSet,             basename="funds")
router.register("orgs",         OrgViewSet,              basename="orgs")
router.register("accounts",     AccountViewSet,          basename="accounts")
router.register("activities",   ActivityViewSet,         basename="activities")
router.register("locations",    LocationViewSet,         basename="fin-locations")
router.register("foapal",       FoapalStringViewSet,     basename="foapal")
router.register("transactions", TransactionViewSet,      basename="transactions")
router.register("splits",       TransactionSplitViewSet, basename="splits")

urlpatterns = [
    path("",         include(router.urls)),
    path("summary/", FinancialsSummaryView.as_view(), name="financials-summary"),
]
