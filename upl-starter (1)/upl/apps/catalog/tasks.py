from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from .models import Document


@shared_task
def notify_admin_new_upload(doc_id):
    d = Document.objects.get(pk=doc_id)
    send_mail("Document pending review", f"{d.title}\nBy {d.author_name}\nType: {d.doc_type}",
              settings.DEFAULT_FROM_EMAIL, [settings.UPL_NOTIFY_EMAIL])
