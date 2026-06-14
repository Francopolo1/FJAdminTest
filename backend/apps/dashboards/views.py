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
from django.db.models import Count, Q, Sum
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
            from django.db import connection
            with connection.cursor() as cur:
                cur.execute(
                    """
                    SELECT wal.action, wal.from_status, wal.to_status,
                           wal.notes, wal.logged_at,
                           au.first_name + ' ' + au.last_name AS actor_name
                    FROM   dbo.workflow_audit_log wal
                    JOIN   dbo.auth_user au ON au.id = wal.actor_id
                    WHERE  wal.instance_id = %s
                    ORDER  BY wal.logged_at DESC
                    """,
                    [str(instance_id)],
                )
                cols = [c[0] for c in cur.description]
                audit_logs = [dict(zip(cols, row)) for row in cur.fetchall()]
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

        context = {
            "tasks":           qs[:300],
            "stats":           stats,
            "now":             now,
            "priority_labels": PRIORITY_LABELS,
            "filter_status":   status_filter,
            "filter_search":   search,
            "overdue_only":    overdue_only,
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

        context = {
            "checklists":     qs[:300],
            "stats":          stats,
            "filter_status":  status_filter,
            "filter_search":  search,
            "blocking_only":  blocking_only,
        }
        return render(request, self.template_name, context)


# ── Compliance dashboard ──────────────────────────────────────────────────

@method_decorator(login_required, name="dispatch")
class ComplianceDashboardView(View):
    template_name = "dashboards/compliance.html"

    def get(self, request):
        violations = []
        rules      = []
        stats      = {}
        try:
            from django.db import connection
            with connection.cursor() as cur:
                # Recent violations
                cur.execute("""
                    SELECT TOP 50
                        cv.compliance_violation_id,
                        cv.violation_date,
                        cv.violation_description,
                        vsl.name  AS severity,
                        vsl.code  AS severity_code,
                        cr2.code  AS rule_code,
                        cr2.name  AS rule_name,
                        ci.item_text
                    FROM dbo.compliance_violations cv
                    JOIN dbo.violationseveritylevels vsl
                        ON vsl.violation_severity_level_id = cv.violation_severity_level_id
                    JOIN dbo.checklist_item_compliance_rules cicr
                        ON cicr.checklist_item_compliance_rule_id = cv.checklist_item_compliance_rule_id
                    JOIN dbo.compliance_rules cr2
                        ON cr2.compliance_rule_id = cicr.compliance_rule_id
                    LEFT JOIN dbo.checklist_item ci
                        ON ci.item_id = cicr.checklist_item_id
                    ORDER BY cv.violation_date DESC
                """)
                cols       = [c[0] for c in cur.description]
                violations = [dict(zip(cols, row)) for row in cur.fetchall()]

                # Rule stats
                cur.execute("""
                    SELECT cr2.code, cr2.name, cr2.is_active, COUNT(cv.compliance_violation_id) AS violation_count
                    FROM  dbo.compliance_rules cr2
                    LEFT JOIN dbo.checklist_item_compliance_rules cicr
                        ON cicr.compliance_rule_id = cr2.compliance_rule_id
                    LEFT JOIN dbo.compliance_violations cv
                        ON cv.checklist_item_compliance_rule_id = cicr.checklist_item_compliance_rule_id
                    GROUP BY cr2.code, cr2.name, cr2.is_active
                    ORDER BY violation_count DESC
                """)
                cols  = [c[0] for c in cur.description]
                rules = [dict(zip(cols, row)) for row in cur.fetchall()]

                stats = {
                    "total_violations": len(violations),
                    "active_rules":     sum(1 for r in rules if r["is_active"]),
                    "rules_with_violations": sum(1 for r in rules if r["violation_count"] > 0),
                }
        except Exception as e:
            stats["error"] = str(e)

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
        transactions = []
        foapal_rows  = []
        stats        = {}
        try:
            from django.db import connection
            with connection.cursor() as cur:
                # Transaction summary
                cur.execute("""
                    SELECT TOP 100
                        t.id, t.transaction_date, t.reference_number,
                        t.description, t.amount, t.currency, t.status,
                        t.source_system, t.coded_by, t.approved_by,
                        fs.foapal_code,
                        f.title  AS fund_title,
                        o.title  AS org_title,
                        a.title  AS account_title
                    FROM   dbo.transactions t
                    LEFT JOIN dbo.foapal_strings fs ON fs.foapalstring_id = t.foapal_string_id
                    LEFT JOIN dbo.funds          f  ON f.fund_id          = t.fund_id
                    LEFT JOIN dbo.orgs           o  ON o.org_id           = t.org_id
                    LEFT JOIN dbo.accounts       a  ON a.account_id       = t.account_id
                    ORDER BY t.transaction_date DESC
                """)
                cols         = [c[0] for c in cur.description]
                transactions = [dict(zip(cols, row)) for row in cur.fetchall()]

                # Status breakdown
                cur.execute("""
                    SELECT status, COUNT(*) AS cnt, SUM(amount) AS total_amount
                    FROM   dbo.transactions
                    GROUP  BY status
                """)
                status_breakdown = [
                    {"status": r[0], "count": r[1], "total": float(r[2] or 0)}
                    for r in cur.fetchall()
                ]

                # FOAPAL usage
                cur.execute("""
                    SELECT TOP 20
                        fs.foapal_code,
                        f.code AS fund_code, o.code AS org_code,
                        a.code AS acct_code, p.code AS prog_code,
                        COUNT(t.id) AS tx_count,
                        SUM(t.amount) AS total_amount
                    FROM   dbo.foapal_strings fs
                    LEFT JOIN dbo.transactions t ON t.foapal_string_id = fs.foapalstring_id
                    LEFT JOIN dbo.funds    f ON f.fund_id    = fs.fund_id
                    LEFT JOIN dbo.orgs     o ON o.org_id     = fs.org_id
                    LEFT JOIN dbo.accounts a ON a.account_id = fs.account_id
                    LEFT JOIN dbo.programs p ON p.program_id = fs.program_id
                    GROUP BY fs.foapal_code, f.code, o.code, a.code, p.code
                    ORDER BY tx_count DESC
                """)
                cols       = [c[0] for c in cur.description]
                foapal_rows = [dict(zip(cols, row)) for row in cur.fetchall()]

                stats = {
                    "total_transactions":    len(transactions),
                    "status_breakdown":      status_breakdown,
                    "pending_count":         sum(1 for t in transactions if t["status"] == "Pending"),
                    "total_amount_pending":  sum(float(t["amount"]) for t in transactions if t["status"] == "Pending"),
                }
        except Exception as e:
            stats["error"] = str(e)

        context = {
            "transactions":  transactions[:50],
            "foapal_rows":   foapal_rows,
            "stats":         stats,
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
            from django.db import connection
            with connection.cursor() as cur:
                # Facilities with location
                cur.execute("""
                    SELECT TOP 100
                        f.facility_id, f.name,
                        f.activity_status, f.active_date,
                        fl.addressline1, fl.city, fl.stateprovince,
                        fl.latitude, fl.longitude
                    FROM  dbo.facilities f
                    LEFT JOIN dbo.facility_locations fl ON fl.location_id = f.location_id
                    ORDER BY f.name
                """)
                cols       = [c[0] for c in cur.description]
                facilities = [dict(zip(cols, row)) for row in cur.fetchall()]

                # Programs with facility counts
                cur.execute("""
                    SELECT p.code, p.title, p.is_active,
                           COUNT(DISTINCT pf.program_facility_id) AS facility_count
                    FROM   dbo.programs p
                    LEFT JOIN dbo.program_facility_types pft ON pft.program_id = p.program_id
                    LEFT JOIN dbo.program_facilities     pf  ON pf.program_facility_type_id = pft.program_facility_type_id
                    GROUP BY p.code, p.title, p.is_active
                    ORDER BY facility_count DESC
                """)
                cols     = [c[0] for c in cur.description]
                programs = [dict(zip(cols, row)) for row in cur.fetchall()]

                stats = {
                    "total_facilities": len(facilities),
                    "active_facilities": sum(1 for f in facilities if f["activity_status"]),
                    "total_programs":   len(programs),
                    "active_programs":  sum(1 for p in programs if p["is_active"]),
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
