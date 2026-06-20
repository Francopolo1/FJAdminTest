from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import AuthUser, AuditLog, UserProgramDistrict


def _is_inspector(user):
    """A user is an inspector if they're a non-staff user with district assignments."""
    return not user.is_staff and UserProgramDistrict.objects.filter(user=user).exists()


def _get_role(user):
    """Role for landing-page/UI purposes: user_profile.role if set, else inferred."""
    profile = getattr(user, "profile", None)
    if profile and profile.role:
        return profile.role
    if user.is_staff:
        return "admin"
    if _is_inspector(user):
        return "inspector"
    return "readonly"


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Accept username (or email) + password."""

    def validate(self, attrs):
        login = attrs.get(self.username_field, "")
        if "@" in login:
            try:
                user = AuthUser.objects.get(email__iexact=login)
            except AuthUser.DoesNotExist:
                pass
            else:
                attrs[self.username_field] = user.username
        return super().validate(attrs)

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["username"]     = user.username
        token["full_name"]    = user.full_name
        token["is_staff"]     = user.is_staff
        token["is_inspector"] = _is_inspector(user)
        token["role"]         = _get_role(user)
        return token


class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer


class AuthUserSerializer(serializers.ModelSerializer):
    full_name    = serializers.SerializerMethodField()
    is_inspector = serializers.SerializerMethodField()
    role         = serializers.SerializerMethodField()

    class Meta:
        model  = AuthUser
        fields = ["id", "username", "first_name", "last_name", "email",
                  "full_name", "is_staff", "is_active", "is_inspector", "role", "date_joined"]
        read_only_fields = ["id", "date_joined"]

    def get_full_name(self, obj):
        return obj.full_name

    def get_is_inspector(self, obj):
        return _is_inspector(obj)

    def get_role(self, obj):
        return _get_role(obj)


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model  = AuditLog
        fields = "__all__"


class RegisterSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=150)
    last_name  = serializers.CharField(max_length=150)
    email      = serializers.EmailField()
    password   = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_email(self, value):
        value = value.lower().strip()
        if AuthUser.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)
        return value

    def _generate_username(self, email):
        base = email.split("@")[0][:140] or "user"
        username = base
        suffix = 1
        while AuthUser.objects.filter(username=username).exists():
            suffix += 1
            username = f"{base}{suffix}"[:150]
        return username

    def create(self, validated_data):
        username = self._generate_username(validated_data["email"])
        user = AuthUser.objects.create_user(
            username=username,
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
        )
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        return value.lower().strip()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid          = serializers.CharField()
    token        = serializers.CharField()
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        from django.utils.encoding import force_str
        from django.utils.http import urlsafe_base64_decode
        from django.contrib.auth.tokens import default_token_generator

        try:
            uid_str = force_str(urlsafe_base64_decode(attrs["uid"]))
            user = AuthUser.objects.get(pk=uid_str)
        except (AuthUser.DoesNotExist, ValueError, TypeError, OverflowError):
            raise serializers.ValidationError("Invalid or expired reset link.")

        if not default_token_generator.check_token(user, attrs["token"]):
            raise serializers.ValidationError("Invalid or expired reset link.")

        try:
            validate_password(attrs["new_password"], user=user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"new_password": exc.messages})

        attrs["user"] = user
        return attrs

    def save(self):
        user = self.validated_data["user"]
        user.set_password(self.validated_data["new_password"])
        user.save()
        return user


class InspectorProgramSerializer(serializers.Serializer):
    program_id = serializers.CharField()
    code       = serializers.CharField()
    title      = serializers.CharField()


class InspectorProgramDistrictSerializer(serializers.Serializer):
    program_district_id = serializers.CharField()
    program_code        = serializers.CharField()
    program_title       = serializers.CharField()
    district            = serializers.IntegerField(allow_null=True)
    description         = serializers.CharField(allow_null=True)


class InspectorProgramFacilitySerializer(serializers.Serializer):
    program_facility_id = serializers.CharField()
    facility_id         = serializers.CharField()
    facility_name       = serializers.CharField(allow_null=True)
    program_district_id = serializers.CharField()
    program_code        = serializers.CharField()
    district            = serializers.IntegerField(allow_null=True)
    facility_type       = serializers.CharField(allow_null=True)
    license_number          = serializers.CharField(allow_null=True)
    risk_assessment_level_id = serializers.IntegerField(allow_null=True)
    risk_assessment         = serializers.CharField(allow_null=True)
    risk_assessment_label   = serializers.CharField(allow_null=True)
    visit_frequency_days    = serializers.IntegerField(allow_null=True)
    activity_flag           = serializers.CharField(allow_null=True)
    activity_flag_label     = serializers.CharField(allow_null=True)
    last_visit_date         = serializers.DateTimeField(allow_null=True)
    next_visit_date         = serializers.DateTimeField(allow_null=True)


class InspectorLandingSerializer(serializers.Serializer):
    programs          = InspectorProgramSerializer(many=True)
    program_districts = InspectorProgramDistrictSerializer(many=True)
    program_facilities = InspectorProgramFacilitySerializer(many=True)


# ── Supervisor landing ──────────────────────────────────────────────────────

class SupervisorDirectReportSerializer(serializers.Serializer):
    user_id           = serializers.IntegerField()
    full_name         = serializers.CharField()
    email             = serializers.CharField()
    job_title         = serializers.CharField(allow_null=True)
    department        = serializers.CharField(allow_null=True)
    role              = serializers.CharField(allow_null=True)
    is_active         = serializers.BooleanField()
    assigned_programs = InspectorProgramSerializer(many=True)


class SupervisorLandingSerializer(serializers.Serializer):
    assigned_programs = InspectorProgramSerializer(many=True)
    direct_reports    = SupervisorDirectReportSerializer(many=True)


class InspectorFacilityAssignmentSerializer(serializers.Serializer):
    program_facility_id = serializers.CharField()
    program_code        = serializers.CharField()
    district            = serializers.IntegerField(allow_null=True)
    facility_type       = serializers.CharField(allow_null=True)
    profile                  = serializers.CharField(allow_null=True)
    license_number           = serializers.CharField(allow_null=True)
    risk_assessment_level_id = serializers.IntegerField(allow_null=True)
    risk_assessment          = serializers.CharField(allow_null=True)
    risk_assessment_label    = serializers.CharField(allow_null=True)
    visit_frequency_days     = serializers.IntegerField(allow_null=True)
    activity_flag            = serializers.CharField(allow_null=True)
    last_visit_date          = serializers.DateTimeField(allow_null=True)
    next_visit_date          = serializers.DateTimeField(allow_null=True)
    instances                = serializers.ListField(child=serializers.DictField())
    activities               = serializers.ListField(child=serializers.DictField())


class InspectorFacilityLocationSerializer(serializers.Serializer):
    address_line1 = serializers.CharField(allow_null=True)
    address_line2 = serializers.CharField(allow_null=True)
    city          = serializers.CharField(allow_null=True)
    state         = serializers.CharField(allow_null=True)
    postal_code   = serializers.CharField(allow_null=True)
    city_state_zip = serializers.CharField(allow_null=True)
    latitude      = serializers.FloatField(allow_null=True)
    longitude     = serializers.FloatField(allow_null=True)


class InspectorFacilityDetailSerializer(serializers.Serializer):
    facility_id   = serializers.CharField()
    facility_name = serializers.CharField(allow_null=True)
    location      = InspectorFacilityLocationSerializer(allow_null=True)
    assignments   = InspectorFacilityAssignmentSerializer(many=True)


# ── Facility directory (search / filter / detail) ───────────────────────────

class FacilityListItemSerializer(serializers.Serializer):
    facility_id         = serializers.CharField()
    facility_name       = serializers.CharField(allow_null=True)
    program_facility_id = serializers.CharField()
    program_id          = serializers.CharField()
    program_code        = serializers.CharField()
    facility_type_id    = serializers.CharField(allow_null=True)
    facility_type       = serializers.CharField(allow_null=True)
    district            = serializers.IntegerField(allow_null=True)
    city                = serializers.CharField(allow_null=True)
    state               = serializers.CharField(allow_null=True)
    license_number      = serializers.CharField(allow_null=True)
    activity_flag       = serializers.CharField(allow_null=True)
    activity_flag_label = serializers.CharField(allow_null=True)


class FacilityProgramOptionSerializer(serializers.Serializer):
    program_id = serializers.CharField()
    code       = serializers.CharField()
    title      = serializers.CharField()


class FacilityTypeOptionSerializer(serializers.Serializer):
    facility_type_id = serializers.CharField()
    code             = serializers.CharField()
    description      = serializers.CharField(allow_null=True)


class FacilityFilterOptionsSerializer(serializers.Serializer):
    programs       = FacilityProgramOptionSerializer(many=True)
    facility_types = FacilityTypeOptionSerializer(many=True)


class FacilityAssignmentSummarySerializer(serializers.Serializer):
    program_facility_id = serializers.CharField()
    program_code        = serializers.CharField()
    district            = serializers.IntegerField(allow_null=True)
    facility_type       = serializers.CharField(allow_null=True)
    profile                  = serializers.CharField(allow_null=True)
    license_number           = serializers.CharField(allow_null=True)
    risk_assessment_level_id = serializers.IntegerField(allow_null=True)
    risk_assessment          = serializers.CharField(allow_null=True)
    risk_assessment_label    = serializers.CharField(allow_null=True)
    visit_frequency_days     = serializers.IntegerField(allow_null=True)
    activity_flag            = serializers.CharField(allow_null=True)
    last_visit_date          = serializers.DateTimeField(allow_null=True)
    next_visit_date          = serializers.DateTimeField(allow_null=True)
    instances                = serializers.ListField(child=serializers.DictField())
    activities               = serializers.ListField(child=serializers.DictField())


class FacilityDetailSerializer(serializers.Serializer):
    facility_id   = serializers.CharField()
    facility_name = serializers.CharField(allow_null=True)
    location      = InspectorFacilityLocationSerializer(allow_null=True)
    assignments   = FacilityAssignmentSummarySerializer(many=True)
