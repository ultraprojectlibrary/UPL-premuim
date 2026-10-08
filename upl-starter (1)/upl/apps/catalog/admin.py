from django.contrib import admin
from django.utils import timezone
from apps.core.models import audit
from .models import Document, SourceCode, Material, Course, ModerationStatus


def _set_status(status):
    def action(modeladmin, request, queryset):
        for obj in queryset:
            obj.status = status; obj.reviewed_by = request.user; obj.reviewed_at = timezone.now(); obj.save()
            audit(request, f"{modeladmin.model.__name__.lower()}.{status}", obj)
    action.short_description = f"Mark selected as {status}"
    action.__name__ = f"mark_{status}"
    return action


class ModeratedAdmin(admin.ModelAdmin):
    list_filter = ("status", "created_at")
    search_fields = ("title",)
    actions = [_set_status(ModerationStatus.APPROVED), _set_status(ModerationStatus.REJECTED),
               _set_status(ModerationStatus.SUSPENDED)]


for m in (Document, SourceCode, Material, Course):
    admin.site.register(m, ModeratedAdmin)
