import logging
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, render
from django_ratelimit.decorators import ratelimit

from apps.payments.models import Entitlement, DownloadLog
from .models import Document, ModerationStatus

log = logging.getLogger("upl.security")


def document_list(request):
    qs = Document.objects.filter(status=ModerationStatus.APPROVED).only(
        "title", "slug", "author_name", "school", "level", "price_kobo", "doc_type")   # no payout/file fields
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(abstract__icontains=q) | Q(author_name__icontains=q))
    for f in ("doc_type", "level"):
        if request.GET.get(f):
            qs = qs.filter(**{f: request.GET[f]})
    page = Paginator(qs.order_by("-created_at"), 12).get_page(request.GET.get("page"))
    return render(request, "documents/list.html", {"page": page, "q": q})


def document_detail(request, slug):
    doc = get_object_or_404(Document, slug=slug, status=ModerationStatus.APPROVED)
    owned = request.user.is_authenticated and Entitlement.objects.filter(
        user=request.user, document=doc, revoked=False).exists()
    return render(request, "documents/detail.html", {"doc": doc, "owned": owned})


@login_required
@ratelimit(key="user", rate="30/h", block=True)
def download_document(request, token):
    """token = Entitlement.download_token (unguessable UUID). The ID in the URL is never trusted alone:
    the entitlement must belong to request.user and be un-revoked."""
    ent = get_object_or_404(Entitlement.objects.select_related("document"),
                            download_token=token, user=request.user, revoked=False)
    doc = ent.document
    if doc is None or doc.status != ModerationStatus.APPROVED:
        raise Http404
    DownloadLog.objects.create(entitlement=ent, user=request.user, ip=request.META.get("REMOTE_ADDR"))
    log.info("download user=%s doc=%s", request.user.pk, doc.pk)
    resp = FileResponse(doc.file.open("rb"), as_attachment=True, filename=f"{doc.slug}.{doc.file.name.rsplit('.',1)[-1]}")
    resp["X-Content-Type-Options"] = "nosniff"
    resp["Cache-Control"] = "private, no-store"
    return resp
