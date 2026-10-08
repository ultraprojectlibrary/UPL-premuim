from datetime import timedelta
from django.conf import settings
from django.db import models, transaction
from django.utils import timezone
from apps.catalog.models import Moderated


class Host(Moderated):
    class Mode(models.TextChoices):
        ONLINE = "online"; PHYSICAL = "physical"; HYBRID = "hybrid"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    session_title = models.CharField(max_length=200)
    display_name = models.CharField(max_length=120)
    profile_image = models.ImageField(upload_to="hosts/", blank=True)
    description = models.TextField()
    email = models.EmailField()
    social_handle = models.CharField(max_length=120, blank=True)
    price_kobo = models.PositiveIntegerField()
    payout_details = models.TextField(blank=True)            # private
    expertise = models.CharField(max_length=200, blank=True)
    years_experience = models.PositiveSmallIntegerField(null=True, blank=True)
    qualification = models.CharField(max_length=200, blank=True)
    location = models.CharField(max_length=120, blank=True)
    mode = models.CharField(max_length=10, choices=Mode.choices, default=Mode.ONLINE)


class Slot(models.Model):
    host = models.ForeignKey(Host, on_delete=models.CASCADE, related_name="slots")
    start_at = models.DateTimeField(db_index=True)
    end_at = models.DateTimeField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=["host", "start_at"], name="uniq_host_slot")]


class Booking(models.Model):
    class Status(models.TextChoices):
        HELD = "held"; CONFIRMED = "confirmed"; EXPIRED = "expired"; CANCELLED = "cancelled"

    slot = models.ForeignKey(Slot, on_delete=models.PROTECT, related_name="bookings")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    order = models.OneToOneField("payments.Order", null=True, on_delete=models.PROTECT)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.HELD)
    held_until = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            # DB-level guarantee: at most ONE active (held/confirmed) booking per slot -> no double booking
            models.UniqueConstraint(fields=["slot"], condition=models.Q(status__in=["held", "confirmed"]),
                                    name="one_active_booking_per_slot"),
        ]


HOLD_MINUTES = 15


@transaction.atomic
def hold_slot(student, slot_id):
    slot = Slot.objects.select_for_update().select_related("host").get(pk=slot_id, host__status="approved")
    if slot.start_at <= timezone.now():
        raise ValueError("Slot is in the past")
    # release stale holds
    Booking.objects.filter(slot=slot, status="held", held_until__lt=timezone.now()).update(status="expired")
    if Booking.objects.filter(slot=slot, status__in=["held", "confirmed"]).exists():
        raise ValueError("Slot is no longer available")
    return Booking.objects.create(slot=slot, student=student,
                                  held_until=timezone.now() + timedelta(minutes=HOLD_MINUTES))
    # price for the payment = slot.host.price_kobo, read here on the server (never from the form)
