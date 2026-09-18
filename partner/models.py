from django.db import models

class Partner(models.Model):
    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    service_type = models.CharField(max_length=100)
    password = models.CharField(max_length=255)
    razorpay_account_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    upi_id = models.CharField(max_length=100, blank=True, null=True)
    def __str__(self):
        return self.full_name

# Create your models here.
from django.db import models

from django.db import models
from django.contrib.auth.models import User

class FCMToken(models.Model):
    token = models.TextField(unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    partner = models.ForeignKey('Partner', on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.user:
            return f"User Token - {self.user.email}"
        if self.partner:
            return f"Partner Token - {self.partner.email}"
        return self.token[:20]
    
from django.utils import timezone

 #─────────────────────────────────────────────
# Coupons for the listing-fee discount
# ─────────────────────────────────────────────
class Coupon(models.Model):
    code = models.CharField(max_length=20, unique=True)
    discount_percent = models.PositiveIntegerField(
        default=0, help_text="e.g. 20 for 20% off. Leave 0 if using a flat amount instead."
    )
    discount_amount = models.PositiveIntegerField(
        default=0, help_text="Flat rupee discount. Leave 0 if using a percentage instead."
    )
    max_uses = models.PositiveIntegerField(
        default=0, help_text="0 = unlimited uses"
    )
    used_count = models.PositiveIntegerField(default=0)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_till = models.DateTimeField(null=True, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
 
    def __str__(self):
        return self.code
 
    def is_valid(self):
        now = timezone.now()
        if not self.active:
            return False
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_till and now > self.valid_till:
            return False
        if self.max_uses and self.used_count >= self.max_uses:
            return False
        return True
 
    def calculate_discount(self, amount):
        """Returns the rupee discount for a given base amount, capped at the amount itself."""
        if self.discount_percent:
            return min(amount, (amount * self.discount_percent) // 100)
        return min(amount, self.discount_amount)
 
 
# ─────────────────────────────────────────────
# Tracks the ₹49 listing-fee payment (Cashfree)
#
# `listing` starts out NULL: payment happens BEFORE the listing
# exists (partner pays first, then fills the add-listing form).
# Once the form is submitted, add_listing() links this row to the
# new listing so a paid record can't be reused for a second listing.
# ─────────────────────────────────────────────
class ListingPayment(models.Model):
    STATUS_CHOICES = (
        ('created', 'Created'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    )
 
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE)
    listing = models.ForeignKey('listings.listings', on_delete=models.SET_NULL, null=True, blank=True)
    cf_order_id = models.CharField(max_length=100, unique=True, help_text="Our own order_id, sent to Cashfree")
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    base_amount = models.PositiveIntegerField(default=49)
    discount_amount = models.PositiveIntegerField(default=0)
    final_amount = models.PositiveIntegerField(default=49)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='created')
    created_at = models.DateTimeField(auto_now_add=True)
 
    def __str__(self):
        return f"{self.partner.full_name} - ₹{self.final_amount} - {self.status}"
