from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect


def verified_required(view):
    """Server-side gate: unverified accounts cannot upload or buy."""
    @wraps(view)
    def wrapper(request, *a, **kw):
        if request.user.is_authenticated and not request.user.is_email_verified:
            messages.warning(request, "Please verify your email first. We can resend the link.")
            return redirect("dashboard")
        return view(request, *a, **kw)
    return wrapper
