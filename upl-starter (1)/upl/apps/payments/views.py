import hashlib
import hmac
import json
import logging
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit

from apps.catalog.models import Document, ModerationStatus
from . import services
from .models import Order, Entitlement

log = logging.getLogger("upl.payments")


@login_required
@require_POST
@ratelimit(key="user", rate="10/m", block=True)
def buy_document(request, slug):
    doc = get_object_or_404(Document, slug=slug, status=ModerationStatus.APPROVED)
    if Entitlement.objects.filter(user=request.user, document=doc, revoked=False).exists():
        return redirect("document_detail", slug=slug)
    order = services.create_order(request.user, "document", doc)
    url = services.initialize(order, request.build_absolute_uri(reverse("payment_callback")))
    return redirect(url)


@login_required
def callback(request):
    ref = request.GET.get("reference", "")
    order = services.verify_and_fulfil(ref)            # re-verified server-side; query params ignored otherwise
    if not order or order.user_id != request.user.id:
        return render(request, "payment_failed.html", status=403)
    ok = order.status == Order.Status.SUCCESSFUL
    return render(request, "payment_result.html" if ok else "payment_failed.html", {"order": order})


@csrf_exempt                                            # authenticity comes from the HMAC, not a cookie
@require_POST
def paystack_webhook(request):
    sig = request.headers.get("x-paystack-signature", "")
    expected = hmac.new(settings.PAYSTACK_SECRET_KEY.encode(), request.body, hashlib.sha512).hexdigest()
    if not hmac.compare_digest(sig, expected):
        logging.getLogger("upl.security").warning("bad webhook signature from %s", request.META.get("REMOTE_ADDR"))
        return HttpResponse(status=401)
    try:
        event = json.loads(request.body)
    except ValueError:
        return HttpResponseBadRequest()
    if event.get("event") == "charge.success":
        services.verify_and_fulfil(event["data"]["reference"])   # idempotent + re-verifies via API
    return HttpResponse(status=200)
