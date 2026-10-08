from django.shortcuts import render
from apps.catalog.models import Document, ModerationStatus
from .utils import whatsapp_link

SERVICES = ["Project", "Seminar", "PowerPoint Slide", "Excel Sheet"]


def home(request):
    services = [{"name": s, "url": whatsapp_link(s)} for s in SERVICES]
    latest = (Document.objects.filter(status=ModerationStatus.APPROVED)
              .only("title", "slug", "author_name", "school", "level", "price_kobo")[:8])
    return render(request, "home.html", {"services": services, "latest": latest})
