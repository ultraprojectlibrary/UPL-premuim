from django.conf import settings
from django.core.cache import cache
from django.db import models


class SiteSetting(models.Model):
    """Admin-editable config: whatsapp_number, telegram_url, instagram_url, ... (no hard-coding)."""
    key = models.SlugField(unique=True)
    value = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *a, **kw):
        super().save(*a, **kw)
        cache.delete("site_settings")

    @classmethod
    def all_dict(cls):
        data = cache.get("site_settings")
        if data is None:
            data = dict(cls.objects.values_list("key", "value"))
            cache.set("site_settings", data, 300)
        return data


class AuditLog(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=80, db_index=True)
    target_type = models.CharField(max_length=60, blank=True)
    target_id = models.CharField(max_length=60, blank=True)
    result = models.CharField(max_length=20, default="ok")
    ip = models.GenericIPAddressField(null=True, blank=True)
    detail = models.JSONField(default=dict, blank=True)   # never put secrets here
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]


def audit(request, action, target=None, result="ok", **detail):
    AuditLog.objects.create(
        actor=request.user if request.user.is_authenticated else None,
        action=action, target_type=type(target).__name__ if target else "",
        target_id=str(getattr(target, "pk", "")), result=result,
        ip=request.META.get("REMOTE_ADDR"), detail=detail)
