import uuid
from django.conf import settings
from django.db import models


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending"; SUCCESSFUL = "successful"; FAILED = "failed"
        CANCELLED = "cancelled"; REFUNDED = "refunded"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders")
    kind = models.CharField(max_length=20)             # document | sourcecode | booking | subscription
    item_id = models.CharField(max_length=40)
    amount_kobo = models.PositiveIntegerField()        # copied from DB price at order time
    currency = models.CharField(max_length=3, default="NGN")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING, db_index=True)
    provider = models.CharField(max_length=20, default="paystack")
    provider_reference = models.CharField(max_length=80, unique=True)
    verified = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)
    provider_payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [models.Index(fields=["user", "-created_at"])]


class Entitlement(models.Model):
    """Purchase -> Paid -> Entitlement -> Download access."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="entitlements")
    document = models.ForeignKey("catalog.Document", null=True, blank=True, on_delete=models.SET_NULL)
    source_code = models.ForeignKey("catalog.SourceCode", null=True, blank=True, on_delete=models.SET_NULL)
    order = models.OneToOneField(Order, on_delete=models.PROTECT)
    download_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    revoked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "document"], condition=models.Q(revoked=False, document__isnull=False),
                                    name="one_active_entitlement_per_user_doc"),
        ]


class DownloadLog(models.Model):
    entitlement = models.ForeignKey(Entitlement, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
