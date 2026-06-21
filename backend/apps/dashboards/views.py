"""
Dashboard views — server-rendered HTML.

Pages
──────────────────────────────────────────────────────────────
/dashboard/                     → Main dashboard  (stats + charts)
/dashboard/instances/           → Instance list  (filterable table)
/dashboard/instances/<id>/      → Instance detail  (tabs: tasks, checklists, audit)
/dashboard/tasks/               → Pending tasks  (SLA countdown table)
/dashboard/checklists/          → Checklist progress  (progress bars)
/dashboard/compliance/          → Compliance violations summary
/dashboard/financials/          → Transactions + FOAPAL overview
/dashboard/facilities/          → Facilities / programs overview
/dashboard/api/stats/           → JSON endpoint for HTMX chart refreshes
"""

import json
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum, DecimalField
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View

from .models import VWInstanceDashboard, VWPendingTask, VWChecklistProgress


# ── Helpers ───────────────────────────────────────────────────────────────

def _safe_int(val, default=0):
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


PRIORITY_LABELS = {1: "Low", 2: "Normal", 3: "High", 4: "Urgent"}
STATUS_COLORS   = {
    "Draft":      "#9AA1AE",
    "InProgress": "#2563EB",
    "Approved":   "#10B981",
    "Rejected":   "#F43F5E",
    "Cancelled":  "#9AA1AE",
    "OnHold":     "#F59E0B",
}


# ── Main dashboard ────────────────────────────────────────────────────────

#@method_decorator(login_required, name="dispatch")
class MainDashboardView(View):
    template_name = "dashboards/main.html"

    def get(self, request):
        instances = VWInstanceDashboard.objects.all()

        # ── Stat cards ───────────────────────────────────────────────────
        stats = {
            "total":       instances.count(),
            "in_progress": instances.filter(status="InProgress").count(),
            "approved":    instances.filter(status="Approved").count(),
            "rejected":    instances.filter(status="Rejected").count(),
            "on_hold":     instances.filter(status="OnHold").count(),
        }

        # ── Status distribution (for pie chart) ──────────────────────────
        status_dist_qs = (
            instances
            .values("status")
            .annotate(count=Count("instance_id"))
            .order_by("status")
        )
        status_dist = [
            {
                "label": s["status"],
                "count": s["count"],
                "color": STATUS_COLORS.get(s["status"], "#9AA1AE"),
            }
            for s in status_dist_qs
        ]

        # ── Priority distribution (for bar chart) ────────────────────────
        priority_dist_qs = (
            instances
            .values("priority")
            .annotate(count=Count("instance_id"))
            .order_by("priority")
        )
        priority_dist = [
            {
                "label": PRIORITY_LABELS.get(p["priority"], f"P{p['priority']}"),
                "count": p["count"],
            }
            for p in priority_dist_qs
        ]

        # ── Category distribution ─────────────────────────────────────────
        category_dist = (
            instances
            .exclude(category__isnull=True)
            .exclude(category="")
            .values("category")
            .annotate(count=Count("instance_id"))
            .order_by("-count")[:8]
        )

        # ── Pending tasks ─────────────────────────────────────────────────
        pending_tasks  = VWPendingTask.objects.all()
        overdue_count  = pending_tasks.filter(
            due_date__lt=timezone.now(),
            status__in=["Pending", "InProgress"],
        ).count()
        task_stats = {
            "total":   pending_tasks.count(),
            "overdue": overdue_count,
            "pending": pending_tasks.filter(status="Pending").count(),
        }

        # ── Checklist progress summary ────────────────────────────────────
        checklists = VWChecklistProgress.objects.all()
        checklist_stats = {
            "blocking_incomplete": checklists.filter(
                blocks_advance=True,
            ).exclude(run_status__in=["Completed", "Skipped"]).count(),
            "completed": checklists.filter(run_status="Completed").count(),
            "total":     checklists.count(),
        }

        # ── Recent instances (last 10) ────────────────────────────────────
        recent = instances[:10]

        # ── Overdue tasks ─────────────────────────────────────────────────
        overdue_tasks = pending_tasks.filter(
            due_date__lt=timezone.now(),
            status__in=["Pending", "InProgress"],
        ).order_by("due_date")[:8]

        context = {
            "stats":           stats,
            "task_stats":      task_stats,
            "checklist_stats": checklist_stats,
            "status_dist":     status_dist,
            "priority_dist":   priority_dist,
            "category_dist":   category_dist,
            "recent":          recent,
            "overdue_tasks":   overdue_tasks,
            "status_dist_json":  json.dumps(status_dist),
            "priority_dist_json": json.dumps(priority_dist),
            "now":             timezone.now(),
        }
        return render(request, self.template_name, context)


# ── Instance list ─────────────────────────────────────────────────────────

@method_decorator(login_required, name="dispatch")
class InstanceListView(View):
    template_name = "dashboards/instances.html"

    def get(self, request):
        qs = VWInstanceDashboard.objects.all()

        # Filters
        status   = request.GET.get("status",   "")
        priority = request.GET.get("priority", "")
        category = request.GET.get("category", "")
        search   = request.GET.get("search",   "")

        if status:
            qs = qs.filter(status=status)
        if priority:
            qs = qs.filter(priority=int(priority))
        if category:
            qs = qs.filter(category=category)
        if search:
            qs = qs.filter(
                Q(reference_no__icontains=search) |
                Q(workflow_name__icontains=search) |
                Q(initiated_by__icontains=search)
            )

        # Distinct value lists for filter dropdowns
        all_qs = VWInstanceDashboard.objects.all()
        statuses   = sorted(set(all_qs.values_list("status",   flat=True)))
        categories = sorted(set(
            v for v in all_qs.values_list("category", flat=True) if v
        ))

        # Chart distributions (reflect active filters)
        status_dist = [
            {"label": s["status"], "count": s["count"],
             "color": STATUS_COLORS.get(s["status"], "#9AA1AE")}
            for s in qs.values("status").annotate(count=Count("instance_id")).order_by("status")
        ]
        priority_dist = [
            {"label": PRIORITY_LABELS.get(p["priority"], f"P{p['priority']}"), "count": p["count"]}
            for p in qs.values("priority").annotate(count=Count("instance_id")).order_by("priority")
        ]
        category_dist = list(
            qs.exclude(category__isnull=True).exclude(category="")
            .values("category").annotate(count=Count("instance_id")).order_by("-count")[:8]
        )

        context = {
            "instances":   qs[:200],
            "total":       qs.count(),
            "statuses":    statuses,
            "categories":  categories,
            "filter_status":   status,
            "filter_priority": priority,
            "filter_category": category,
            "filter_search":   search,
            "priority_labels": PRIORITY_LABELS,
            "status_colors":   STATUS_COLORS,
            "status_dist_json":   json.dumps(status_dist),
            "priority_dist_json": json.dumps(priority_dist),
            "category_dist":      category_dist,
        }
        return render(request, self.template_name, context)


# ── Instance detail ───────────────────────────────────────────────────────

@method_decorator(login_required, name="dispatch")
class InstanceDetailView(View):
    template_name = "dashboards/instance_detail.html"

    def get(self, request, instance_id):
        instance = get_object_or_404(VWInstanceDashboard, instance_id=instance_id)

        # Tasks for this instance
        tasks = VWPendingTask.objects.filter(reference_no=instance.reference_no)

        # Checklist progress for this instance
        checklists = VWChecklistProgress.objects.filter(instance_id=instance_id)

        # Audit log from workflow_audit_log table
        audit_logs = []
        try:
            from apps.workflows.models import WorkflowAuditLog
            audit_logs = list(
                WorkflowAuditLog.objects
                .filter(instance_id=instance_id)
                .select_related("actor")
                .order_by("-logged_at")
                .values("action", "from_status", "to_status", "notes", "logged_at",
                        "actor__first_name", "actor__last_name")
            )
            for log in audit_logs:
                log["actor_name"] = f"{log.pop('actor__first_name', '')} {log.pop('actor__last_name', '')}".strip()
        except Exception:
            pass

        context = {
            "instance":   instance,
            "tasks":      tasks,
            "checklists": checklists,
            "audit_logs": audit_logs,
            "priority_label": PRIORITY_LABELS.get(instance.priority, "—"),
            "now":        timezone.now(),
        }
        return render(request, self.template_name, context)


# ── Tasks dashboard ───────────────────────────────────────────────────────

@method_decorator(login_required, name="dispatch")
class TasksDashboardView(View):
    template_name = "dashboards/tasks.html"

    def get(self, request):
        now = timezone.now()
        qs  = VWPendingTask.objects.all()

        status_filter = request.GET.get("status", "")
        search        = request.GET.get("search", "")
        overdue_only  = request.GET.get("overdue_only", "") == "1"

        if status_filter:
            qs = qs.filter(status=status_filter)
        if search:
            qs = qs.filter(
                Q(reference_no__icontains=search) |
                Q(assigned_to__icontains=search) |
                Q(step_name__icontains=search)
            )
        if overdue_only:
            qs = qs.filter(due_date__lt=now)

        stats = {
            "total":      qs.count(),
            "overdue":    qs.filter(due_date__lt=now).count(),
            "no_due":     qs.filter(due_date__isnull=True).count(),
            "pending":    qs.filter(status="Pending").count(),
            "in_progress":qs.filter(status="InProgress").count(),
        }

        TASK_STATUS_COLORS = {
            "Pending":    "#F59E0B",
            "InProgress": "#2563EB",
            "Overdue":    "#E11D48",
        }
        status_dist = [
            {"label": s["status"], "count": s["count"],
             "color": TASK_STATUS_COLORS.get(s["status"], "#9AA1AE")}
            for s in qs.values("status").annotate(count=Count("task_id")).order_by("status")
        ]
        priority_dist = [
            {"label": PRIORITY_LABELS.get(p["priority"], f"P{p['priority']}"), "count": p["count"]}
            for p in qs.values("priority").annotate(count=Count("task_id")).order_by("priority")
        ]

        context = {
            "tasks":              qs[:300],
            "stats":              stats,
            "now":                now,
            "priority_labels":    PRIORITY_LABELS,
            "filter_status":      status_filter,
            "filter_search":      search,
            "overdue_only":       overdue_only,
            "status_dist_json":   json.dumps(status_dist),
            "priority_dist_json": json.dumps(priority_dist),
        }
        return render(request, self.template_name, context)


# ── Checklists dashboard ──────────────────────────────────────────────────

@method_decorator(login_required, name="dispatch")
class ChecklistsDashboardView(View):
    template_name = "dashboards/checklists.html"

    def get(self, request):
        qs = VWChecklistProgress.objects.all()

        status_filter = request.GET.get("status",  "")
        search        = request.GET.get("search",  "")
        blocking_only = request.GET.get("blocking_only", "") == "1"

        if status_filter:
            qs = qs.filter(run_status=status_filter)
        if search:
            qs = qs.filter(
                Q(reference_no__icontains=search) |
                Q(checklist_title__icontains=search)
            )
        if blocking_only:
            qs = qs.filter(blocks_advance=True)

        all_qs = VWChecklistProgress.objects.all()
        stats = {
            "total":                all_qs.count(),
            "completed":            all_qs.filter(run_status="Completed").count(),
            "in_progress":          all_qs.filter(run_status="InProgress").count(),
            "not_started":          all_qs.filter(run_status="NotStarted").count(),
            "blocking_incomplete":  all_qs.filter(blocks_advance=True).exclude(
                                        run_status__in=["Completed", "Skipped"]
                                    ).count(),
        }

        CHECKLIST_STATUS_COLORS = {
            "Completed":  "#10B981",
            "InProgress": "#2563EB",
            "NotStarted": "#ADB5BD",
            "Skipped":    "#F59E0B",
        }
        status_dist = [
            {"label": s["run_status"], "count": s["count"],
             "color": CHECKLIST_STATUS_COLORS.get(s["run_status"], "#9AA1AE")}
            for s in all_qs.values("run_status").annotate(count=Count("instance_id")).order_by("run_status")
        ]

        context = {
            "checklists":        qs[:300],
            "stats":             stats,
            "filter_status":     status_filter,
            "filter_search":     search,
            "blocking_only":     blocking_only,
            "status_dist_json":  json.dumps(status_dist),
        }
        return render(request, self.template_name, context)


# ── Compliance dashboard ──────────────────────────────────────────────────

@method_decorator(login_required, name="dispatch")
class ComplianceDashboardView(View):
    template_name = "dashboards/compliance.html"

    def get(self, request):
        from apps.compliance.models import (
            ComplianceViolation, ComplianceRule, ChecklistItemComplianceRule,
        )

        violations_qs = (
            ComplianceViolation.objects
            .select_related(
                "violation_severity_level",
                "checklist_item_compliance_rule__compliance_rule",
                "checklist_item_compliance_rule__checklist_item",
            )
            .order_by("-violation_date")[:50]
        )
        violations = [
            {
                "compliance_violation_id": v.compliance_violation_id,
                "violation_date":          v.violation_date,
                "violation_description":   v.violation_description,
                "severity":                v.violation_severity_level.name,
                "severity_code":           v.violation_severity_level.code,
                "rule_code":               v.checklist_item_compliance_rule.compliance_rule.code,
                "rule_name":               v.checklist_item_compliance_rule.compliance_rule.name,
                "item_text":               getattr(v.checklist_item_compliance_rule.checklist_item, "item_text", None),
            }
            for v in violations_qs
        ]

        rules_qs = (
            ComplianceRule.objects
            .annotate(violation_count=Count("checklist_item_links__violations"))
            .order_by("-violation_count")
            .values("code", "name", "is_active", "violation_count")
        )
        rules = list(rules_qs)

        stats = {
            "total_violations":      ComplianceViolation.objects.count(),
            "active_rules":          ComplianceRule.objects.filter(is_active=True).count(),
            "rules_with_violations": sum(1 for r in rules if r["violation_count"] > 0),
        }

        context = {
            "violations": violations,
            "rules":      rules,
            "stats":      stats,
        }
        return render(request, self.template_name, context)


# ── Financials dashboard ──────────────────────────────────────────────────

@method_decorator(login_required, name="dispatch")
class FinancialsDashboardView(View):
    template_name = "dashboards/financials.html"

    def get(self, request):
        from apps.financials.models import Transaction, FoapalString

        transactions_qs = (
            Transaction.objects
            .select_related("foapal_string", "foapal_string__fund", "foapal_string__org", "foapal_string__account")
            .order_by("-transaction_date")[:100]
        )
        transactions = list(transactions_qs.values(
            "id", "transaction_date", "reference_number", "description",
            "amount", "currency", "status", "source_system", "coded_by", "approved_by",
            "foapal_string__foapal_code",
            "foapal_string__fund__title",
            "foapal_string__org__title",
            "foapal_string__account__title",
        ))
        for t in transactions:
            t["foapal_code"]   = t.pop("foapal_string__foapal_code", None)
            t["fund_title"]    = t.pop("foapal_string__fund__title", None)
            t["org_title"]     = t.pop("foapal_string__org__title", None)
            t["account_title"] = t.pop("foapal_string__account__title", None)

        status_breakdown = list(
            Transaction.objects
            .values("status")
            .annotate(count=Count("id"), total_amount=Sum("amount"))
            .order_by("status")
        )
        for row in status_breakdown:
            row["total"] = float(row.pop("total_amount") or 0)

        foapal_rows = list(
            FoapalString.objects
            .annotate(tx_count=Count("transactions"), total_amount=Sum("transactions__amount"))
            .select_related("fund", "org", "account", "program")
            .order_by("-tx_count")[:20]
            .values(
                "foapal_code",
                "fund__code", "org__code", "account__code", "program__code",
                "tx_count", "total_amount",
            )
        )
        for row in foapal_rows:
            row["fund_code"]  = row.pop("fund__code", None)
            row["org_code"]   = row.pop("org__code", None)
            row["acct_code"]  = row.pop("account__code", None)
            row["prog_code"]  = row.pop("program__code", None)
            row["total_amount"] = float(row["total_amount"] or 0)

        stats = {
            "total_transactions":   Transaction.objects.count(),
            "status_breakdown":     status_breakdown,
            "pending_count":        Transaction.objects.filter(status="Pending").count(),
            "total_amount_pending": float(
                Transaction.objects.filter(status="Pending").aggregate(s=Sum("amount"))["s"] or 0
            ),
        }

        context = {
            "transactions": transactions[:50],
            "foapal_rows":  foapal_rows,
            "stats":        stats,
        }
        return render(request, self.template_name, context)


# ── Facilities dashboard ──────────────────────────────────────────────────

@method_decorator(login_required, name="dispatch")
class FacilitiesDashboardView(View):
    template_name = "dashboards/facilities.html"

    def get(self, request):
        facilities = []
        programs   = []
        stats      = {}
        try:
            from apps.core.models import Facility
            from apps.financials.models import Program

            facilities = list(
                Facility.objects
                .select_related("location")
                .order_by("name")[:100]
                .values(
                    "facility_id", "name", "activity_status", "active_date",
                    "location__addressline1", "location__city", "location__stateprovince",
                    "location__latitude", "location__longitude",
                )
            )
            for f in facilities:
                f["addressline1"]  = f.pop("location__addressline1", None)
                f["city"]          = f.pop("location__city", None)
                f["stateprovince"] = f.pop("location__stateprovince", None)
                f["latitude"]      = f.pop("location__latitude", None)
                f["longitude"]     = f.pop("location__longitude", None)

            # Program → ProgramFacilityType (reverse) → ProgramFacility (reverse)
            programs = list(
                Program.objects
                .annotate(facility_count=Count("programfacilitytype__programfacility", distinct=True))
                .order_by("-facility_count")
                .values("code", "title", "is_active", "facility_count")
            )

            stats = {
                "total_facilities":  Facility.objects.count(),
                "active_facilities": Facility.objects.filter(activity_status=True).count(),
                "total_programs":    Program.objects.count(),
                "active_programs":   Program.objects.filter(is_active=True).count(),
            }
        except Exception as e:
            stats["error"] = str(e)

        context = {
            "facilities": facilities,
            "programs":   programs,
            "stats":      stats,
        }
        return render(request, self.template_name, context)


# ── JSON stats endpoint (for live chart refresh) ──────────────────────────

@login_required
def api_stats(request):
    instances = VWInstanceDashboard.objects.all()
    tasks     = VWPendingTask.objects.all()
    now       = timezone.now()

    status_dist = list(
        instances.values("status").annotate(count=Count("instance_id")).order_by("status")
    )
    return JsonResponse({
        "instances": {
            "total":       instances.count(),
            "in_progress": instances.filter(status="InProgress").count(),
            "approved":    instances.filter(status="Approved").count(),
        },
        "tasks": {
            "total":   tasks.count(),
            "overdue": tasks.filter(due_date__lt=now).count(),
        },
        "status_dist": status_dist,
        "timestamp":   now.isoformat(),
    })
