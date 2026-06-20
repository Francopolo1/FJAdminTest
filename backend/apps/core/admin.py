from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    AuthUser, AuditLog, UserProfile, UserRole,
    FacilityType, Specialtracking, ProgramFacilityType, ProgramFacilityTypeActivity,
    FacilityLocation, Facility, ProgramDistricts, ProgramFacility,
    RiskAssessmentLevel, UserProgram, UserProgramDistrict,
)
from apps.financials.models import Org
from apps.workflows.models import WorkflowDefinition


class UserProfileForm(forms.ModelForm):
    class Meta:
        model  = UserProfile
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        org_titles = Org.objects.order_by("title").values_list("title", "title")
        self.fields["department"] = forms.ChoiceField(
            choices=[("", "---------"), *org_titles],
            required=False,
        )
        role_choices = UserRole.objects.values_list("code", "name")
        self.fields["role"] = forms.ChoiceField(
            choices=[("", "---------"), *role_choices],
        )


class UserProfileInline(admin.StackedInline):
    model    = UserProfile
    form     = UserProfileForm
    fk_name  = "user"
    extra    = 0
    max_num  = 1
    can_delete = False
    fields   = ["role", "phone", "job_title", "department", "manager",
                "timezone", "is_verified", "force_password_change",
                "avatar_url", "bio"]
    autocomplete_fields = ["manager"]


@admin.register(AuthUser)
class AuthUserAdmin(UserAdmin):
    list_display  = ["username", "first_name", "last_name", "email", "is_staff", "is_active", "role"]
    search_fields = ["username", "email", "first_name", "last_name"]
    list_filter   = ["is_staff", "is_active", "profile__role"]
    readonly_fields = ["date_joined"]
    fieldsets     = (
        (None,          {"fields": ("username", "password")}),
        ("Personal",    {"fields": ("first_name", "last_name", "email")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Dates",       {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("username", "email", "password1", "password2")}),
    )

    def get_inlines(self, request, obj):
        if obj is None:
            return []
        return [UserProfileInline, UserProgramInline, UserProgramDistrictInline]

    def role(self, obj):
        return getattr(getattr(obj, "profile", None), "get_role_display", lambda: "—")()
    role.short_description = "Role"
    role.admin_order_field = "profile__role"


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "display_order"]
    ordering     = ["display_order", "name"]


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    form          = UserProfileForm
    list_display  = ["user", "role", "department", "job_title", "manager", "is_verified"]
    list_filter   = ["role", "department", "is_verified"]
    search_fields = ["user__username", "user__first_name", "user__last_name", "job_title", "department"]
    autocomplete_fields = ["user", "manager"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display  = ["table_name", "record_id", "action", "changed_by", "changed_at"]
    list_filter   = ["action", "table_name"]
    search_fields = ["table_name", "changed_by"]
    readonly_fields = ["id", "changed_at"]
    fieldsets = (
        (None, {
            "fields": ("table_name", "record_id", "action", "old_data", "new_data", "changed_by", "changed_at")
        }),
    )


# ── Facility / Program hierarchy ───────────────────────────────────────────

@admin.register(FacilityType)
class FacilityTypeAdmin(admin.ModelAdmin):
    list_display  = ["code", "description"]
    search_fields = ["code", "description"]
    ordering      = ["code"]


@admin.register(Specialtracking)
class SpecialtrackingAdmin(admin.ModelAdmin):
    list_display  = ["trackingcode", "trackingdescription"]
    search_fields = ["trackingcode", "trackingdescription"]
    ordering      = ["trackingcode"]


class WorkflowDefinitionInline(admin.TabularInline):
    model    = WorkflowDefinition
    fk_name  = "program_facility_type_activity"
    extra    = 0
    fields   = ["name", "version", "category", "is_active"]
    exclude  = ["workflow_id"]
    show_change_link = True


@admin.register(ProgramFacilityTypeActivity)
class ProgramFacilityTypeActivityAdmin(admin.ModelAdmin):
    list_display  = ["description", "program_facility_type", "specialtracking", "foapalstring"]
    list_filter   = ["program_facility_type", "specialtracking"]
    search_fields = ["description", "program_facility_type__description", "foapalstring__foapal_code"]
    autocomplete_fields = ["foapalstring"]
    inlines       = [WorkflowDefinitionInline]


class ProgramFacilityTypeActivityInline(admin.TabularInline):
    model  = ProgramFacilityTypeActivity
    extra  = 0
    fields = ["description", "specialtracking", "foapalstring"]
    exclude = ["program_facility_type_activity_id"]
    autocomplete_fields = ["foapalstring"]
    show_change_link = True


class RiskAssessmentLevelInline(admin.TabularInline):
    model  = RiskAssessmentLevel
    extra  = 0
    fields = ["code", "label", "visit_frequency_days", "description"]
    ordering = ["visit_frequency_days"]


@admin.register(ProgramFacilityType)
class ProgramFacilityTypeAdmin(admin.ModelAdmin):
    list_display  = ["program", "facility_type", "description"]
    list_filter   = ["program", "facility_type"]
    search_fields = ["description", "program__code", "facility_type__code"]
    autocomplete_fields = ["program", "facility_type"]
    inlines       = [RiskAssessmentLevelInline, ProgramFacilityTypeActivityInline]


@admin.register(RiskAssessmentLevel)
class RiskAssessmentLevelAdmin(admin.ModelAdmin):
    list_display   = ["code", "label", "program_facility_type", "visit_frequency_days"]
    list_filter    = ["program_facility_type"]
    search_fields  = ["code", "label", "program_facility_type__description"]
    ordering       = ["program_facility_type", "visit_frequency_days"]


@admin.register(FacilityLocation)
class FacilityLocationAdmin(admin.ModelAdmin):
    list_display  = ["location_id", "addressline1", "city", "stateprovince", "postalcode"]
    search_fields = ["addressline1", "addressline2", "city", "postalcode"]
    fieldsets = (
        (None, {"fields": ("location_id",)}),
        ("Address", {"fields": (
            "addressline1", "addressline2", "city", "stateprovince",
            "postalcode", "country", "countyname",
        )}),
        ("Coordinates", {"fields": ("latitude", "longitude", "xcoordinate", "ycoordinate"), "classes": ("collapse",)}),
    )


@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display  = ["name", "location", "activity_status", "active_date", "deactive_date"]
    list_filter   = ["activity_status", "master"]
    search_fields = ["name"]
    autocomplete_fields = ["location"]

@admin.register(ProgramDistricts)
class ProgramDistrictsAdmin(admin.ModelAdmin):
    list_display  = ["program", "district", "description"]
    list_filter   = ["program"]
    search_fields = ["description", "program__code", "program__title"]
    autocomplete_fields = ["program"]
    ordering      = ["program", "district"]


@admin.register(ProgramFacility)
class ProgramFacilityAdmin(admin.ModelAdmin):
    list_display  = ["facility", "program_facility_type", "program_district",
                      "license_number", "license_expire_date", "activity_flag"]
    list_filter   = ["program_facility_type", "program_district", "activity_flag"]
    search_fields = ["facility__name", "license_number", "tracking_id"]
    autocomplete_fields = ["facility", "program_facility_type", "program_district"]
    fieldsets = (
        (None, {"fields": ("facility", "program_facility_type", "program_district", "profile")}),
        ("Licensing", {"fields": (
            "license_number", "license_expire_date", "tracking_id",
            "risk_assessment", "activity_flag",
        )}),
        ("Visits", {"fields": (
            "start_date", "last_visit_date", "next_visit_date",
            "visit_month_seed", "activity_change_date",
        )}),
        ("Contact / Notes", {"fields": ("facility_phone", "comments")}),
    )

# ── User program assignments ────────────────────────────────────────────────

class UserProgramInline(admin.TabularInline):
    model  = UserProgram
    fk_name = "user"
    extra  = 0
    fields = ["program"]
    autocomplete_fields = ["program"]


class UserProgramDistrictInline(admin.TabularInline):
    model  = UserProgramDistrict
    fk_name = "user"
    extra  = 0
    fields = ["program_district", "assigned_date"]
    exclude = ["auth_user_program_district_id"]
    autocomplete_fields = ["program_district"]


@admin.register(UserProgram)
class UserProgramAdmin(admin.ModelAdmin):
    list_display  = ["user", "program"]
    list_filter   = ["program"]
    search_fields = ["user__username", "user__first_name", "user__last_name", "program__code"]
    autocomplete_fields = ["user", "program"]


@admin.register(UserProgramDistrict)
class UserProgramDistrictAdmin(admin.ModelAdmin):
    list_display  = ["user", "program_district", "assigned_date"]
    list_filter   = ["program_district"]
    search_fields = ["user__username", "user__first_name", "user__last_name"]
    autocomplete_fields = ["user", "program_district"]