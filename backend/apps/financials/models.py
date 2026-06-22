"""
Financials app models — all unmanaged (managed=False).

Tables mapped:
  funds               → Fund
  orgs                → Org
  accounts            → Account
  programs            → Program  
  activities          → Activity
  locations           → Location  (FOAPAL location codes, NOT facility_locations)
  foapal_strings      → FoapalString
  transactions        → Transaction
  transaction_splits  → TransactionSplit
"""
import uuid
from django.db import models
from apps.core.db_fields import GUIDField, new_guid_str


class Fund(models.Model):
    """dbo.funds"""
    fund_id        = GUIDField(primary_key=True, default=uuid.uuid4)
    code           = models.CharField(max_length=10, unique=True)
    title          = models.CharField(max_length=120)
    description    = models.TextField(null=True, blank=True)
    fund_type      = models.CharField(max_length=50, null=True, blank=True)
    is_active      = models.BooleanField(default=True)
    effective_date = models.DateField(null=True, blank=True)
    expiry_date    = models.DateField(null=True, blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "funds"
        managed = True
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.title}"


class Org(models.Model):
    """dbo.orgs"""
    org_id         = GUIDField(primary_key=True, default=uuid.uuid4)
    code           = models.CharField(max_length=10, unique=True)
    title          = models.CharField(max_length=120)
    description    = models.TextField(null=True, blank=True)
    parent_org     = models.ForeignKey(
        "self", null=True, blank=True,
        on_delete=models.SET_NULL,
        db_column="parent_org_id",
        related_name="children",
    )
    is_active      = models.BooleanField(default=True)
    effective_date = models.DateField(null=True, blank=True)
    expiry_date    = models.DateField(null=True, blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "orgs"
        managed = True
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.title}"


class Account(models.Model):
    """dbo.accounts"""
    NORMAL_BALANCE_CHOICES = [("Debit", "Debit"), ("Credit", "Credit")]

    account_id     = GUIDField(primary_key=True, default=uuid.uuid4)
    code           = models.CharField(max_length=10, unique=True)
    title          = models.CharField(max_length=120)
    description    = models.TextField(null=True, blank=True)
    account_type   = models.CharField(max_length=30)
    normal_balance = models.CharField(max_length=6, choices=NORMAL_BALANCE_CHOICES)
    is_active      = models.BooleanField(default=True)
    effective_date = models.DateField(null=True, blank=True)
    expiry_date    = models.DateField(null=True, blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "accounts"
        managed = True
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.title}"

class Program(models.Model):
    program_id = models.CharField(primary_key=True, max_length=36, default=new_guid_str)
    code = models.CharField(unique=True, max_length=10)
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField()
    effective_date = models.DateField(blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'programs'

    def __str__(self):
        return f"{self.code} — {self.title}"

class Activity(models.Model):
    """dbo.activities"""
    activity_id    = GUIDField(primary_key=True, default=uuid.uuid4)
    code           = models.CharField(max_length=10, unique=True)
    title          = models.CharField(max_length=120)
    description    = models.TextField(null=True, blank=True)
    is_active      = models.BooleanField(default=True)
    effective_date = models.DateField(null=True, blank=True)
    expiry_date    = models.DateField(null=True, blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "activities"
        managed = True
        ordering = ["code"]
        verbose_name_plural = "activities"
    def __str__(self):
        return f"{self.code} — {self.title}"
    

class Location(models.Model):
    """dbo.locations  (FOAPAL location codes — NOT facility_locations)"""
    locaton_id     = GUIDField(primary_key=True, default=uuid.uuid4,
                                      db_column="locaton_id")   # typo preserved from schema
    code           = models.CharField(max_length=10, unique=True)
    title          = models.CharField(max_length=120)
    description    = models.TextField(null=True, blank=True)
    building       = models.CharField(max_length=80, null=True, blank=True)
    campus         = models.CharField(max_length=80, null=True, blank=True)
    is_active      = models.BooleanField(default=True)
    effective_date = models.DateField(null=True, blank=True)
    expiry_date    = models.DateField(null=True, blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "locations"
        managed = True
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.title}"


class FoapalString(models.Model):
    """dbo.foapal_strings — Fund-Org-Account-Program-Activity-Location composite."""
    foapalstring_id = GUIDField(primary_key=True, default=uuid.uuid4)
    fund            = models.ForeignKey(Fund,     on_delete=models.PROTECT,
                                        db_column="fund_id",     related_name="foapal_strings")
    org             = models.ForeignKey(Org,      on_delete=models.PROTECT,
                                        db_column="org_id",      related_name="foapal_strings")
    account         = models.ForeignKey(Account,  on_delete=models.PROTECT,
                                        db_column="account_id",  related_name="foapal_strings")
    program         = models.ForeignKey(
        Program, null=True, blank=True,
        on_delete=models.SET_NULL, db_column="program_id", related_name="foapal_strings",
    )
    activity        = models.ForeignKey(Activity, null=True, blank=True,
                                        on_delete=models.SET_NULL,
                                        db_column="activity_id", related_name="foapal_strings")
    location        = models.ForeignKey(Location, null=True, blank=True,
                                        on_delete=models.SET_NULL,
                                        db_column="location_id", related_name="foapal_strings")
    foapal_code     = models.CharField(max_length=80, null=True, blank=True)
    description     = models.TextField(null=True, blank=True)
    is_active       = models.BooleanField(default=True)
    valid_from      = models.DateField(null=True, blank=True)
    valid_to        = models.DateField(null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "foapal_strings"
        managed = True
        ordering = ["foapal_code"]
        unique_together = [["fund", "org", "account", "program", "activity", "location"]]

    def __str__(self):
        return self.foapal_code or f"FOAPAL {self.foapalstring_id}"

    def save(self, *args, **kwargs):
        if not self.foapal_code:
            parts = [
                self.fund.code,
                self.org.code,
                self.account.code,
                self.program.code if self.program_id else "",
                self.activity.code if self.activity_id else "",
                self.location.code if self.location_id else "",
            ]
            self.foapal_code = "-".join(parts)
        super().save(*args, **kwargs)

    @property
    def is_valid_today(self):
        from django.utils import timezone
        today = timezone.now().date()
        if not self.is_active:
            return False
        if self.valid_from and self.valid_from > today:
            return False
        if self.valid_to and self.valid_to < today:
            return False
        return True

    @property
    def display_code(self):
        """Human-readable F-O-A-P-A-L string."""
        parts = [
            self.fund.code    if self.fund     else "—",
            self.org.code     if self.org      else "—",
            self.account.code if self.account  else "—",
            getattr(self.program,  "code", "—") if self.program  else "—",
            self.activity.code if self.activity else "—",
            self.location.code if self.location else "—",
        ]
        return "-".join(parts)


class Transaction(models.Model):
    """dbo.transactions"""
    STATUS_CHOICES = [
        ("Pending",  "Pending"),
        ("Coded",    "Coded"),
        ("Approved", "Approved"),
        ("Posted",   "Posted"),
        ("Voided",   "Voided"),
    ]

    id               = GUIDField(primary_key=True, default=uuid.uuid4)
    transaction_date = models.DateField()
    posted_date      = models.DateField(null=True, blank=True)
    reference_number = models.CharField(max_length=50, null=True, blank=True)
    description      = models.TextField()
    amount           = models.DecimalField(max_digits=15, decimal_places=2)
    currency         = models.CharField(max_length=3, default="USD")
    foapal_string    = models.ForeignKey(
        FoapalString, on_delete=models.PROTECT,
        db_column="foapal_string_id", related_name="transactions",
    )
    fund             = models.ForeignKey(Fund,     null=True, blank=True,
                                         on_delete=models.SET_NULL,
                                         db_column="fund_id",     related_name="transactions")
    org              = models.ForeignKey(Org,      null=True, blank=True,
                                         on_delete=models.SET_NULL,
                                         db_column="org_id",      related_name="transactions")
    account          = models.ForeignKey(Account,  null=True, blank=True,
                                         on_delete=models.SET_NULL,
                                         db_column="account_id",  related_name="transactions")
    program          = models.ForeignKey(
        Program, null=True, blank=True,
        on_delete=models.SET_NULL, db_column="program_id", related_name="transactions",
    )
    activity         = models.ForeignKey(Activity, null=True, blank=True,
                                         on_delete=models.SET_NULL,
                                         db_column="activity_id", related_name="transactions")
    location         = models.ForeignKey(Location, null=True, blank=True,
                                         on_delete=models.SET_NULL,
                                         db_column="location_id", related_name="transactions")
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
    source_system    = models.CharField(max_length=50, null=True, blank=True)
    coded_by         = models.CharField(max_length=100, null=True, blank=True)
    coded_at         = models.DateTimeField(null=True, blank=True)
    approved_by      = models.CharField(max_length=100, null=True, blank=True)
    approved_at      = models.DateTimeField(null=True, blank=True)
    notes            = models.TextField(null=True, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "transactions"
        managed = True
        ordering = ["-transaction_date", "-created_at"]

    def __str__(self):
        return f"{self.reference_number or self.id} — {self.amount} {self.currency}"


class TransactionSplit(models.Model):
    """dbo.transaction_splits — splits a transaction across multiple FOAPAL strings."""
    split_id         = GUIDField(primary_key=True, default=uuid.uuid4)
    transaction      = models.ForeignKey(
        Transaction, on_delete=models.CASCADE,
        db_column="transaction_id", related_name="splits",
    )
    foapal_string    = models.ForeignKey(
        FoapalString, on_delete=models.PROTECT,
        db_column="foapal_string_id", related_name="splits",
    )
    amount           = models.DecimalField(max_digits=15, decimal_places=2)
    percentage       = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    notes            = models.TextField(null=True, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "transaction_splits"
        managed = True
        ordering = ["-created_at"]

    def __str__(self):
        return f"Split {self.split_id} — {self.amount}"
