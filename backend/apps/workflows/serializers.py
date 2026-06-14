from rest_framework import serializers
from .models import (WorkflowDefinition, WorkflowStep, WorkflowTransition,
                     StepAction, WorkflowInstance, WorkflowTask, WorkflowAuditLog)


class WorkflowStepSerializer(serializers.ModelSerializer):
    class Meta:
        model  = WorkflowStep
        fields = ["step_id","workflow","step_name","step_type","step_order",
                  "is_initial","is_final","sla_hours","entry_condition","created_at"]


class WorkflowTransitionSerializer(serializers.ModelSerializer):
    from_step_name = serializers.CharField(source="from_step.step_name", read_only=True)
    to_step_name   = serializers.CharField(source="to_step.step_name",   read_only=True)
    class Meta:
        model  = WorkflowTransition
        fields = ["transition_id","workflow","from_step","from_step_name",
                  "to_step","to_step_name","transition_name","trigger_event","condition","created_at"]


class WorkflowDefinitionSerializer(serializers.ModelSerializer):
    steps       = WorkflowStepSerializer(many=True, read_only=True)
    transitions = WorkflowTransitionSerializer(many=True, read_only=True)
    class Meta:
        model  = WorkflowDefinition
        fields = ["workflow_id","name","description","version","category","is_active",
                  "created_at","updated_at","program_facility_type_activity","steps","transitions"]


class WorkflowDefinitionListSerializer(serializers.ModelSerializer):
    step_count = serializers.IntegerField(source="steps.count", read_only=True)
    class Meta:
        model  = WorkflowDefinition
        fields = ["workflow_id","name","version","category","is_active","created_at","step_count"]


class WorkflowTaskSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(source="assigned_to.full_name", read_only=True)
    step_name        = serializers.CharField(source="step.step_name",         read_only=True)
    hours_remaining  = serializers.SerializerMethodField()

    class Meta:
        model  = WorkflowTask
        fields = ["task_id","instance","step","step_name","assigned_to","assigned_to_name",
                  "assigned_by","status","comments","assigned_at","due_date","completed_at","hours_remaining"]

    def get_hours_remaining(self, obj):
        from django.utils import timezone
        if not obj.due_date: return None
        delta = obj.due_date - timezone.now()
        return max(0, int(delta.total_seconds() / 3600))


class WorkflowInstanceSerializer(serializers.ModelSerializer):
    workflow_name       = serializers.CharField(source="workflow.name",            read_only=True)
    initiated_by_name   = serializers.CharField(source="initiated_by.full_name",   read_only=True)
    current_step_name   = serializers.CharField(source="current_step.step_name",   read_only=True, default=None)
    tasks               = WorkflowTaskSerializer(many=True, read_only=True)

    class Meta:
        model  = WorkflowInstance
        fields = ["instance_id","workflow","workflow_name","initiated_by","initiated_by_name",
                  "current_step","current_step_name","status","reference_no","request_data",
                  "priority","started_at","completed_at","due_date","program_facility","tasks"]


class WorkflowInstanceListSerializer(serializers.ModelSerializer):
    workflow_name     = serializers.CharField(source="workflow.name",          read_only=True)
    initiated_by_name = serializers.CharField(source="initiated_by.full_name", read_only=True)
    current_step_name = serializers.CharField(source="current_step.step_name", read_only=True, default=None)
    class Meta:
        model  = WorkflowInstance
        fields = ["instance_id","reference_no","workflow_name","initiated_by_name",
                  "current_step_name","status","priority","started_at","due_date"]


class WorkflowAuditLogSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source="actor.full_name", read_only=True)
    class Meta:
        model  = WorkflowAuditLog
        fields = ["log_id","instance","task","actor","actor_name","action",
                  "from_status","to_status","notes","logged_at"]

class AdvanceInstanceSerializer(serializers.Serializer):
    trigger_event = serializers.CharField()
    comments      = serializers.CharField(required=False, allow_blank=True)

class StepActionSerializer(serializers.ModelSerializer):
    class Meta:
        model  = StepAction
        fields = ["action_id","step","action_name","trigger_event","condition","created_at"]

