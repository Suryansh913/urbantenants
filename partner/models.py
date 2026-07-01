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