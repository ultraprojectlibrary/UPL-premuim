from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django_ratelimit.decorators import ratelimit

from apps.accounts.decorators import verified_required
from apps.accounts.models import User
from apps.core.models import audit
from .forms import DocumentUploadForm
from .models import ModerationStatus
from .tasks import notify_admin_new_upload


@login_required
@verified_required
@ratelimit(key="user", rate="10/h", method="POST", block=True)
def upload_document(request):
    form = DocumentUploadForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        doc = form.save(commit=False)
        doc.contributor = request.user
        doc.status = ModerationStatus.PENDING       # never public until an admin approves
        doc.save()
        if request.user.role == User.Role.STUDENT:
            request.user.role = User.Role.CONTRIBUTOR
            request.user.save(update_fields=["role"])
        audit(request, "document.submitted", doc)
        notify_admin_new_upload.delay(doc.pk)
        messages.success(request, "Submitted. Your document is pending review and will go live once approved.")
        return redirect("dashboard")
    return render(request, "documents/upload.html", {"form": form})
