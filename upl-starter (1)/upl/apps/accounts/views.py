from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit

from apps.core.models import audit
from apps.payments.models import Entitlement
from apps.catalog.models import Document
from .forms import RegisterForm
from .models import User
from .tasks import send_verification_email
from .tokens import read_token


def _base(request):
    return f"{request.scheme}://{request.get_host()}"


@ratelimit(key="ip", rate="10/h", method="POST", block=True)   # slows mass account creation
def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save(commit=False)
        user.role = User.Role.STUDENT          # always; elevated roles are granted only by admins
        user.is_email_verified = False
        user.save()
        send_verification_email.delay(user.pk, _base(request))
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        messages.success(request, "Account created. Check your email to verify it.")
        return redirect("dashboard")
    return render(request, "accounts/register.html", {"form": form})


def verify_email(request, token):
    data = read_token(token)
    user = User.objects.filter(pk=data["uid"], email=data["email"]).first() if data else None
    if not user:
        return render(request, "accounts/verify_failed.html", status=400)
    if not user.is_email_verified:
        user.is_email_verified = True
        user.save(update_fields=["is_email_verified"])
    messages.success(request, "Email verified. You can now upload and buy.")
    return redirect("dashboard" if request.user.is_authenticated else "login")


@login_required
@require_POST
@ratelimit(key="user", rate="3/h", block=True)
def resend_verification(request):
    if not request.user.is_email_verified:
        send_verification_email.delay(request.user.pk, _base(request))
        messages.info(request, "Verification email sent.")
    return redirect("dashboard")


@login_required
def dashboard(request):
    purchases = (Entitlement.objects.filter(user=request.user, revoked=False, document__isnull=False)
                 .select_related("document").order_by("-created_at")[:50])
    uploads = Document.objects.filter(contributor=request.user).only(
        "title", "status", "review_note", "price_kobo", "created_at").order_by("-created_at")[:50]
    return render(request, "accounts/dashboard.html", {"purchases": purchases, "uploads": uploads})
