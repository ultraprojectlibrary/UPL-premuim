from django.conf import settings
from django.db import models


class Plan(models.Model):
    name = models.CharField(max_length=60, unique=True)       # Free / Student / Premium / Organization
    price_kobo = models.PositiveIntegerField(default=0)
    duration_days = models.PositiveIntegerField(default=30)
    features = models.JSONField(default=list)                 # admin-editable
    permissions = models.JSONField(default=list)              # e.g. ["nysc","it","jobs","courses","one_on_one"]
    is_active = models.BooleanField(default=True)


class Subscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscriptions")
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    order = models.OneToOneField("payments.Order", null=True, blank=True, on_delete=models.PROTECT)
    starts_at = models.DateTimeField()
    expires_at = models.DateTimeField(db_index=True)
