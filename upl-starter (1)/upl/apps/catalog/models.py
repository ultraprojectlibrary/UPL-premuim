import uuid
from django.conf import settings
from django.db import models
from django.utils.text import slugify
from .validators import private_storage, secure_path, validate_upload


class ModerationStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PENDING = "pending", "Pending Review"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
    SUSPENDED = "suspended", "Suspended"
    ARCHIVED = "archived", "Archived"


class Moderated(models.Model):
    status = models.CharField(max_length=12, choices=ModerationStatus.choices,
                              default=ModerationStatus.PENDING, db_index=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                    on_delete=models.SET_NULL, related_name="+")
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        abstract = True


class Document(Moderated):
    class Type(models.TextChoices):
        PROJECT = "project", "Project"
        SEMINAR = "seminar", "Seminar"
        BOOK = "book", "Educational Book"

    class Level(models.TextChoices):
        ND = "ND", "ND"; HND = "HND", "HND"; BSC = "BSc", "BSc"; MSC = "MSc", "Master's"

    doc_type = models.CharField(max_length=10, choices=Type.choices, db_index=True)
    title = models.CharField(max_length=250)
    slug = models.SlugField(max_length=280, unique=True, blank=True)
    author_name = models.CharField(max_length=150)
    abstract = models.TextField()
    school = models.CharField(max_length=200, blank=True)
    department = models.CharField(max_length=200, blank=True)
    level = models.CharField(max_length=5, choices=Level.choices, blank=True)
    price_kobo = models.PositiveIntegerField(help_text="Price in kobo (NGN x 100). Server-side source of truth.")

    contributor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="documents")
    contributor_email = models.EmailField()          # used for sale notifications
    payout_details = models.TextField(blank=True)    # PRIVATE: never rendered in public templates; encrypt at rest
    rights_declared = models.BooleanField(default=False)  # "I have the right to distribute this"

    file = models.FileField(storage=private_storage, upload_to=secure_path, validators=[validate_upload])
    preview_file = models.FileField(storage=private_storage, upload_to=secure_path,
                                    validators=[validate_upload], blank=True)

    class Meta:
        indexes = [models.Index(fields=["status", "doc_type", "-created_at"])]

    @property
    def price_naira(self):
        return self.price_kobo / 100

    def save(self, *a, **kw):
        if not self.slug:
            self.slug = f"{slugify(self.title)[:240]}-{uuid.uuid4().hex[:6]}"
        super().save(*a, **kw)

    def __str__(self):
        return self.title


class SourceCode(Moderated):
    title = models.CharField(max_length=250)
    description = models.TextField(blank=True)
    github_url = models.URLField()                   # PRIVATE until paid
    contributor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    contributor_email = models.EmailField()
    payout_details = models.TextField(blank=True)
    price_kobo = models.PositiveIntegerField()


class Material(Moderated):
    class Kind(models.TextChoices):
        HANDOUT = "handout", "Handout"
        PAST_Q = "past_questions", "Past Questions"

    kind = models.CharField(max_length=20, choices=Kind.choices, db_index=True)
    title = models.CharField(max_length=250)
    school = models.CharField(max_length=200, blank=True)
    level = models.CharField(max_length=5, blank=True)
    file = models.FileField(storage=private_storage, upload_to=secure_path, validators=[validate_upload])
    uploader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    download_count = models.PositiveIntegerField(default=0)


class Course(Moderated):
    title = models.CharField(max_length=250)
    provider_name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    link = models.URLField()
    uploader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    price_kobo = models.PositiveIntegerField(default=0)
