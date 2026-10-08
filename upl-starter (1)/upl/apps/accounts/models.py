from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = "student", "Student/User"
        CONTRIBUTOR = "contributor", "Contributor"
        HOST = "host", "Host"
        ORGANIZATION = "organization", "Organization"
        ADMIN = "admin", "Admin"
        SUPER_ADMIN = "super_admin", "Super Admin"

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
    is_email_verified = models.BooleanField(default=False)
    phone = models.CharField(max_length=20, blank=True)

    REQUIRED_FIELDS = ["email"]

    @property
    def is_upl_admin(self):
        return self.role in (self.Role.ADMIN, self.Role.SUPER_ADMIN) or self.is_superuser
