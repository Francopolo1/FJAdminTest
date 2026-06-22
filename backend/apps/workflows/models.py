import uuid
from django.db import models
from django.conf import settings
from apps.core.db_fields import GUIDField


class WorkflowDefinition(models.Model):
    workflow_id                     = GUIDField(primary_key=True, default=uuid.uuid4)
    name                            = models.CharField(max_length=200)
    description                     = models.TextField(null=True, blank=True)
    version                         = models.CharField(max_length=20, default="1.0")
    category                        = models.CharField(max_length=100, null=True, blank=True)
    is_active                       = models.BooleanField(default=True)
    created_at                      = models.DateTimeField(auto_now_add=True)
    updated_at                      = models.DateTimeField(auto_now=True)
    program_facility_type_activity  = models.ForeignKey(
        "core.ProgramFacilityTypeActivity",
        on_delete=models.PROTECT,
        db_column="program_facility_type_activity_id",
    )

    class Meta:
        db_table        = "workflow_definition"
        managed         = False
        unique_together = [("name", "version")]

    def __str__(self):
        return f"{self.name} v{self.version}"


class WorkflowStep(models.Model):
    step_id         = GUIDField(primary_key=True, default=uuid.uuid4)
    workflow        = models.ForeignKey(WorkflowDefinition, on_delete=models.CASCADE,
                                        db_column="workflow_id", related_name="steps")
    step_name       = models.CharField(max_length=200)
    step_type       = models.CharField(max_length=50, default="Manual")
    step_order      = models.IntegerField()
    is_initial      = models.BooleanField(default=False)
    is_final        = models.BooleanField(default=False)
    sla_hours       = models.IntegerField(null=True, blank=True)
    entry_condition = models.TextField(null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "workflow_step"
        managed  = False
        ordering = ["step_order"]

    def __str__(self):
        return f"{self.workflow.name} – {self.step_name}"


class WorkflowTransition(models.Model):
    transition_id   = GUIDField(primary_key=True, default=uuid.uuid4)
    workflow        = models.ForeignKey(WorkflowDefinition, on_delete=models.CASCADE,
                                        db_column="workflow_id", related_name="transitions")
    from_step       = models.ForeignKey(WorkflowStep, on_delete=models.CASCADE,
                                        db_column="from_step_id", related_name="outgoing")
    to_step         = models.ForeignKey(WorkflowStep, on_delete=models.CASCADE,
                                        db_column="to_step_id", related_name="incoming")
    transition_name = models.CharField(max_length=200)
    trigger_event   = models.CharField(max_length=100)
    condition       = models.TextField(null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table        = "workflow_transition"
        managed         = False
        unique_together = [("from_step", "trigger_event")]

    def __str__(self):
        return f"{self.from_step.step_name} –[{self.trigger_event}]→ {self.to_step.step_name}"


class StepAction(models.Model):
    action_id       = GUIDField(primary_key=True, default=uuid.uuid4)
    step            = models.ForeignKey(WorkflowStep, on_delete=models.CASCADE,
                                        db_column="step_id", related_name="actions")
    action_type     = models.CharField(max_length=100)
    action_config   = models.TextField(null=True, blank=True)
    execution_order = models.IntegerField(default=1)
    is_required     = models.BooleanField(default=True)

    class Meta:
        db_table = "step_action"
        managed  = False
        ordering = ["execution_order"]


class WorkflowInstance(models.Model):
    STATUS_CHOICES = [
        ("Draft","Draft"), ("InProgress","In Progress"), ("Approved","Approved"),
        ("Rejected","Rejected"), ("Cancelled","Cancelled"), ("OnHold","On Hold"),
        ("Closed","Closed"),
    ]
    instance_id      = GUIDField(primary_key=True, default=uuid.uuid4)
    workflow         = models.ForeignKey(WorkflowDefinition, on_delete=models.PROTECT,
                                         db_column="workflow_id", related_name="instances")
    initiated_by     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                                         db_column="initiated_by_id", related_name="initiated_instances")
    current_step     = models.ForeignKey(WorkflowStep, null=True, blank=True,
                                         on_delete=models.SET_NULL, db_column="current_step_id")
    status           = models.CharField(max_length=50, choices=STATUS_CHOICES, default="Draft")
    reference_no     = models.CharField(max_length=50, unique=True)
    request_data     = models.TextField(null=True, blank=True)
    priority         = models.SmallIntegerField(default=2)
    started_at       = models.DateTimeField(auto_now_add=True)
    completed_at     = models.DateTimeField(null=True, blank=True)
    due_date         = models.DateTimeField(null=True, blank=True)
    program_facility = models.ForeignKey(
        "core.ProgramFacility", on_delete=models.PROTECT,
        db_column="program_facility_id", related_name="instances",
    )

    class Meta:
        db_table = "workflow_instance"
        managed  = False
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.reference_no} [{self.status}]"


class WorkflowTask(models.Model):
    STATUS_CHOICES = [
        ("Pending","Pending"), ("InProgress","In Progress"), ("Completed","Completed"),
        ("Delegated","Delegated"), ("Overdue","Overdue"), ("Skipped","Skipped"),
    ]
    task_id      = GUIDField(primary_key=True, default=uuid.uuid4)
    instance     = models.ForeignKey(WorkflowInstance, on_delete=models.CASCADE,
                                     db_column="instance_id", related_name="tasks")
    step         = models.ForeignKey(WorkflowStep, on_delete=models.PROTECT,
                                     db_column="step_id", related_name="tasks")
    assigned_to  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                                     db_column="assigned_to", related_name="assigned_tasks")
    assigned_by  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                                     db_column="assigned_by", related_name="created_tasks")
    delegated_to = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                     on_delete=models.SET_NULL, db_column="delegated_to",
                                     related_name="delegated_tasks")
    status       = models.CharField(max_length=50, choices=STATUS_CHOICES, default="Pending")
    comments     = models.TextField(null=True, blank=True)
    assigned_at  = models.DateTimeField(auto_now_add=True)
    due_date     = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "workflow_task"
        managed  = False
        ordering = ["due_date"]


class WorkflowAuditLog(models.Model):
    log_id      = GUIDField(primary_key=True, default=uuid.uuid4)
    instance    = models.ForeignKey(WorkflowInstance, on_delete=models.CASCADE,
                                    db_column="instance_id", related_name="audit_logs")
    task        = models.ForeignKey(WorkflowTask, null=True, blank=True,
                                    on_delete=models.SET_NULL, db_column="task_Id")
    actor       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                                    db_column="actor_id", related_name="workflow_audit_logs")
    action      = models.CharField(max_length=100)
    from_status = models.CharField(max_length=50, null=True, blank=True)
    to_status   = models.CharField(max_length=50, null=True, blank=True)
    notes       = models.TextField(null=True, blank=True)
    ip_address  = models.CharField(max_length=45, null=True, blank=True)
    logged_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "workflow_audit_log"
        managed  = False
        ordering = ["-logged_at"]
