from django.contrib import admin
from django.utils.html import format_html
from .models import (Fund, Org, Account, Program, Activity, Location,
                     FoapalString, Transaction, TransactionSplit)
from apps.core.models import ProgramFacilityType, ProgramDistricts


class TransactionSplitInline(admin.TabularInline):
    model   = TransactionSplit
    extra   = 0
    fields  = ["foapal_string", "amount", "percentage", "notes"]
    readonly_fields = ["split_id"]
    autocomplete_fields = ["foapal_string"]


class ProgramFacilityTypeInline(admin.TabularInline):
    model  = ProgramFacilityType
    extra  = 0
    fields = ["facility_type", "description", "profile_template"]
    exclude = ["program_facility_type_id"]
    show_change_link = True


class ProgramDistrictsInline(admin.TabularInline):
    model  = ProgramDistricts
    fk_name = "program"
    extra  = 0
    fields = ["district", "description"]
    exclude = ["program_district_id"]
    show_change_link = True


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display  = ["code", "title", "is_active", "effective_date", "expiry_date"]
    list_filter   = ["is_active"]
    search_fields = ["code", "title"]
    ordering      = ["code"]
    readonly_fields = ["created_at", "updated_at"]
    inlines       = [ProgramFacilityTypeInline, ProgramDistrictsInline]


@admin.register(Fund)
class FundAdmin(admin.ModelAdmin):
    list_display  = ["code", "title", "fund_type", "is_active", "effective_date", "expiry_date"]
    list_filter   = ["is_active", "fund_type"]
    search_fields = ["code", "title"]
    ordering      = ["code"]
    readonly_fields = ["fund_id", "created_at", "updated_at"]


@admin.register(Org)
class OrgAdmin(admin.ModelAdmin):
    list_display  = ["code", "title", "parent_org", "is_active"]
    list_filter   = ["is_active"]
    search_fields = ["code", "title"]
    ordering      = ["code"]
    readonly_fields = ["org_id", "created_at", "updated_at"]


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display  = ["code", "title", "account_type", "normal_balance", "is_active"]
    list_filter   = ["is_active", "account_type", "normal_balance"]
    search_fields = ["code", "title"]
    ordering      = ["code"]
    readonly_fields = ["account_id", "created_at", "updated_at"]


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display  = ["code", "title", "is_active", "effective_date"]
    list_filter   = ["is_active"]
    search_fields = ["code", "title"]
    ordering      = ["code"]
    readonly_fields = ["activity_id", "created_at", "updated_at"]

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display  = ["code", "title", "building", "campus", "is_active"]
    list_filter   = ["is_active", "campus"]
    search_fields = ["code", "title", "building"]
    ordering      = ["code"]
    readonly_fields = ["locaton_id", "created_at", "updated_at"]


@admin.register(FoapalString)
class FoapalStringAdmin(admin.ModelAdmin):
    list_display  = ["foapal_code", "fund", "org", "account", "program",
                     "is_active", "valid_today_badge", "valid_from", "valid_to"]
    list_filter   = ["is_active", "fund", "org"]
    search_fields = ["foapal_code", "description", "fund__code", "org__code", "account__code"]
    ordering      = ["foapal_code"]
    readonly_fields = ["foapalstring_id", "created_at", "updated_at"]
    autocomplete_fields = ["fund", "org", "account", "program", "activity", "location"]

    def valid_today_badge(self, obj):
        if obj.is_valid_today:
            return format_html('<span style="color:{}font-weight:600">● Valid</span>', "#059669;")
        return format_html('<span style="color:{}">● Invalid</span>', "#ADB5BD")
    valid_today_badge.short_description = "Valid Today"


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display  = ["reference_number", "transaction_date", "amount", "currency",
                     "status_badge", "fund", "org", "account", "coded_by", "approved_by"]
    list_filter   = ["status", "currency", "source_system"]
    search_fields = ["reference_number", "description", "coded_by", "approved_by",
                     "foapal_string__foapal_code"]
    ordering      = ["-transaction_date"]
    readonly_fields = ["id", "created_at", "updated_at"]
    date_hierarchy = "transaction_date"
    inlines        = [TransactionSplitInline]
    autocomplete_fields = ["foapal_string", "fund", "org", "account", "program", "activity", "location"]
    fieldsets = (
        ("Transaction",  {"fields": ("id", "transaction_date", "posted_date",
                                     "reference_number", "description", "amount", "currency", "status")}),
        ("Coding",       {"fields": ("foapal_string", "fund", "org", "account",
                                     "program", "activity", "location")}),
        ("Workflow",     {"fields": ("source_system", "coded_by", "coded_at",
                                     "approved_by", "approved_at")}),
        ("Notes",        {"fields": ("notes",)}),
        ("Timestamps",   {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def status_badge(self, obj):
        colours = {"Pending":"#F59E0B","Coded":"#3B82F6","Approved":"#059669",
                   "Posted":"#10B981","Voided":"#9CA3AF"}
        c = colours.get(obj.status, "#9CA3AF")
        return format_html('<span style="color:{};font-weight:600">{}</span>', c, obj.status)
    status_badge.short_description = "Status"


@admin.register(TransactionSplit)
class TransactionSplitAdmin(admin.ModelAdmin):
    list_display  = ["split_id", "transaction", "foapal_string", "amount", "percentage"]
    list_filter   = ["foapal_string"]
    search_fields = ["transaction__reference_number", "foapal_string__foapal_code"]
    ordering      = ["-created_at"]
    readonly_fields = ["split_id", "created_at"]
