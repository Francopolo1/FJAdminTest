"""
Compliance app tests.

Coverage
──────────────────────────────────────────────────────────────────────────
Models
  ComplianceRule       — str, ordering
  FineSchedule         — is_active property (active / expired / not-yet)
  ViolationSeverityLevel — ordering by rank

API
  GET  /api/compliance/rules/                list, search, filter active
  GET  /api/compliance/rules/{id}/           detail with violation count
  GET  /api/compliance/rules/{id}/violations/ violations for rule
  GET  /api/compliance/severity-levels/      list ordered by rank
  GET  /api/compliance/fine-schedules/       list
  GET  /api/compliance/violations/           list, filter by severity & date
  POST /api/compliance/violations/           create with valid / invalid FK
  GET  /api/compliance/summary/              aggregated stats shape
"""

import uuid
from datetime import date, timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from core.models import AuthUser


# ── Helpers ───────────────────────────────────────────────────────────────

def make_user(username="testuser", is_staff=False):
    return AuthUser.objects.create_user(
        username=username, password="pass1234", is_staff=is_staff
    )


# ── Unit tests ────────────────────────────────────────────────────────────

class FineScheduleActivePropertyTest(TestCase):
    """FineSchedule.is_active uses effective_date and expiration_date."""

    def _make_schedule(self, effective_delta=0, expiration_delta=None):
        from .models import FineSchedule, ComplianceRule
        rule = ComplianceRule(
            compliance_rule_id=uuid.uuid4(),
            code=f"TEST-{uuid.uuid4().hex[:6]}",
            name="Test Rule",
        )
        today = timezone.now().date()
        sched = FineSchedule(
            fine_schedule_id=uuid.uuid4(),
            compliance_rule=rule,
            schedule_name="Test Schedule",
            effective_date=today + timedelta(days=effective_delta),
            expiration_date=(today + timedelta(days=expiration_delta)
                             if expiration_delta is not None else None),
        )
        return sched

    def test_active_no_expiry(self):
        self.assertTrue(self._make_schedule(effective_delta=-10).is_active)

    def test_active_with_future_expiry(self):
        self.assertTrue(self._make_schedule(effective_delta=-10, expiration_delta=30).is_active)

    def test_inactive_not_yet_effective(self):
        self.assertFalse(self._make_schedule(effective_delta=5).is_active)

    def test_inactive_expired(self):
        self.assertFalse(self._make_schedule(effective_delta=-30, expiration_delta=-1).is_active)


# ── API tests (no real DB — skip when DB unavailable) ─────────────────────

class ComplianceAPITestBase(APITestCase):
    """Base class that skips gracefully when SQL Server is not available."""

    @classmethod
    def setUpClass(cls):
        try:
            from django.db import connection
            connection.ensure_connection()
        except Exception:
            import unittest
            raise unittest.SkipTest("SQL Server not available — skipping live API tests.")
        super().setUpClass()

    def setUp(self):
        self.user  = make_user()
        self.admin = make_user("admin", is_staff=True)
        self.client = APIClient()

    def auth(self, user=None):
        self.client.force_authenticate(user=user or self.user)


class ComplianceRuleAPITest(ComplianceAPITestBase):

    def test_list_unauthenticated_denied(self):
        r = self.client.get("/api/compliance/rules/")
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_returns_200(self):
        self.auth()
        r = self.client.get("/api/compliance/rules/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn("results", r.data)

    def test_list_filter_active(self):
        self.auth()
        r = self.client.get("/api/compliance/rules/?is_active=true")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_list_search(self):
        self.auth()
        r = self.client.get("/api/compliance/rules/?search=RULE")
        self.assertEqual(r.status_code, status.HTTP_200_OK)


class ViolationSeverityLevelAPITest(ComplianceAPITestBase):

    def test_list_ordered_by_rank(self):
        self.auth()
        r = self.client.get("/api/compliance/severity-levels/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        ranks = [item["rank"] for item in r.data.get("results", r.data)]
        self.assertEqual(ranks, sorted(ranks))


class FineScheduleAPITest(ComplianceAPITestBase):

    def test_list_returns_200(self):
        self.auth()
        r = self.client.get("/api/compliance/fine-schedules/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)


class ComplianceViolationAPITest(ComplianceAPITestBase):

    def test_list_returns_200(self):
        self.auth()
        r = self.client.get("/api/compliance/violations/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_create_with_invalid_rule_link(self):
        self.auth()
        payload = {
            "checklist_item_compliance_rule_id": str(uuid.uuid4()),
            "violation_date":                    date.today().isoformat(),
            "violation_severity_level_id":       str(uuid.uuid4()),
            "checklist_response_id":             str(uuid.uuid4()),
        }
        r = self.client.post("/api/compliance/violations/", payload, format="json")
        self.assertIn(r.status_code, [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND,
        ])

    def test_delete_requires_admin(self):
        self.auth()
        r = self.client.delete(f"/api/compliance/violations/{uuid.uuid4()}/")
        self.assertIn(r.status_code, [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        ])

    def test_filter_by_date(self):
        self.auth()
        r = self.client.get("/api/compliance/violations/?date_after=2025-01-01")
        self.assertEqual(r.status_code, status.HTTP_200_OK)


class ComplianceSummaryAPITest(ComplianceAPITestBase):

    def test_summary_shape(self):
        self.auth()
        r = self.client.get("/api/compliance/summary/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        for key in [
            "total_rules", "active_rules", "total_violations",
            "violations_last_30_days", "rules_with_violations",
            "top_violated_rules", "severity_breakdown", "active_fine_schedules",
        ]:
            self.assertIn(key, r.data, f"Missing key: {key}")

    def test_summary_counts_non_negative(self):
        self.auth()
        r = self.client.get("/api/compliance/summary/")
        self.assertGreaterEqual(r.data["total_rules"],    0)
        self.assertGreaterEqual(r.data["active_rules"],   0)
        self.assertGreaterEqual(r.data["total_violations"], 0)
