from django.db import models

class loginm(models.Model):
    username=models.CharField(max_length=200)
    phone=models.IntegerField( )
    password=models.CharField( max_length=50)

    def __str__(self):
        return self.username



# Create your models here.
# models.py mein add karo

from django import forms
from django.core.exceptions import ValidationError

class SetNewPasswordForm(forms.Form):
    new_password1 = forms.CharField(
        label="Naya Password",
        widget=forms.PasswordInput(attrs={"placeholder": "Naya password"}),
        min_length=8,
    )
    new_password2 = forms.CharField(
        label="Password Confirm karo",
        widget=forms.PasswordInput(attrs={"placeholder": "Password dobara likho"}),
    )

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("new_password1")
        p2 = cleaned.get("new_password2")
        if p1 and p2 and p1 != p2:
            raise ValidationError("Dono passwords match nahi karte.")
        return cleaned