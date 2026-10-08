from django.conf import settings
from django.db import models
from apps.catalog.models import Moderated


class Placement(Moderated):
    class Type(models.TextChoices):
        IT = "it", "IT Placement"; NYSC = "nysc", "NYSC Placement"; JOB = "job", "Job Placement"

    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    ptype = models.CharField(max_length=5, choices=Type.choices, db_index=True)
    org_name = models.CharField(max_length=200)
    org_email = models.EmailField()
    org_phone = models.CharField(max_length=30)
    org_website = models.URLField(blank=True)
    org_description = models.TextField()                          # required
    title = models.CharField(max_length=200)
    description = models.TextField()
    requirements = models.TextField(blank=True)
    openings = models.PositiveSmallIntegerField(default=1)
    duration = models.CharField(max_length=80, blank=True)
    location = models.CharField(max_length=150, db_index=True)
    nearest_landmark = models.CharField(max_length=200)            # compulsory (blank not allowed)
    salary = models.CharField(max_length=80, blank=True)
    start_date = models.DateField(null=True, blank=True)
    closing_date = models.DateField(null=True, blank=True, db_index=True)
    contact_person = models.CharField(max_length=120)
    contact_phone = models.CharField(max_length=30)
    contact_email = models.EmailField()
    how_to_apply = models.TextField()

    class Meta:
        indexes = [models.Index(fields=["ptype", "status", "-created_at"])]


class Application(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = "submitted"; REVIEW = "review"; SHORTLISTED = "shortlisted"
        REJECTED = "rejected"; ACCEPTED = "accepted"

    placement = models.ForeignKey(Placement, on_delete=models.CASCADE, related_name="applications")
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.SUBMITTED)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["placement", "applicant"], name="one_application_each")]
