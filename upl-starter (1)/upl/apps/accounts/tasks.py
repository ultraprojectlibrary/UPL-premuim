from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from .models import User
from .tokens import make_token


@shared_task(bind=True, max_retries=5, default_retry_delay=60)
def send_verification_email(self, user_id, base_url):
    user = User.objects.get(pk=user_id)
    link = f"{base_url}{reverse('verify_email', args=[make_token(user)])}"
    try:
        send_mail("Verify your Ultra Project Library account",
                  f"Hi {user.first_name or user.username},\n\nConfirm your email (link valid for 3 days):\n{link}\n\n"
                  "If you did not create this account, ignore this email.",
                  settings.DEFAULT_FROM_EMAIL, [user.email])
    except Exception as exc:
        raise self.retry(exc=exc)
