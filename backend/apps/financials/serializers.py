from rest_framework import serializers
from .models import (
    Fund, Org, Account, Activity, Location,
    FoapalString, Program, Program, Transaction, TransactionSplit,
)


# ── Reference data ────────────────────────────────────────────────────────

class FundSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Fund
        fields = ["fund_id", "code", "title", "description", "fund_type",
                  "is_active", "effective_date", "expiry_date", "created_at", "updated_at"]
        read_only_fields = ["fund_id", "created_at", "updated_at"]


class FundListSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Fund
        fields = ["fund_id", "code", "title", "fund_type", "is_active"]


class OrgSerializer(serializers.ModelSerializer):
    parent_code = serializers.CharField(source="parent_org.code", read_only=True, default=None)

    class Meta:
        model  = Org
        fields = ["org_id", "code", "title", "description", "parent_org", "parent_code",
                  "is_active", "effective_date", "expiry_date", "created_at", "updated_at"]
        read_only_fields = ["org_id", "created_at", "updated_at"]


class OrgListSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Org
        fields = ["org_id", "code", "title", "parent_org", "is_active"]


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Account
        fields = ["account_id", "code", "title", "description", "account_type",
                  "normal_balance", "is_active", "effective_date", "expiry_date",
                  "created_at", "updated_at"]
        read_only_fields = ["account_id", "created_at", "updated_at"]


class AccountListSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Account
        fields = ["account_id", "code", "title", "account_type", "normal_balance", "is_active"]


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model  = Activity
        fields = ["activity_id", "code", "title", "description",
                  "is_active", "effective_date", "expiry_date", "created_at", "updated_at"]
        read_only_fields = ["activity_id", "created_at", "updated_at"]


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Location
        fields = ["locaton_id", "code", "title", "description", "building", "campus",
                  "is_active", "effective_date", "expiry_date", "created_at", "updated_at"]
        read_only_fields = ["locaton_id", "created_at", "updated_at"]


# ── FOAPAL string ─────────────────────────────────────────────────────────

class FoapalStringSerializer(serializers.ModelSerializer):
    fund_code     = serializers.CharField(source="fund.code",           read_only=True)
    org_code      = serializers.CharField(source="org.code",            read_only=True)
    account_code  = serializers.CharField(source="account.code",        read_only=True)
    program_code  = serializers.SerializerMethodField()
    activity_code = serializers.CharField(source="activity.code",       read_only=True, default=None)
    location_code = serializers.CharField(source="location.code",       read_only=True, default=None)
    display_code  = serializers.CharField(read_only=True)
    is_valid_today = serializers.BooleanField(read_only=True)

    class Meta:
        model  = FoapalString
        fields = [
            "foapalstring_id", "foapal_code", "display_code", "description",
            "fund", "fund_code",
            "org", "org_code",
            "account", "account_code",
            "program", "program_code",
            "activity", "activity_code",
            "location", "location_code",
            "is_active", "is_valid_today", "valid_from", "valid_to",
            "created_at", "updated_at",
        ]
        read_only_fields = ["foapalstring_id", "created_at", "updated_at"]

    def get_program_code(self, obj):
        if obj.program:
            return getattr(obj.program, "code", None)
        return None


class FoapalStringListSerializer(serializers.ModelSerializer):
    fund_code    = serializers.CharField(source="fund.code",    read_only=True)
    org_code     = serializers.CharField(source="org.code",     read_only=True)
    account_code = serializers.CharField(source="account.code", read_only=True)
    display_code = serializers.CharField(read_only=True)
    is_valid_today = serializers.BooleanField(read_only=True)

    class Meta:
        model  = FoapalString
        fields = ["foapalstring_id", "foapal_code", "display_code",
                  "fund_code", "org_code", "account_code",
                  "is_active", "is_valid_today"]


# ── Transaction split ─────────────────────────────────────────────────────

class TransactionSplitSerializer(serializers.ModelSerializer):
    foapal_code  = serializers.CharField(source="foapal_string.foapal_code", read_only=True)

    class Meta:
        model  = TransactionSplit
        fields = ["split_id", "transaction", "foapal_string", "foapal_code",
                  "amount", "percentage", "notes", "created_at"]
        read_only_fields = ["split_id", "created_at"]


# ── Transaction ───────────────────────────────────────────────────────────

class TransactionSerializer(serializers.ModelSerializer):
    foapal_code  = serializers.CharField(source="foapal_string.foapal_code", read_only=True)
    fund_code    = serializers.CharField(source="fund.code",    read_only=True, default=None)
    org_code     = serializers.CharField(source="org.code",     read_only=True, default=None)
    account_code = serializers.CharField(source="account.code", read_only=True, default=None)
    splits       = TransactionSplitSerializer(many=True, read_only=True)

    class Meta:
        model  = Transaction
        fields = [
            "id", "transaction_date", "posted_date", "reference_number",
            "description", "amount", "currency", "status",
            "foapal_string", "foapal_code",
            "fund", "fund_code",
            "org", "org_code",
            "account", "account_code",
            "program", "activity", "location",
            "source_system", "coded_by", "coded_at",
            "approved_by", "approved_at",
            "notes", "created_at", "updated_at",
            "splits",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class TransactionListSerializer(serializers.ModelSerializer):
    foapal_code  = serializers.CharField(source="foapal_string.foapal_code", read_only=True)
    fund_code    = serializers.CharField(source="fund.code",    read_only=True, default=None)
    org_code     = serializers.CharField(source="org.code",     read_only=True, default=None)
    account_code = serializers.CharField(source="account.code", read_only=True, default=None)

    class Meta:
        model  = Transaction
        fields = [
            "id", "transaction_date", "reference_number",
            "description", "amount", "currency", "status",
            "foapal_code", "fund_code", "org_code", "account_code",
            "source_system", "coded_by", "approved_by",
        ]


# ── Summary ───────────────────────────────────────────────────────────────

class FinancialsSummarySerializer(serializers.Serializer):
    total_transactions     = serializers.IntegerField()
    total_amount           = serializers.DecimalField(max_digits=20, decimal_places=2)
    pending_count          = serializers.IntegerField()
    pending_amount         = serializers.DecimalField(max_digits=20, decimal_places=2)
    approved_count         = serializers.IntegerField()
    approved_amount        = serializers.DecimalField(max_digits=20, decimal_places=2)
    posted_count           = serializers.IntegerField()
    posted_amount          = serializers.DecimalField(max_digits=20, decimal_places=2)
    voided_count           = serializers.IntegerField()
    status_breakdown       = serializers.ListField(child=serializers.DictField())
    top_funds              = serializers.ListField(child=serializers.DictField())
    top_accounts           = serializers.ListField(child=serializers.DictField())
    active_foapal_strings  = serializers.IntegerField()
    total_splits           = serializers.IntegerField()

class ProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Program
        fields = ["program_id", "code", "title", "description", "is_active",
                  "effective_date", "expiry_date", "created_at", "updated_at"]
        read_only_fields = ["program_id", "created_at", "updated_at"]

class ProgramListSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Program
        fields = ["program_id", "code", "title", "is_active"]