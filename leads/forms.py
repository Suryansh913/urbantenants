from django import forms

from .models import Lead


class LoginForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        label="Aapka Naam",
        widget=forms.TextInput(attrs={"placeholder": "AAPKA NAAM (employee)", "autocomplete": "off"}),
    )
    passcode = forms.CharField(
        label="Employee Passcode",
        widget=forms.PasswordInput(attrs={"placeholder": "EMPLOYEE PASSCODE", "autocomplete": "off"}),
    )


class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ["name", "phone", "city", "budget", "note"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Customer ka naam"}),
            "phone": forms.TextInput(attrs={"placeholder": "98xxxxxxxx"}),
            "city": forms.TextInput(attrs={"placeholder": "Kanpur"}),
            "budget": forms.TextInput(attrs={"placeholder": "2000"}),
            "note": forms.TextInput(attrs={"placeholder": "Koi extra detail..."}),
        }


class UpdateForm(forms.Form):
    text = forms.CharField(
        label="Update Text",
        widget=forms.Textarea(
            attrs={
                "placeholder": "Jaise: 2 rooms dekh chuka hai / pasand aa gaya / book kar liya...",
                "rows": 3,
            }
        ),
    )
    status = forms.ChoiceField(
        choices=[("", "Isi ke saath status bhi badlein (optional)")] + Lead.STATUS_CHOICES,
        required=False,
    )