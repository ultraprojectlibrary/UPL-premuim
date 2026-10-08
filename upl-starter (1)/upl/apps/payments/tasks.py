from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from .models import Order
from apps.catalog.models import Document, SourceCode


@shared_task(bind=True, max_retries=5, default_retry_delay=60)
def send_purchase_emails(self, order_id):
    o = Order.objects.select_related("user").get(pk=order_id)
    item = (Document if o.kind == "document" else SourceCode).objects.get(pk=o.item_id)
    seller_email = item.contributor_email
    body = (f"Item: {item.title}\nAmount: NGN {o.amount_kobo/100:,.2f}\nReference: {o.provider_reference}\n"
            f"Order ID: {o.id}\nDate: {o.paid_at:%Y-%m-%d %H:%M} UTC\n")   # no buyer contact details to the author
    try:
        send_mail("New purchase on Ultra Project Library", body, settings.DEFAULT_FROM_EMAIL,
                  [seller_email, settings.UPL_NOTIFY_EMAIL])
        send_mail("Your purchase is confirmed", body + "\nDownload it from your dashboard.",
                  settings.DEFAULT_FROM_EMAIL, [o.user.email])
    except Exception as exc:
        raise self.retry(exc=exc)
