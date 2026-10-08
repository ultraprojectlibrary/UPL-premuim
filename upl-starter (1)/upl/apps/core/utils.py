from urllib.parse import quote
from .models import SiteSetting


def whatsapp_link(service_name: str) -> str:
    number = SiteSetting.all_dict().get("whatsapp_number", "").lstrip("+").replace(" ", "")
    text = f"Hey, good day. I will need your service for {service_name}."
    return f"https://wa.me/{number}?text={quote(text)}"
