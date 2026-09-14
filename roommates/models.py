"""
roommates/models.py

All models for the Find Roommate feature.
Every model links back to settings.AUTH_USER_MODEL so it automatically uses
whatever User model (custom or default) UrbanTenants already has. No second
authentication system, no duplicate user table.
"""

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from cloudinary.models import CloudinaryField

# ---------------------------------------------------------------------------
# CHOICES
# ---------------------------------------------------------------------------

class Gender(models.TextChoices):
    MALE = "male", "Male"
    FEMALE = "female", "Female"
    PREFER_NOT_TO_SAY = "prefer_not_to_say", "Prefer not to say"


class AccommodationType(models.TextChoices):
    ROOM = "room", "Room"
    PG = "pg", "PG"
    FLAT = "flat", "Flat"


class SharingType(models.TextChoices):
    SINGLE = "single", "Single"
    DOUBLE = "double", "Double"
    TRIPLE = "triple", "Triple"


class FoodPreference(models.TextChoices):
    VEG = "veg", "Veg"
    NON_VEG = "non_veg", "Non-Veg"
    BOTH = "both", "Both"


class YesNo(models.TextChoices):
    YES = "yes", "Yes"
    NO = "no", "No"


class SleepSchedule(models.TextChoices):
    EARLY_SLEEPER = "early_sleeper", "Early Sleeper"
    FLEXIBLE = "flexible", "Flexible"
    NIGHT_OWL = "night_owl", "Night Owl"


class Cleanliness(models.TextChoices):
    VERY_CLEAN = "very_clean", "Very Clean"
    MODERATE = "moderate", "Moderate"
    FLEXIBLE = "flexible", "Flexible"


class StudyHabits(models.TextChoices):
    QUIET = "quiet", "Quiet"
    SOMETIMES_MUSIC = "sometimes_music", "Sometimes Music"
    SOCIAL = "social", "Social"


# ---------------------------------------------------------------------------
# ROOMMATE PROFILE
# ---------------------------------------------------------------------------

class RoommateProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="roommate_profile",
    )

    profile_photo = CloudinaryField(
        'image',
        blank=True,
        null=True
    )
    full_name = models.CharField(max_length=150)
    age = models.PositiveSmallIntegerField()
    gender = models.CharField(max_length=20, choices=Gender.choices)

    college = models.CharField(max_length=200)
    course = models.CharField(max_length=150, blank=True)

    preferred_location = models.CharField(max_length=150)
    budget_min = models.PositiveIntegerField()
    budget_max = models.PositiveIntegerField()

    accommodation_type = models.CharField(max_length=10, choices=AccommodationType.choices)
    sharing_type = models.CharField(max_length=10, choices=SharingType.choices)
    move_in_date = models.DateField()

    food_preference = models.CharField(max_length=10, choices=FoodPreference.choices)
    smoking = models.CharField(max_length=3, choices=YesNo.choices, default=YesNo.NO)
    drinking = models.CharField(max_length=3, choices=YesNo.choices, default=YesNo.NO)
    sleep_schedule = models.CharField(max_length=20, choices=SleepSchedule.choices)
    cleanliness = models.CharField(max_length=15, choices=Cleanliness.choices)
    study_habits = models.CharField(max_length=20, choices=StudyHabits.choices)

    interests = models.CharField(
        max_length=300, blank=True,
        help_text="Comma-separated, e.g. Music, Football, Reading"
    )
    bio = models.TextField(max_length=800, blank=True)
    phone_number = models.CharField(
        max_length=10,
        blank=True,
        help_text="10-digit mobile number. Only shown to users who've unlocked chat credits.",
    )

    is_active = models.BooleanField(default=True, help_text="Uncheck to hide profile from search")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_active"]),
            models.Index(fields=["preferred_location"]),
            models.Index(fields=["college"]),
        ]

    def __str__(self):
        return f"{self.full_name} ({self.user})"

    def get_absolute_url(self):
        return reverse("roommates:roommate-detail", kwargs={"pk": self.pk})

    @property
    def interests_list(self):
        return [i.strip() for i in self.interests.split(",") if i.strip()]


# ---------------------------------------------------------------------------
# CONNECTION REQUESTS
# ---------------------------------------------------------------------------

class RoommateConnectionRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"
        CANCELLED = "cancelled", "Cancelled"

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="sent_roommate_requests",
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="received_roommate_requests",
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["sender", "receiver"],
                condition=models.Q(status="pending"),
                name="unique_pending_roommate_request",
            )
        ]

    def __str__(self):
        return f"{self.sender} -> {self.receiver} ({self.status})"


# ---------------------------------------------------------------------------
# REPORTS
# ---------------------------------------------------------------------------

class RoommateReport(models.Model):
    class Reason(models.TextChoices):
        FAKE_PROFILE = "fake_profile", "Fake Profile"
        HARASSMENT = "harassment", "Harassment"
        INAPPROPRIATE = "inappropriate", "Inappropriate Content"
        SPAM = "spam", "Spam"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        REVIEWING = "reviewing", "Reviewing"
        RESOLVED = "resolved", "Resolved"
        DISMISSED = "dismissed", "Dismissed"

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="filed_roommate_reports",
    )
    reported_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="roommate_reports_against",
    )
    reason = models.CharField(max_length=20, choices=Reason.choices)
    description = models.TextField(max_length=1000, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Report by {self.reporter} on {self.reported_user} ({self.reason})"


# ---------------------------------------------------------------------------
# BLOCKING
# ---------------------------------------------------------------------------

class RoommateBlock(models.Model):
    blocker = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="roommate_blocks_made",
    )
    blocked = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="roommate_blocks_received",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["blocker", "blocked"], name="unique_roommate_block")
        ]

    def __str__(self):
        return f"{self.blocker} blocked {self.blocked}"


# ---------------------------------------------------------------------------
# PAID CHAT UNLOCK (Cashfree) — mirrors the existing ChatSubscription pattern
# used for room listings, but scoped to the roommate feature (not tied to a
# single room). ₹9 unlocks 5 roommate chats.
# ---------------------------------------------------------------------------

class RoommateChatSubscription(models.Model):
    PLAN_BASIC5 = "basic5"

    PLAN_CHOICES = [
        (PLAN_BASIC5, "5 Chats - ₹9"),
    ]

    PLAN_PRICES = {
        PLAN_BASIC5: 9,
    }

    PLAN_CHATS = {
        PLAN_BASIC5: 5,
    }

    STATUS_CREATED = "created"
    STATUS_PAID = "paid"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_CREATED, "Created"),
        (STATUS_PAID, "Paid"),
        (STATUS_FAILED, "Failed"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="roommate_chat_subscriptions",
    )
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default=PLAN_BASIC5)
    amount = models.PositiveIntegerField(default=9)
    chats_limit = models.PositiveIntegerField(default=5)
    chats_used = models.PositiveIntegerField(default=0)

    cf_order_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    cf_payment_session_id = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_CREATED)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} - {self.plan} - {self.status}"

    @property
    def chats_remaining(self):
        return max(self.chats_limit - self.chats_used, 0)

    @classmethod
    def total_remaining_for_user(cls, user):
        """Sum of remaining chats across all this user's PAID subscriptions."""
        subs = cls.objects.filter(user=user, status=cls.STATUS_PAID)
        return sum(s.chats_remaining for s in subs)

    @classmethod
    def consume_one_for_user(cls, user):
        """
        Deducts one chat credit from the oldest PAID subscription that still
        has credits left. Returns True if a credit was consumed.
        """
        subs = cls.objects.filter(user=user, status=cls.STATUS_PAID).order_by("created_at")
        for sub in subs:
            if sub.chats_remaining > 0:
                sub.chats_used += 1
                sub.save(update_fields=["chats_used", "updated_at"])
                return True
        return False
