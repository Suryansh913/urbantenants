import random
import string

from django.db import models


def generate_lead_id():
    """UT-XXXXX style unique id for a lead, e.g. UT-7F3KQ"""
    while True:
        code = "UT-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
        if not Lead.objects.filter(lead_id=code).exists():
            return code


class Employee(models.Model):
    """A logged-in UrbanTents team member. Created automatically on first login."""
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Lead(models.Model):
    STATUS_ACTIVE = "active"
    STATUS_BOOKED = "booked"
    STATUS_LOST = "lost"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Active"),
        (STATUS_BOOKED, "Booked"),
        (STATUS_LOST, "Lost"),
    ]

    lead_id = models.CharField(max_length=20, unique=True, default=generate_lead_id, editable=False)
    name = models.CharField(max_length=150, verbose_name="Naam")
    phone = models.CharField(max_length=20, verbose_name="Phone Number")
    city = models.CharField(max_length=100, default="Kanpur", verbose_name="Shehar")
    budget = models.CharField(max_length=30, default="2000", verbose_name="Budget (₹)")
    note = models.CharField(max_length=255, blank=True, verbose_name="Note")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_ACTIVE)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name="leads_created"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.lead_id} · {self.name} ({self.get_status_display()})"


class StatusUpdate(models.Model):
    """A single timeline entry for a lead — free text + the status at that point in time."""
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="history")
    text = models.TextField()
    status = models.CharField(max_length=10, choices=Lead.STATUS_CHOICES)
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.lead.lead_id} · {self.status} · {self.created_at:%d %b %H:%M}"