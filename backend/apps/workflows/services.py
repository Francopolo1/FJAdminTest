"""
Business logic for submitting and advancing workflow instances.
Mirrors SP_SubmitInstance / SP_AdvanceInstance from the SQL schema.
"""

from django.db import transaction
from django.utils import timezone

from .models import (
    WorkflowDefinition, WorkflowStep, WorkflowInstance,
    WorkflowTask, WorkflowTransition, WorkflowAuditLog,
)

# Maps WorkflowStep.step_type to the UserProfile.role responsible for acting
# on that step. Step types not listed here (e.g. "Automated") need no task.
ROLE_BY_STEP_TYPE = {
    "Manual": "inspector",
    "Decision": "supervisor",
}


def generate_reference_no(workflow):
    """Generate the next sequential reference number for a workflow definition.

    Format: {year}-{program.code}-{facility_type.code}-{activity.code}-{NNNN}
    The 4-digit incrementor resets to 0001 at the start of each year.
    """
    pfta                  = workflow.program_facility_type_activity
    program_facility_type = pfta.program_facility_type
    program               = program_facility_type.program
    facility_type         = program_facility_type.facility_type
    activity              = pfta.foapalstring.activity

    activity_code = activity.code if activity else "GEN"

    year = timezone.now().year
    stub = f"{year}-{program.code.strip()}-{facility_type.code.strip()}-{activity_code.strip()}-"

    max_seq = 0
    for ref in WorkflowInstance.objects.filter(reference_no__startswith=stub).values_list("reference_no", flat=True):
        try:
            max_seq = max(max_seq, int(ref[len(stub):]))
        except ValueError:
            continue

    return f"{stub}{max_seq + 1:04d}"


def submit_instance(workflow_id, initiated_by, reference_no,
                    request_data=None, priority=2, program_facility=None):
    """Create and start a new workflow instance."""
    with transaction.atomic():
        wf = WorkflowDefinition.objects.get(pk=workflow_id, is_active=True)

        initial_step = (
            WorkflowStep.objects
            .filter(workflow=wf, is_initial=True)
            .order_by("step_order")
            .first()
        )
        if not initial_step:
            raise ValueError("Workflow has no initial step defined.")

        due_date = None
        if initial_step.sla_hours:
            due_date = timezone.now() + timezone.timedelta(hours=initial_step.sla_hours)

        instance = WorkflowInstance.objects.create(
            workflow=wf,
            initiated_by=initiated_by,
            current_step=initial_step,
            status="InProgress",
            reference_no=reference_no,
            request_data=request_data,
            priority=priority,
            due_date=due_date,
            program_facility=program_facility,
        )

        # Spin up checklist runs for the initial step
        _create_checklist_runs(instance, initial_step)

        # Assign task(s) for the initial step
        _create_step_tasks(instance, initial_step, assigned_by=initiated_by)

        WorkflowAuditLog.objects.create(
            instance=instance,
            actor=initiated_by,
            action="Submit",
            to_status="InProgress",
            notes="Instance created and submitted.",
        )
        return instance


def advance_instance(instance, actor, trigger_event, comments=None):
    """Transition an instance to the next step."""
    with transaction.atomic():
        current_step = instance.current_step
        if current_step is None:
            raise ValueError("Instance is already completed.")

        # Restrict the action to users with the role responsible for this
        # step (e.g. only supervisors may act on "Decision" steps).
        required_role = ROLE_BY_STEP_TYPE.get(current_step.step_type)
        if required_role and not actor.is_staff:
            actor_role = getattr(getattr(actor, "profile", None), "role", None)
            if actor_role != required_role:
                raise ValueError(
                    f"Only users with the '{required_role}' role can act on "
                    f"the '{current_step.step_name}' step."
                )

        # Block advance when a blocking checklist is incomplete
        blocking = instance.checklist_runs.filter(
            template__blocks_advance=True,
        ).exclude(status__in=["Completed", "Skipped"])
        if blocking.exists():
            titles = ", ".join(blocking.values_list("template__title", flat=True))
            raise ValueError(
                f"Complete all blocking checklists before advancing: {titles}"
            )

        transition = WorkflowTransition.objects.filter(
            from_step=current_step,
            trigger_event=trigger_event,
        ).first()
        if not transition:
            raise ValueError(
                f"No transition '{trigger_event}' from step '{current_step.step_name}'."
            )

        next_step  = transition.to_step
        is_final   = next_step.is_final
        from_status = instance.status

        if is_final:
            to_status = {
                "Approve": "Approved",
                "Reject": "Rejected",
                "Inspection Closed": "Approved",
                "Inspection Rejected": "Rejected",
            }.get(trigger_event, "Approved")
        else:
            to_status = "InProgress"

        # Update instance
        instance.status       = to_status
        instance.current_step = None if is_final else next_step
        if is_final:
            instance.completed_at = timezone.now()
        elif next_step.sla_hours:
            instance.due_date = timezone.now() + timezone.timedelta(hours=next_step.sla_hours)
        instance.save()

        # Complete the actor's open task at the current step
        WorkflowTask.objects.filter(
            instance=instance,
            step=current_step,
            assigned_to=actor,
            status__in=["Pending", "InProgress"],
        ).update(
            status="Completed",
            completed_at=timezone.now(),
            comments=comments,
        )

        # Spin up checklists and task(s) for next step
        if not is_final:
            _create_checklist_runs(instance, next_step)
            _create_step_tasks(instance, next_step, assigned_by=actor)

            # Automated compliance check: assess fines for any violations found
            if next_step.step_type == "ComplianceCheck":
                from apps.enforcement.services import run_compliance_check
                run_compliance_check(instance, actor=actor)

        WorkflowAuditLog.objects.create(
            instance=instance,
            actor=actor,
            action=trigger_event,
            from_status=from_status,
            to_status=to_status,
            notes=comments,
        )
        return instance


def _create_step_tasks(instance, step, assigned_by):
    """Create WorkflowTask rows assigning the new current step to the users
    responsible for the facility's program district.

    Automated steps (not present in ROLE_BY_STEP_TYPE) need no human task.
    If nobody with the required role is assigned to the district, fall back
    to the instance's initiator so the step still has an owner.
    """
    role = ROLE_BY_STEP_TYPE.get(step.step_type)
    if role is None:
        return

    from django.contrib.auth import get_user_model
    User = get_user_model()

    program_district = instance.program_facility.program_district
    assignees = list(
        User.objects.filter(
            user_program_districts__program_district=program_district,
            profile__role=role,
        ).distinct()
    )
    if not assignees:
        assignees = [instance.initiated_by]

    due_date = None
    if step.sla_hours:
        due_date = timezone.now() + timezone.timedelta(hours=step.sla_hours)

    for user in assignees:
        WorkflowTask.objects.create(
            instance=instance,
            step=step,
            assigned_to=user,
            assigned_by=assigned_by,
            due_date=due_date,
        )


def _create_checklist_runs(instance, step):
    """Create ChecklistRun rows for templates attached to this step."""
    from apps.checklists.models import ChecklistTemplate, ChecklistRun

    existing = set(
        instance.checklist_runs.values_list("template_id", flat=True)
    )
    templates = ChecklistTemplate.objects.filter(
        workflow=instance.workflow,
        is_required=True,
    ).filter(
        models_q := __import__("django.db.models", fromlist=["Q"]).Q(step=step) |
                   __import__("django.db.models", fromlist=["Q"]).Q(step__isnull=True)
    ).exclude(pk__in=existing)

    runs = [
        ChecklistRun(instance=instance, template=t, status="NotStarted")
        for t in templates
    ]
    ChecklistRun.objects.bulk_create(runs)
