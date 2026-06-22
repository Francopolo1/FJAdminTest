import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from apps.core.db_fields import GUIDField, new_guid_str
from apps.financials.models import FoapalString


class AuthUserManager(BaseUserManager):
    def create_user(self, username, email="", password=None, **extra):
        user = self.model(username=username, email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email="", password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        return self.create_user(username, email, password, **extra)


class AuthUser(AbstractBaseUser, PermissionsMixin):
    """Maps to dbo.auth_user."""
    id           = models.AutoField(primary_key=True)
    username     = models.CharField(max_length=150, unique=True)
    first_name   = models.CharField(max_length=150, default="")
    last_name    = models.CharField(max_length=150, default="")
    email        = models.CharField(max_length=254, default="")
    is_staff     = models.BooleanField(default=False)
    is_active    = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    date_joined  = models.DateTimeField(auto_now_add=True)
    last_login   = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD  = "username"
    REQUIRED_FIELDS = ["email"]
    objects = AuthUserManager()

    class Meta:
        db_table = "auth_user"
        managed  = False

    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username


class UserRole(models.Model):
    """dbo.user_roles — lookup table backing UserProfile.role's dropdown."""
    code          = models.CharField(max_length=30, primary_key=True)
    name          = models.CharField(max_length=50)
    display_order = models.IntegerField(default=0)

    class Meta:
        db_table = "user_roles"
        ordering = ["display_order", "name"]

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    """Maps to dbo.user_profile — extended user attributes incl. role."""

    id          = models.BigAutoField(primary_key=True)
    user        = models.OneToOneField(AuthUser, models.CASCADE, db_column="user_id", related_name="profile")
    manager     = models.ForeignKey(
        "self", models.SET_NULL, null=True, blank=True,
        db_column="manager_id", related_name="direct_reports",
    )
    phone       = models.CharField(max_length=20, blank=True, null=True)
    job_title   = models.CharField(max_length=100, blank=True, null=True)
    department  = models.CharField(max_length=100, blank=True, null=True)
    role        = models.CharField(max_length=30)
    avatar_url  = models.CharField(max_length=200, blank=True, null=True)
    bio         = models.TextField(blank=True, null=True)
    timezone    = models.CharField(max_length=60)
    is_verified = models.BooleanField(default=False)
    force_password_change = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_profile"
        managed  = False

    def __str__(self):
        role_name = UserRole.objects.filter(pk=self.role).values_list("name", flat=True).first()
        return f"{self.user} — {role_name or self.role}"


class AuditLog(models.Model):
    id         = GUIDField(primary_key=True, default=uuid.uuid4)
    table_name = models.CharField(max_length=50, null=True, blank=True)
    record_id  = GUIDField(null=True, blank=True)
    action     = models.CharField(max_length=10, null=True, blank=True)
    old_data   = models.TextField(null=True, blank=True)
    new_data   = models.TextField(null=True, blank=True)
    changed_by = models.CharField(max_length=100, null=True, blank=True)
    changed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "audit_log"
        managed  = False
        ordering = ["-changed_at"]

    def __str__(self):
        return f"{self.action} on {self.table_name} at {self.changed_at}"

class FacilityType(models.Model):
    facility_type_id = models.CharField(primary_key=True, max_length=36, default=new_guid_str)
    code = models.CharField(max_length=5, db_collation='SQL_Latin1_General_CP1_CI_AS')
    description = models.CharField(max_length=50, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'facility_types'
    def __str__(self):
        return f"{self.code} ({self.description})"
    
class ProgramFacilityType(models.Model):
    program_facility_type_id = models.CharField(primary_key=True, max_length=36, default=new_guid_str)
    program = models.ForeignKey('financials.Program', models.DO_NOTHING)
    facility_type = models.ForeignKey(FacilityType, models.DO_NOTHING)
    profile_template = models.CharField(max_length=4000, db_collation='SQL_Latin1_General_CP1_CI_AS')
    description = models.CharField(max_length=200, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'program_facility_types'
    def __str__(self):
        return f"{self.program.code} - {self.facility_type.code} ({self.description})"

class Specialtracking(models.Model):
    specialtracking_id = models.CharField(primary_key=True, max_length=36, default=new_guid_str)
    trackingcode = models.CharField(max_length=20, db_collation='SQL_Latin1_General_CP1_CI_AS')
    trackingdescription = models.CharField(max_length=100, db_collation='SQL_Latin1_General_CP1_CI_AS')

    class Meta:
        managed = False
        db_table = 'specialtracking'

    def __str__(self):        return f"{self.trackingcode} ({self.trackingdescription})"


class ProgramFacilityTypeActivity(models.Model):
    program_facility_type_activity_id = models.CharField(primary_key=True, max_length=36, default=new_guid_str)
    foapalstring = models.ForeignKey(
        FoapalString, models.DO_NOTHING, db_column='foapalstring_id',
        related_name='program_facility_type_activities',
    )
    program_facility_type = models.ForeignKey('ProgramFacilityType', models.DO_NOTHING)
    specialtracking = models.ForeignKey('Specialtracking', models.DO_NOTHING, blank=True, null=True)
    description = models.CharField(max_length=100, db_collation='SQL_Latin1_General_CP1_CI_AS')

    class Meta:
        managed = False
        db_table = 'program_facility_type_activities'
    def __str__(self):
        return f"{self.program_facility_type} - {self.description}"

class FacilityLocation(models.Model):
    location_id = models.CharField(primary_key=True, max_length=36, default=new_guid_str)
    xcoordinate = models.FloatField(blank=True, null=True)
    ycoordinate = models.FloatField(blank=True, null=True)
    addressid = models.IntegerField(blank=True, null=True)
    intersectionid = models.IntegerField(blank=True, null=True)
    addressline1 = models.CharField(max_length=50, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    addressline2 = models.CharField(max_length=50, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    city = models.CharField(max_length=25, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    citystatezip = models.CharField(max_length=50, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    stateprovince = models.CharField(max_length=50, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    postalcode = models.CharField(max_length=15, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    zipplus4 = models.CharField(db_column='zipPlus4', max_length=15, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)  # Field name made lowercase.
    addressnumberprefix = models.CharField(max_length=10, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    addressnumber = models.IntegerField(blank=True, null=True)
    addressnumbersuffix = models.CharField(max_length=10, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    streetnamepremodifier = models.CharField(max_length=10, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    streetnamepredirectional = models.CharField(max_length=10, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    streetnamepretype = models.CharField(max_length=10, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    streetname = models.CharField(max_length=50, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    streetnameposttype = models.CharField(max_length=10, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    streetnamepostdirectional = models.CharField(max_length=10, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    streetnamepostmodifier = models.CharField(max_length=10, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    unittype = models.CharField(max_length=10, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    unitidentifier = models.CharField(max_length=10, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    buildingidentifier = models.CharField(max_length=10, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    buildingtype = models.CharField(max_length=10, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    compositeunitidentifier = models.CharField(max_length=10, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    compositeunittype = models.CharField(max_length=10, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    postalplacename = models.CharField(max_length=50, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    country = models.CharField(max_length=50, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    countyname = models.CharField(max_length=50, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    postaldeliveryline = models.CharField(max_length=100, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    postallastline = models.CharField(max_length=50, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    postaldeliverable = models.CharField(max_length=10, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    postaldeliverynotes = models.CharField(max_length=10, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    source = models.CharField(max_length=10, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    type = models.CharField(max_length=10, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    score = models.DecimalField(max_digits=18, decimal_places=0, blank=True, null=True)
    parsed = models.BooleanField(blank=True, null=True)
    parsedremainder = models.CharField(max_length=10, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    easting = models.FloatField(blank=True, null=True)
    northing = models.FloatField(blank=True, null=True)
    coordinatesystem = models.CharField(max_length=50, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    datum = models.CharField(max_length=50, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    comments = models.CharField(max_length=50, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    displayline1 = models.CharField(max_length=80, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    displayline2 = models.CharField(max_length=50, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    displaycitystatezip = models.CharField(max_length=50, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    lasteditdate = models.DateTimeField(blank=True, null=True)
    lasteditby = models.IntegerField(blank=True, null=True)
    creationdate = models.DateTimeField(blank=True, null=True)
    createdby = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'facility_locations'

class Facility(models.Model):
    facility_id = models.CharField(primary_key=True, max_length=36, default=new_guid_str)
    location = models.ForeignKey(FacilityLocation, models.DO_NOTHING)
    name = models.CharField(max_length=50, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    activity_status = models.BooleanField(blank=True, null=True)
    active_date = models.DateTimeField(blank=True, null=True)
    deactive_date = models.DateTimeField(blank=True, null=True)
    master_facility_id = models.IntegerField(blank=True, null=True)
    master = models.BooleanField(blank=True, null=True)
    checked = models.BooleanField(blank=True, null=True)
    temp_notes = models.CharField(max_length=255, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    temp_loc = models.IntegerField(blank=True, null=True)
    temp_name = models.CharField(max_length=50, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    last_edit_date = models.DateTimeField(blank=True, null=True)
    last_edit_by = models.IntegerField(blank=True, null=True)
    creation_date = models.DateTimeField(blank=True, null=True)
    created_by = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'facilities'
        verbose_name_plural = "facilities"
    def __str__(self):        return f"{self.name} ({self.location})"

class ProgramDistricts(models.Model):
    program_district_id = models.CharField(primary_key=True, max_length=36, default=new_guid_str)
    program = models.ForeignKey('financials.Program', models.DO_NOTHING, db_column='program_id', related_name='program_districts')
    district = models.SmallIntegerField()
    description = models.CharField(max_length=50, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'program_districts'
    def __str__(self):        return f"{self.program} - District {self.district} ({self.description})"

class ProgramFacility(models.Model):
    program_facility_id = models.CharField(primary_key=True, max_length=36, default=new_guid_str)
    program_facility_type = models.ForeignKey(ProgramFacilityType, models.DO_NOTHING)
    facility = models.ForeignKey(Facility, models.DO_NOTHING)
    profile = models.CharField(max_length=4000, db_collation='SQL_Latin1_General_CP1_CI_AS')
    program_district = models.ForeignKey(ProgramDistricts, models.DO_NOTHING)
    tracking_id = models.CharField(max_length=20, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    risk_assessment_level = models.ForeignKey(
        'RiskAssessmentLevel', models.SET_NULL,
        null=True, blank=True,
        db_column='risk_assessment_levels_id',
        related_name='program_facilities',
    )
    start_date = models.DateTimeField(blank=True, null=True)
    activity_flag = models.CharField(max_length=1, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    license_number = models.CharField(max_length=15, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    license_expire_date = models.DateTimeField(blank=True, null=True)
    last_visit_date = models.DateTimeField(blank=True, null=True)
    next_visit_date = models.DateTimeField(blank=True, null=True)
    facility_phone = models.CharField(max_length=15, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    activity_change_date = models.DateTimeField(blank=True, null=True)
    comments = models.CharField(max_length=255, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    visit_month_seed = models.SmallIntegerField(blank=True, null=True)
    season_start = models.CharField(
        max_length=5, blank=True, null=True,
        help_text="Facility season start date as 'MM-DD' (e.g., '05-01' for May 1st). If set, activity_flag auto-adjusts based on season."
    )
    season_end = models.CharField(
        max_length=5, blank=True, null=True,
        help_text="Facility season end date as 'MM-DD' (e.g., '09-30' for Sept 30th). If set, activity_flag auto-adjusts based on season."
    )

    class Meta:
        managed = False
        db_table = 'program_facilities'
        verbose_name_plural = "program facilities"

    def __str__(self):
        return f"{self.facility} in {self.program_facility_type} ({self.program_district})"

    def is_in_season(self):
        """Check if facility is currently in its active season.

        Returns True if season_start and season_end are set and current date is within range.
        Handles season ranges that span year boundaries (e.g., Nov 1 - Feb 28).
        """
        if not self.season_start or not self.season_end:
            return True  # No season defined = always in season

        try:
            today = timezone.now().date()
            start_month, start_day = map(int, self.season_start.split('-'))
            end_month, end_day = map(int, self.season_end.split('-'))

            # Create date objects for this year
            start_date = today.replace(month=start_month, day=start_day)
            end_date = today.replace(month=end_month, day=end_day)

            # Handle season that spans year boundary (e.g., Nov 1 - Feb 28)
            if start_date <= end_date:
                # Normal case: season within same year
                return start_date <= today <= end_date
            else:
                # Season spans year boundary
                return today >= start_date or today <= end_date
        except (ValueError, AttributeError):
            return True  # Invalid season format = always in season

    def get_activity_flag_for_season(self):
        """Determine what activity_flag should be based on season.

        Returns:
        - 'I' if out of season and facility is not closed
        - 'A' if in season and facility is not closed
        - Current activity_flag if it's 'C' (closed)
        """
        if self.activity_flag == 'C':
            return self.activity_flag  # Don't override closed status

        if self.is_in_season():
            return 'A'  # Active
        else:
            return 'I'  # Inactive

    def calculate_next_visit_date(self):
        """Calculate next_visit_date based on last_visit_date and risk assessment frequency.

        Returns the calculated next visit date, or None if calculation is not possible.

        Calculation logic:
        - If no last_visit_date: returns None (no baseline to calculate from)
        - If no risk_assessment_level: returns None (no frequency defined)
        - If risk_assessment_level has no visit_frequency_days: returns None
        - Otherwise: returns last_visit_date + visit_frequency_days
        """
        if not self.last_visit_date or not self.risk_assessment_level:
            return None

        if not self.risk_assessment_level.visit_frequency_days:
            return None

        from datetime import timedelta
        return self.last_visit_date + timedelta(days=self.risk_assessment_level.visit_frequency_days)

    def update_next_visit_date(self):
        """Recalculate and save next_visit_date based on current last_visit_date and risk level.

        Returns True if next_visit_date was updated, False otherwise.
        """
        calculated_date = self.calculate_next_visit_date()
        if calculated_date != self.next_visit_date:
            self.next_visit_date = calculated_date
            return True
        return False


class StepTypeRole(models.Model):
    """Lookup table mapping workflow step types to the role responsible for acting
    on them.  responsible_role=None means the step is automated — no human task
    is created and the engine auto-advances using the 'Auto' trigger event.
    """
    step_type        = models.CharField(max_length=50, primary_key=True)
    label            = models.CharField(max_length=100)
    responsible_role = models.CharField(
        max_length=30, null=True, blank=True,
        help_text="UserProfile.role that handles this step. Leave blank for automated steps.",
    )
    description      = models.TextField(null=True, blank=True)

    class Meta:
        db_table            = "workflow_step_type_roles"
        ordering            = ["step_type"]
        verbose_name        = "step type role"
        verbose_name_plural = "step type roles"

    def __str__(self):
        role = self.responsible_role or "automated"
        return f"{self.step_type} → {role}"


class ActivityFlag(models.Model):
    """Lookup table for program_facilities.activity_flag (A/I/C)."""
    code        = models.CharField(max_length=1, primary_key=True)
    label       = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table            = "activity_flags"
        ordering            = ["code"]
        verbose_name        = "activity flag"
        verbose_name_plural = "activity flags"

    def __str__(self):
        return f"{self.code} — {self.label}"


class RiskAssessmentLevel(models.Model):
    """Visit-frequency lookup keyed by (code, program_facility_type).

    `program_facilities.risk_assessment` stores the code; join on both
    code + program_facility_type_id to resolve label and visit frequency.
    """
    code                  = models.CharField(max_length=5)
    program_facility_type = models.ForeignKey(
        ProgramFacilityType, models.CASCADE,
        related_name="risk_assessment_levels",
    )
    label                 = models.CharField(max_length=50)
    visit_frequency_days  = models.PositiveIntegerField(
        help_text="Target days between visits for this risk level.",
    )
    description           = models.TextField(blank=True, null=True)

    class Meta:
        db_table             = "risk_assessment_levels"
        unique_together      = [("code", "program_facility_type")]
        ordering             = ["program_facility_type", "visit_frequency_days"]
        verbose_name         = "risk assessment level"
        verbose_name_plural  = "risk assessment levels"

    def __str__(self):
        return f"{self.code} — {self.label} ({self.visit_frequency_days}d)"


class UserProgram(models.Model):
    id         = models.AutoField(primary_key=True)
    user       = models.ForeignKey('core.AuthUser', models.CASCADE, db_column='user_id', related_name='user_programs')
    program    = models.ForeignKey('financials.Program', models.CASCADE, db_column='program_id', related_name='user_programs')

    class Meta:
        managed = False
        db_table = 'user_programs'

    def __str__(self):
        return f"{self.user} — {self.program}"


class UserProgramDistrict(models.Model):
    auth_user_program_district_id = models.CharField(primary_key=True, max_length=36, default=new_guid_str)
    user             = models.ForeignKey('core.AuthUser', models.CASCADE, db_column='user_id', related_name='user_program_districts')
    program_district = models.ForeignKey(ProgramDistricts, models.CASCADE, db_column='program_district_id', related_name='user_program_districts')
    assigned_date    = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = 'user_program_districts'

    def __str__(self):
        return f"{self.user} — {self.program_district}"