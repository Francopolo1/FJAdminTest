"""
Checklist app models.

Design notes
───────────────────────────────────────────────────────────────────────────
• ChecklistTemplate  – reusable checklist definition tied to a workflow step
• ChecklistItem      – one answerable question inside a template
• ChecklistRun       – runtime execution of a template against an instance
• ChecklistResponse  – a single user answer to a single item in a run

Key behaviours
  - options field is validated as a non-empty list for choice-type items
  - completion_pct, required_done, total_required are cached-on-save via
    a post_save signal so list views don't need N+1 queries
  - BlocksAdvance=True runs block WorkflowInstance.advance() in services.py
  - A run auto-completes when all required items are answered (via the
    respond() view action or the signal)
"""

import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.utils import timezone

from apps.core.db_fields import GUIDField
from ..workflows.models import WorkflowDefinition, WorkflowStep, WorkflowInstance, WorkflowTask
from ..compliance.models import ComplianceRule, ViolationSeverityLevel, FineSchedule, FineTier

# ── ChecklistTemplate ─────────────────────────────────────────────────────────

class ChecklistTemplate(models.Model):
    """
    A reusable checklist definition.

    Attach to a specific WorkflowStep (step FK) to show the checklist only
    when the instance reaches that step.  Leave step=None to attach it to
    every step of the workflow.

    blocks_advance=True means the workflow engine refuses to call
    advance_instance() while any run of this template is not yet Completed
    or Skipped.
    """

    template_id    = GUIDField(primary_key=True, default=uuid.uuid4)
    workflow       = models.ForeignKey(
        WorkflowDefinition, on_delete=models.CASCADE,
        related_name="checklist_templates",
    )
    step           = models.ForeignKey(
        WorkflowStep, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="checklist_templates",
        help_text="Leave blank to attach to all steps of the workflow.",
    )
    title          = models.CharField(max_length=300)
    description    = models.TextField(blank=True, null=True)
    is_required    = models.BooleanField(
        default=True,
        help_text="Required checklists are automatically created when an instance enters the step.",
    )
    blocks_advance = models.BooleanField(
        default=True,
        help_text="Prevent advancing the workflow until this checklist is completed or skipped.",
    )
    display_order  = models.IntegerField(default=1)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        managed  = False
        db_table = "checklist_template"
        ordering = ["display_order", "title"]
        indexes  = [
            models.Index(fields=["workflow", "step"], name="idx_chktmpl_wf_step"),
        ]

    def __str__(self):
        step_label = f" @ {self.step.step_name}" if self.step else " (all steps)"
        return f"{self.title}{step_label}"

    def clean(self):
        # A blocking checklist must also be required — otherwise it can never
        # be created automatically and the instance would be permanently stuck.
        if self.blocks_advance and not self.is_required:
            raise ValidationError(
                "A checklist that blocks advance must also be marked as required."
            )

    @property
    def item_count(self):
        return self.items.count()

    @property
    def required_item_count(self):
        return self.items.filter(is_required=True).count()


# ── ChecklistItem ─────────────────────────────────────────────────────────────

class ChecklistItem(models.Model):
    """
    One answerable question / instruction within a ChecklistTemplate.

    response_type drives the UI widget and the validation logic applied when
    a ChecklistResponse is saved:

        YesNo         → "Yes" or "No" (case-insensitive)
        Text          → any non-empty string
        Number        → parseable as float
        Date          → ISO-8601 date (YYYY-MM-DD)
        SingleChoice  → one value from options[]
        MultiChoice   → comma-joined values all present in options[]
        FileUpload    → any non-empty string (file reference / URL)
        Signature     → any non-empty string (typed name)
    """

    RESPONSE_TYPE_CHOICES = [
        ("YesNo",        "Yes / No"),
        ("Text",         "Text"),
        ("Number",       "Number"),
        ("Date",         "Date"),
        ("SingleChoice", "Single Choice"),
        ("MultiChoice",  "Multi Choice"),
        ("FileUpload",   "File Upload"),
        ("Signature",    "Signature"),
    ]

    CHOICE_TYPES = {"SingleChoice", "MultiChoice"}

    item_id        = GUIDField(primary_key=True, default=uuid.uuid4)
    template       = models.ForeignKey(
        ChecklistTemplate, on_delete=models.CASCADE, related_name="items"
    )
    item_text      = models.CharField(max_length=500)
    help_text      = models.TextField(blank=True, null=True)
    response_type  = models.CharField(
        max_length=50, choices=RESPONSE_TYPE_CHOICES, default="YesNo"
    )
    category       = models.CharField(max_length=100, blank=True, null=True)
    display_order  = models.IntegerField(default=1)
    is_required    = models.BooleanField(default=True)
    options        = models.JSONField(
        blank=True, null=True,
        help_text="Non-empty list of strings for SingleChoice / MultiChoice items.",
    )
    default_value  = models.CharField(max_length=500, blank=True, null=True)
    example_url    = models.CharField(
        max_length=500, blank=True, null=True,
        help_text="External URL (e.g. Google image, YouTube) linking to an example response.",
    )
    example_file   = models.FileField(
        upload_to="checklist_examples/", blank=True, null=True,
        help_text="Uploaded image or PDF stored in cloud storage (R2). Takes precedence over example_url when set.",
    )
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed  = False
        db_table = "checklist_item"
        ordering = ["category", "display_order"]
        indexes  = [
            models.Index(fields=["template", "display_order"], name="idx_chkitem_tmpl_order"),
            models.Index(fields=["template", "category", "display_order"], name="idx_chkitem_tmpl_cat_order"),
        ]

    def __str__(self):
        return f"{self.template.title} – {self.item_text[:60]}"

    def clean(self):
        if self.response_type in self.CHOICE_TYPES:
            if not self.options or not isinstance(self.options, list) or len(self.options) == 0:
                raise ValidationError(
                    f"response_type '{self.response_type}' requires a non-empty options list."
                )
            if not all(isinstance(o, str) for o in self.options):
                raise ValidationError("All options must be strings.")
        else:
            # options are meaningless for non-choice types
            if self.options:
                self.options = None

    def validate_response(self, value: str) -> str:
        """
        Validate and normalise a raw response string.
        Raises ValidationError on invalid input.
        Returns the normalised value.
        """
        if not value and not self.is_required:
            return value  # blank is OK for optional items

        rt = self.response_type

        if rt == "YesNo":
            normalised = value.strip().capitalize()
            if normalised not in ("Yes", "No"):
                raise ValidationError(f"Expected 'Yes' or 'No', got '{value}'.")
            return normalised

        if rt == "Number":
            try:
                float(value)
            except (ValueError, TypeError):
                raise ValidationError(f"Expected a number, got '{value}'.")
            return value

        if rt == "Date":
            import datetime
            try:
                datetime.date.fromisoformat(value.strip())
            except (ValueError, AttributeError):
                raise ValidationError(f"Expected YYYY-MM-DD date, got '{value}'.")
            return value.strip()

        if rt == "SingleChoice":
            if value not in self.options:
                raise ValidationError(
                    f"'{value}' is not a valid choice. Options: {self.options}"
                )
            return value

        if rt == "MultiChoice":
            selected = [v.strip() for v in value.split(",")]
            invalid  = [v for v in selected if v not in self.options]
            if invalid:
                raise ValidationError(
                    f"Invalid choices: {invalid}. Options: {self.options}"
                )
            return ", ".join(selected)

        # Text / FileUpload / Signature — just ensure non-empty when required
        if self.is_required and not value.strip():
            raise ValidationError("This field is required.")

        return value


# ── ChecklistRun ──────────────────────────────────────────────────────────────

class ChecklistRun(models.Model):
    """
    A single execution of a ChecklistTemplate against a WorkflowInstance.

    One run is created automatically per template when the instance enters
    the associated step (see workflows/services.py → _create_checklist_runs).

    Cached counters (answered_required, total_required) are recomputed by
    a signal on ChecklistResponse save so that list-view serializers
    never cause N+1 queries.
    """

    STATUS_CHOICES = [
        ("NotStarted", "Not Started"),
        ("InProgress",  "In Progress"),
        ("Completed",  "Completed"),
        ("Skipped",    "Skipped"),
    ]

    run_id            = GUIDField(primary_key=True, default=uuid.uuid4)
    instance          = models.ForeignKey(
        WorkflowInstance, on_delete=models.CASCADE, related_name="checklist_runs"
    )
    task              = models.ForeignKey(
        WorkflowTask, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="checklist_runs",
        help_text="Optional: scope this run to a specific task.",
        db_column="task_Id",
    )
    template          = models.ForeignKey(
        ChecklistTemplate, on_delete=models.PROTECT, related_name="runs"
    )
    status            = models.CharField(
        max_length=50, choices=STATUS_CHOICES, default="NotStarted", db_index=True
    )
    started_at        = models.DateTimeField(null=True, blank=True)
    completed_at      = models.DateTimeField(null=True, blank=True)
    created_at        = models.DateTimeField(auto_now_add=True)
    total_items       = models.IntegerField(default=0, editable=False)
    total_required    = models.IntegerField(default=0, editable=False)
    answered_items    = models.IntegerField(default=0, editable=False)
    answered_required = models.IntegerField(default=0, editable=False)

    class Meta:
        managed  = False
        db_table = "checklist_run"
        ordering = ["-created_at"]
        indexes  = [
            models.Index(fields=["instance", "status"], name="idx_chkrun_inst_status"),
        ]

    def __str__(self):
        return f"Run {self.pk} – {self.template.title} [{self.status}]"

    # ── Computed properties ───────────────────────────────────

    @property
    def completion_pct(self) -> float:
        if self.total_items == 0:
            return 100.0
        return round(self.answered_items * 100 / self.total_items, 1)

    @property
    def required_completion_pct(self) -> float:
        if self.total_required == 0:
            return 100.0
        return round(self.answered_required * 100 / self.total_required, 1)

    @property
    def is_complete(self) -> bool:
        return self.status == "Completed"

    @property
    def is_blocking(self) -> bool:
        return self.template.blocks_advance and self.status not in ("Completed", "Skipped")

    # ── Computed counters ──────────────────────────────────────

    @property
    def total_items(self) -> int:
        return self.template.items.count()

    @property
    def total_required(self) -> int:
        return self.template.items.filter(is_required=True).count()

    @property
    def _answered_item_ids(self):
        return set(
            self.responses
            .exclude(response_value__isnull=True)
            .exclude(response_value="")
            .values_list("item_id", flat=True)
        )

    @property
    def answered_items(self) -> int:
        return len(self._answered_item_ids)

    @property
    def answered_required(self) -> int:
        answered = self._answered_item_ids
        return self.template.items.filter(is_required=True, item_id__in=answered).count()

    # ── Mutation helpers ──────────────────────────────────────

    def try_auto_complete(self):
        """Mark Completed when all required items are answered."""
        if self.status in ("Completed", "Skipped"):
            return
        if self.total_required > 0 and self.answered_required >= self.total_required:
            self.status       = "Completed"
            self.completed_at = timezone.now()
            self.save(update_fields=["status", "completed_at"])

    def mark_in_progress(self):
        if self.status == "NotStarted":
            self.status     = "InProgress"
            self.started_at = timezone.now()
            self.save(update_fields=["status", "started_at"])

    def mark_skipped(self):
        if self.template.blocks_advance:
            raise ValidationError("Blocking checklists cannot be skipped.")
        if self.status in ("Completed", "Skipped"):
            raise ValidationError(f"Run is already {self.status}.")
        self.status       = "Skipped"
        self.completed_at = timezone.now()
        self.save(update_fields=["status", "completed_at"])


# ── ChecklistResponse ─────────────────────────────────────────────────────────

class ChecklistResponse(models.Model):
    """
    A single user answer to a single ChecklistItem within a ChecklistRun.

    response_value is stored as text regardless of the item's response_type;
    the item's validate_response() method normalises it before saving.

    The unique_together constraint on (run, item) means each item can only
    be answered once per run; subsequent POSTs to respond/ update the
    existing record (upsert).
    """

    response_id    = GUIDField(primary_key=True, default=uuid.uuid4)
    run            = models.ForeignKey(
        ChecklistRun, on_delete=models.CASCADE, related_name="responses"
    )
    item           = models.ForeignKey(
        ChecklistItem, on_delete=models.PROTECT, related_name="responses"
    )
    responded_by   = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="checklist_responses",
        db_column="responded_by",
    )
    response_value = models.TextField(blank=True, null=True)
    notes          = models.TextField(blank=True, null=True)
    box_folder_url = models.CharField(
        max_length=500, blank=True, null=True,
        help_text="Link to the Box.com documents folder for this response.",
    )
    responded_at   = models.DateTimeField(auto_now=True)

    class Meta:
        managed         = False
        db_table        = "checklist_response"
        unique_together = [("run", "item")]
        indexes         = [
            models.Index(fields=["run"], name="idx_chkresp_run"),
        ]

    def __str__(self):
        return f"Response[run={self.run_id}, item={self.item_id}]"

    def clean(self):
        # Validate the item belongs to the run's template
        if self.item.template_id != self.run.template_id:
            raise ValidationError(
                f"Item {self.item_id} does not belong to template {self.run.template_id}."
            )
        # Normalise and validate the response value
        if self.response_value is not None:
            self.response_value = self.item.validate_response(self.response_value)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


# ── Signals ───────────────────────────────────────────────────────────────────

@receiver(post_save, sender=ChecklistResponse)
def on_response_saved(sender, instance, **kwargs):
    """
    After any response is saved:
      1. Refresh the run's cached counters.
      2. Auto-complete the run if all required items are answered.
      3. Ensure the run is marked InProgress if it was NotStarted.
    """
    run = instance.run
    run.mark_in_progress()
    run.try_auto_complete()
    
class ChecklistItemComplianceRules(models.Model):
    checklist_item_compliance_rule_id = models.CharField(primary_key=True, max_length=36)
    checklist_item = models.ForeignKey(ChecklistItem, models.DO_NOTHING, blank=True, null=True)
    compliance_rule = models.ForeignKey('compliance.ComplianceRule', models.DO_NOTHING)

    class Meta:
        managed = True
        db_table = 'checklist_item_compliance_rules'
