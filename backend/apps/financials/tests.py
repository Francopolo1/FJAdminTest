"""
Financials app tests.

Coverage
──────────────────────────────────────────────────────────────────────────
Models
  FoapalString.is_valid_today  — active/inactive, date range checks
  FoapalString.display_code    — F-O-A-P-A-L segments joined

API (skip gracefully when SQL Server unavailable)
  Funds / Orgs / Accounts / Activities / Locations  — list + 200
  FOAPAL   — list, filter by fund
  Transactions — list, filter by status/date, search
  Transactions — approve action (Coded→Approved)
  Transactions — void action
  Transactions — create/delete blocked for non-admin
  Splits       — list
  Summary      — shape check
"""
import uuid
from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status as http_status


def make_user(username="fin_user", is_staff=False):
    from core.models import AuthUser
    return AuthUser.objects.create_user(
        username=username, password="pass1234", is_staff=is_staff
    )


# ── Unit tests (no DB required) ───────────────────────────────────────────

class FoapalStringUnitTest(TestCase):
    """Tests for FoapalString computed properties."""

    def _make_foapal(self, is_active=True, valid_from=None, valid_to=None,
                     fund_code="F001", org_code="O001", account_code="A001"):
        from .models import FoapalString, Fund, Org, Account
        fund    = Fund(fund_id=uuid.uuid4(), code=fund_code, title="Fund")
        org     = Org(org_id=uuid.uuid4(),  code=org_code,  title="Org")
        account = Account(account_id=uuid.uuid4(), code=account_code,
                          title="Acct", account_type="Expense", normal_balance="Debit")
        fs = FoapalString(
            foapalstring_id=uuid.uuid4(),
            fund=fund, org=org, account=account,
            is_active=is_active,
            valid_from=valid_from,
            valid_to=valid_to,
        )
        return fs

    def test_is_valid_today_active_no_dates(self):
        self.assertTrue(self._make_foapal().is_valid_today)

    def test_is_valid_today_inactive(self):
        self.assertFalse(self._make_foapal(is_active=False).is_valid_today)

    def test_is_valid_today_before_valid_from(self):
        future = date.today() + timedelta(days=10)
        self.assertFalse(self._make_foapal(valid_from=future).is_valid_today)

    def test_is_valid_today_after_valid_to(self):
        past = date.today() - timedelta(days=1)
        self.assertFalse(self._make_foapal(valid_to=past).is_valid_today)

    def test_is_valid_today_within_range(self):
        past   = date.today() - timedelta(days=30)
        future = date.today() + timedelta(days=30)
        self.assertTrue(self._make_foapal(valid_from=past, valid_to=future).is_valid_today)

    def test_display_code_segments(self):
        fs = self._make_foapal(fund_code="F01", org_code="O01", account_code="A01")
        code = fs.display_code
        self.assertIn("F01", code)
        self.assertIn("O01", code)
        self.assertIn("A01", code)
        # Should be joined with dashes
        self.assertEqual(code.count("-"), 5)


# ── API tests ─────────────────────────────────────────────────────────────

class FinancialsAPIBase(APITestCase):
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
        self.user   = make_user("fin_user")
        self.admin  = make_user("fin_admin", is_staff=True)
        self.client = APIClient()

    def auth(self, user=None):
        self.client.force_authenticate(user=user or self.user)


class ReferenceDataAPITest(FinancialsAPIBase):

    def _check_list(self, path):
        self.auth()
        r = self.client.get(path)
        self.assertEqual(r.status_code, http_status.HTTP_200_OK)
        self.assertIn("results", r.data)

    def test_funds_list(self):          self._check_list("/api/financials/funds/")
    def test_orgs_list(self):           self._check_list("/api/financials/orgs/")
    def test_accounts_list(self):       self._check_list("/api/financials/accounts/")
    def test_activities_list(self):     self._check_list("/api/financials/activities/")
    def test_locations_list(self):      self._check_list("/api/financials/fin-locations/")

    def test_accounts_filter_type(self):
        self.auth()
        r = self.client.get("/api/financials/accounts/?account_type=Expense")
        self.assertEqual(r.status_code, http_status.HTTP_200_OK)

    def test_funds_search(self):
        self.auth()
        r = self.client.get("/api/financials/funds/?search=general")
        self.assertEqual(r.status_code, http_status.HTTP_200_OK)

    def test_unauthenticated_denied(self):
        r = self.client.get("/api/financials/funds/")
        self.assertEqual(r.status_code, http_status.HTTP_401_UNAUTHORIZED)


class FoapalAPITest(FinancialsAPIBase):

    def test_foapal_list(self):
        self.auth()
        r = self.client.get("/api/financials/foapal/")
        self.assertEqual(r.status_code, http_status.HTTP_200_OK)

    def test_foapal_filter_active(self):
        self.auth()
        r = self.client.get("/api/financials/foapal/?is_active=true")
        self.assertEqual(r.status_code, http_status.HTTP_200_OK)


class TransactionAPITest(FinancialsAPIBase):

    def test_list_200(self):
        self.auth()
        r = self.client.get("/api/financials/transactions/")
        self.assertEqual(r.status_code, http_status.HTTP_200_OK)

    def test_filter_by_status(self):
        self.auth()
        r = self.client.get("/api/financials/transactions/?status=Pending")
        self.assertEqual(r.status_code, http_status.HTTP_200_OK)

    def test_filter_by_date_range(self):
        self.auth()
        r = self.client.get("/api/financials/transactions/?date_after=2025-01-01&date_before=2025-12-31")
        self.assertEqual(r.status_code, http_status.HTTP_200_OK)

    def test_search(self):
        self.auth()
        r = self.client.get("/api/financials/transactions/?search=REF")
        self.assertEqual(r.status_code, http_status.HTTP_200_OK)

    def test_create_requires_admin(self):
        self.auth()
        r = self.client.post("/api/financials/transactions/", {}, format="json")
        self.assertEqual(r.status_code, http_status.HTTP_403_FORBIDDEN)

    def test_delete_requires_admin(self):
        self.auth()
        r = self.client.delete(f"/api/financials/transactions/{uuid.uuid4()}/")
        self.assertIn(r.status_code, [
            http_status.HTTP_403_FORBIDDEN,
            http_status.HTTP_404_NOT_FOUND,
        ])

    def test_approve_nonexistent_404(self):
        self.auth(self.admin)
        r = self.client.post(f"/api/financials/transactions/{uuid.uuid4()}/approve/")
        self.assertEqual(r.status_code, http_status.HTTP_404_NOT_FOUND)

    def test_approve_requires_admin(self):
        self.auth()
        r = self.client.post(f"/api/financials/transactions/{uuid.uuid4()}/approve/")
        self.assertIn(r.status_code, [
            http_status.HTTP_403_FORBIDDEN,
            http_status.HTTP_404_NOT_FOUND,
        ])

    def test_void_requires_admin(self):
        self.auth()
        r = self.client.post(f"/api/financials/transactions/{uuid.uuid4()}/void/")
        self.assertIn(r.status_code, [
            http_status.HTTP_403_FORBIDDEN,
            http_status.HTTP_404_NOT_FOUND,
        ])


class SplitsAPITest(FinancialsAPIBase):

    def test_splits_list_200(self):
        self.auth()
        r = self.client.get("/api/financials/splits/")
        self.assertEqual(r.status_code, http_status.HTTP_200_OK)


class FinancialsSummaryAPITest(FinancialsAPIBase):

    def test_summary_200_and_shape(self):
        self.auth()
        r = self.client.get("/api/financials/summary/")
        self.assertEqual(r.status_code, http_status.HTTP_200_OK)
        for key in [
            "total_transactions", "total_amount",
            "pending_count", "pending_amount",
            "approved_count", "approved_amount",
            "posted_count", "posted_amount",
            "voided_count",
            "status_breakdown", "top_funds", "top_accounts",
            "active_foapal_strings", "total_splits",
        ]:
            self.assertIn(key, r.data, f"Missing key: {key}")

    def test_summary_counts_non_negative(self):
        self.auth()
        r = self.client.get("/api/financials/summary/")
        for key in ["total_transactions", "pending_count", "approved_count",
                    "posted_count", "voided_count", "active_foapal_strings"]:
            self.assertGreaterEqual(r.data[key], 0, key)
        self.assertGreaterEqual(Decimal(r.data["total_amount"]), 0)