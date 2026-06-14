from django.db import migrations

ROLES = [
    ("admin",            "Admin",            10),
    ("director_manager", "Director/Manager", 20),
    ("supervisor",       "Supervisor",       30),
    ("inspector",        "Inspector",        40),
    ("it_staff",         "IT Staff",         50),
    ("support_staff",    "Support Staff",    60),
    ("readonly",         "Read Only",        70),
]


def seed_roles(apps, schema_editor):
    UserRole = apps.get_model("core", "UserRole")
    for code, name, display_order in ROLES:
        UserRole.objects.update_or_create(
            code=code,
            defaults={"name": name, "display_order": display_order},
        )


def unseed_roles(apps, schema_editor):
    UserRole = apps.get_model("core", "UserRole")
    UserRole.objects.filter(code__in=[code for code, _, _ in ROLES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_userrole'),
    ]

    operations = [
        migrations.RunPython(seed_roles, unseed_roles),
    ]
