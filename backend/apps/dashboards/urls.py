from django.urls import path
from . import views

app_name = "dashboards"

urlpatterns = [
    path("",                              views.MainDashboardView.as_view(),       name="main"),
    path("instances/",                    views.InstanceListView.as_view(),        name="instances"),
    path("instances/<uuid:instance_id>/", views.InstanceDetailView.as_view(),     name="instance_detail"),
    path("tasks/",                        views.TasksDashboardView.as_view(),      name="tasks"),
    path("checklists/",                   views.ChecklistsDashboardView.as_view(), name="checklists"),
    path("compliance/",                   views.ComplianceDashboardView.as_view(), name="compliance"),
    path("financials/",                   views.FinancialsDashboardView.as_view(), name="financials"),
    path("facilities/",                   views.FacilitiesDashboardView.as_view(), name="facilities"),
    path("api/stats/",                    views.api_stats,                         name="api_stats"),
]
