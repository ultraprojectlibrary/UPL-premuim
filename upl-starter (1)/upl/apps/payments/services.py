"""Payment logic. The browser redirect is NEVER trusted: every order is confirmed by calling
Paystack's verify API server-side and checking status, amount and currency against our own DB."""
import logging
import uuid
import requests
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.catalog.models import Document, SourceCode, ModerationStatus
from .models import Order, Entitlement

log = logging.getLogger("upl.payments")
PAYSTACK = "https://api.paystack.co"
HEADERS = lambda: {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}


def create_order(user, kind, item):
    """Price is read from the DB here; nothing from the browser decides the amount."""
    if kind not in ("document", "sourcecode"):
        raise ValueError("unsupported kind")
    return Order.objects.create(user=user, kind=kind, item_id=str(item.pk), amount_kobo=item.price_kobo,
                                provider_reference=f"UPL-{uuid.uuid4().hex[:18].upper()}")


def initialize(order, callback_url):
    r = requests.post(f"{PAYSTACK}/transaction/initialize", headers=HEADERS(), timeout=15, json={
        "email": order.user.email, "amount": order.amount_kobo, "currency": order.currency,
        "reference": order.provider_reference, "callback_url": callback_url,
        "metadata": {"order_id": str(order.id)}})
    r.raise_for_status()
    return r.json()["data"]["authorization_url"]


def verify_and_fulfil(reference):
    """Idempotent: safe to call from callback AND webhook, any number of times."""
    with transaction.atomic():
        try:
            order = Order.objects.select_for_update().get(provider_reference=reference)
        except Order.DoesNotExist:
            log.warning("verify for unknown reference %s", reference)
            return None
        if order.status == Order.Status.SUCCESSFUL:
            return order

        r = requests.get(f"{PAYSTACK}/transaction/verify/{reference}", headers=HEADERS(), timeout=15)
        r.raise_for_status()
        data = r.json().get("data", {})
        ok = (data.get("status") == "success" and data.get("amount") == order.amount_kobo
              and data.get("currency") == order.currency and data.get("reference") == reference)
        if not ok:
            if data.get("status") in ("failed", "abandoned", "reversed"):
                order.status = Order.Status.FAILED
                order.save(update_fields=["status"])
            log.warning("payment not valid ref=%s status=%s", reference, data.get("status"))
            return order

        order.status = Order.Status.SUCCESSFUL
        order.verified = True
        order.paid_at = timezone.now()
        order.provider_payload = {k: data.get(k) for k in ("id", "status", "amount", "currency", "paid_at", "channel")}
        order.save()
        _fulfil(order)
        transaction.on_commit(lambda: _notify(order.id))
        log.info("order %s fulfilled", order.id)
        return order


def _fulfil(order):
    if order.kind == "document":
        doc = Document.objects.get(pk=order.item_id, status=ModerationStatus.APPROVED)
        Entitlement.objects.get_or_create(order=order, defaults={"user": order.user, "document": doc})
    elif order.kind == "sourcecode":
        sc = SourceCode.objects.get(pk=order.item_id, status=ModerationStatus.APPROVED)
        Entitlement.objects.get_or_create(order=order, defaults={"user": order.user, "source_code": sc})


def _notify(order_id):
    from .tasks import send_purchase_emails
    send_purchase_emails.delay(str(order_id))
