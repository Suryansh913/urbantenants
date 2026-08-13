from django import forms

from .models import Lead,CustomerLead,PartnerLead


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




# ============================================================
# ADD THIS TO forms.py
# Update the top import line to also pull in PartnerLead, CustomerLead:
#   from .models import Lead, PartnerLead, CustomerLead
# ============================================================

class PartnerLeadForm(forms.ModelForm):
    class Meta:
        model = PartnerLead
        fields = ["listing_id","partner_name", "phone", "location", "status"]
        widgets = {
            "partner_name": forms.TextInput(attrs={"placeholder": "Partner ka naam"}),
            "phone": forms.TextInput(attrs={"placeholder": "98xxxxxxxx"}),
            "location": forms.TextInput(attrs={"placeholder": "Kakadeo"}),
        }


class CustomerLeadForm(forms.ModelForm):
    class Meta:
        model = CustomerLead
        fields = ["customer_name", "phone", "requirement"]
        widgets = {
            "customer_name": forms.TextInput(attrs={"placeholder": "Customer ka naam"}),
            "phone": forms.TextInput(attrs={"placeholder": "98xxxxxxxx"}),
            "requirement": forms.TextInput(attrs={"placeholder": "1 RK, Kanpur"}),
        }