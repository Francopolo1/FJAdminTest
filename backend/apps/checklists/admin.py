import uuid

from django import forms
from django.contrib import admin
from django.core.files.storage import default_storage

from .models import ChecklistTemplate, ChecklistItem


class ChecklistItemAdminForm(forms.ModelForm):
    example_file = forms.FileField(
        required=False,
        help_text="Upload an image, PDF, or video to use as the example (overrides the URL below).",
    )

    class Meta:
        model  = ChecklistItem
        fields = "__all__"

    def save(self, commit=True):
        instance = super().save(commit=False)
        upload = self.cleaned_data.get("example_file")
        if upload:
            ext = upload.name.rsplit(".", 1)[-1].lower() if "." in upload.name else ""
            filename = f"checklist_examples/{uuid.uuid4()}.{ext}" if ext else f"checklist_examples/{uuid.uuid4()}"
            saved_path = default_storage.save(filename, upload)
            instance.example_url = default_storage.url(saved_path)
        if commit:
            instance.save()
        return instance


class ChecklistItemInline(admin.TabularInline):
    model  = ChecklistItem
    extra  = 0
    fields = ["item_text", "response_type", "category", "options", "default_value",
              "example_url", "is_required", "display_order"]
    exclude = ["item_id"]
    ordering = ["category", "display_order"]


@admin.register(ChecklistTemplate)
class ChecklistTemplateAdmin(admin.ModelAdmin):
    list_display  = ["title", "workflow", "step", "is_required", "blocks_advance",
                      "display_order", "item_count"]
    list_filter   = ["workflow", "is_required", "blocks_advance"]
    search_fields = ["title", "description"]
    ordering      = ["workflow", "display_order", "title"]
    readonly_fields = ["created_at", "updated_at"]
    autocomplete_fields = ["workflow"]
    inlines       = [ChecklistItemInline]

    def item_count(self, obj):
        return obj.item_count
    item_count.short_description = "Items"


@admin.register(ChecklistItem)
class ChecklistItemAdmin(admin.ModelAdmin):
    form          = ChecklistItemAdminForm
    list_display  = ["template", "item_text_short", "response_type", "category", "is_required", "display_order"]
    list_filter   = ["response_type", "category", "is_required", "template"]
    search_fields = ["item_text", "template__title"]
    ordering      = ["template", "category", "display_order"]
    autocomplete_fields = ["template"]

    def item_text_short(self, obj):
        return obj.item_text[:60]
    item_text_short.short_description = "Item"
