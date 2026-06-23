"""
The dashboards app reads from the existing SQL Server views via
Django ORM proxy (unmanaged) models.
"""
from django.db import models
from apps.core.db_fields import GUIDField


class VWInstanceDashboard(models.Model):
    """Maps to dbo.VW_InstanceDashboard."""
    instance_id          = models.CharField(primary_key=True, max_length=36)
    reference_no         = models.CharField(max_length=50)
    workflow_name        = models.CharField(max_length=200,  db_column="WorkflowName")
    category             = models.CharField(max_length=100,  db_column="Category",      null=True)
    initiated_by         = models.CharField(max_length=301)
    current_step         = models.CharField(max_length=200,  db_column="CurrentStep",   null=True)
    status               = models.CharField(max_length=50)
    priority             = models.SmallIntegerField(         db_column="Priority")
    started_at           = models.DateTimeField()
    due_date             = models.DateTimeField(null=True)
    completed_at         = models.DateTimeField(null=True)
    elapsed_hours        = models.IntegerField(              db_column="ElapsedHours",  null=True)
    total_tasks          = models.IntegerField(              db_column="TotalTasks",    null=True)
    completed_tasks      = models.IntegerField(              db_column="CompletedTasks", null=True)
    total_checklists     = models.IntegerField(              db_column="TotalChecklists", null=True)
    completed_checklists = models.IntegerField(              db_column="CompletedChecklists", null=True)
    checklist_pct_done   = models.DecimalField(max_digits=5, decimal_places=1,
                                               db_column="ChecklistPctDone", null=True)

    class Meta:
        db_table = "VW_InstanceDashboard"
        managed  = False
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.reference_no} [{self.status}]"


class VWPendingTask(models.Model):
    """Maps to dbo.VW_PendingTasks."""
    task_id         = models.CharField(primary_key=True, max_length=36)
    reference_no    = models.CharField(max_length=50)
    workflow_name   = models.CharField(max_length=200,  db_column="WorkflowName")
    step_name       = models.CharField(max_length=200)
    assigned_to     = models.CharField(max_length=301)
    assignee_email  = models.CharField(max_length=254,  db_column="AssigneeEmail")
    status          = models.CharField(max_length=50)
    assigned_at     = models.DateTimeField()
    due_date        = models.DateTimeField(null=True)
    hours_remaining = models.IntegerField(               db_column="HoursRemaining", null=True)
    priority        = models.SmallIntegerField(          db_column="Priority")

    class Meta:
        db_table = "VW_PendingTasks"
        managed  = False
        ordering = ["due_date"]

    def __str__(self):
        return f"{self.reference_no} — {self.step_name}"


class VWChecklistProgress(models.Model):
    """Maps to dbo.VW_ChecklistProgress."""
    instance_id       = models.CharField(primary_key=True, max_length=36)
    reference_no      = models.CharField(max_length=50)
    checklist_title   = models.CharField(max_length=300, db_column="Checklisttitle")
    blocks_advance    = models.BooleanField()
    run_status        = models.CharField(max_length=50,  db_column="Runstatus")
    total_items       = models.IntegerField(             db_column="TotalItems",       null=True)
    required_items    = models.IntegerField(             db_column="RequiredItems",    null=True)
    answered_items    = models.IntegerField(             db_column="AnsweredItems",    null=True)
    answered_required = models.IntegerField(             db_column="AnsweredRequired", null=True)
    pct_complete      = models.DecimalField(max_digits=5, decimal_places=1,
                                            db_column="PctComplete", null=True)

    class Meta:
        db_table = "VW_ChecklistProgress"
        managed  = False

    def __str__(self):
        return f"{self.reference_no} — {self.checklist_title}"
