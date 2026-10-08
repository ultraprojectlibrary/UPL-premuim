import os
import uuid
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage

private_storage = FileSystemStorage(location=settings.PRIVATE_MEDIA_ROOT)  # swap for private S3 in prod

ALLOWED = {
    ".pdf": (b"%PDF",),
    ".docx": (b"PK\x03\x04",), ".pptx": (b"PK\x03\x04",), ".xlsx": (b"PK\x03\x04",),
    ".zip": (b"PK\x03\x04",),
}
FORBIDDEN_INNER = {".php", ".phtml", ".exe", ".sh", ".bat", ".js", ".py", ".cgi", ".jsp", ".asp", ".aspx", ".html", ".htm", ".svg"}


def validate_upload(f):
    name = os.path.basename(f.name)
    parts = name.lower().split(".")
    if len(parts) > 2 and any("." + p in FORBIDDEN_INNER for p in parts[1:-1]):
        raise ValidationError("Double-extension filenames are not allowed.")
    ext = os.path.splitext(name)[1].lower()
    if ext not in ALLOWED:
        raise ValidationError(f"File type {ext or '(none)'} is not allowed.")
    if f.size > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise ValidationError(f"File exceeds {settings.MAX_UPLOAD_MB} MB.")
    head = f.read(8); f.seek(0)
    if not any(head.startswith(sig) for sig in ALLOWED[ext]):
        raise ValidationError("File content does not match its extension.")


def secure_path(instance, filename):
    """Random server-generated name; the user-supplied name is never used on disk."""
    ext = os.path.splitext(filename)[1].lower()
    return f"{instance.__class__.__name__.lower()}/{uuid.uuid4().hex}{ext}"
