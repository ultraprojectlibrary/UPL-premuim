from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render
from apps.catalog.models import ModerationStatus
from .models import Placement


def listing(request, ptype):
    qs = Placement.objects.filter(ptype=ptype, status=ModerationStatus.APPROVED)
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(org_name__icontains=q) | Q(location__icontains=q))
    if request.GET.get("location"):
        qs = qs.filter(location__icontains=request.GET["location"])
    page = Paginator(qs.order_by("-created_at"), 12).get_page(request.GET.get("page"))
    return render(request, "placements/list.html", {"page": page, "ptype": ptype, "q": q})
