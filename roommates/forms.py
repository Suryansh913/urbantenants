import datetime

from django import forms

from .models import RoommateProfile, RoommateReport


class RoommateProfileForm(forms.ModelForm):
    class Meta:
        model = RoommateProfile
        fields = [
            "profile_photo",
            "full_name",
            "age",
            "gender",
            "college",
            "course",
            "preferred_location",
            "budget_min",
            "budget_max",
            "accommodation_type",
            "sharing_type",
            "move_in_date",
            "food_preference",
            "smoking",
            "drinking",
            "sleep_schedule",
            "cleanliness",
            "study_habits",
            "interests",
            "bio",
            "phone_number",
        ]
        widgets = {
            "move_in_date": forms.DateInput(attrs={"type": "date"}),
            "bio": forms.Textarea(attrs={"rows": 4, "maxlength": 800,
                                          "placeholder": "Tell future roommates a bit about yourself..."}),
            "interests": forms.TextInput(attrs={"placeholder": "e.g. Music, Football, Reading"}),
            "full_name": forms.TextInput(attrs={"placeholder": "Your full name"}),
            "college": forms.TextInput(attrs={"placeholder": "e.g. Chandigarh University"}),
            "course": forms.TextInput(attrs={"placeholder": "e.g. B.Tech CSE"}),
            "preferred_location": forms.TextInput(attrs={"placeholder": "e.g. Gharuan"}),
            "budget_min": forms.NumberInput(attrs={"placeholder": "Min ₹/month"}),
            "budget_max": forms.NumberInput(attrs={"placeholder": "Max ₹/month"}),
            "phone_number": forms.TextInput(attrs={"placeholder": "10-digit mobile number"}),
        }
    def clean_phone_number(self):
        raw = self.cleaned_data.get("phone_number", "").strip()
        if not raw:
            return raw  # optional field

        digits = raw.replace(" ", "").replace("-", "")
        if digits.startswith("+91"):
            digits = digits[3:]
        elif digits.startswith("91") and len(digits) == 12:
            digits = digits[2:]

        if not digits.isdigit() or len(digits) != 10:
            raise forms.ValidationError("Enter a valid 10-digit mobile number.")

        return digits
    def clean_age(self):
        age = self.cleaned_data["age"]
        if age < 16 or age > 100:
            raise forms.ValidationError("Please enter a realistic age (16-100).")
        return age

    def clean_move_in_date(self):
        move_in_date = self.cleaned_data["move_in_date"]
        if move_in_date < datetime.date.today():
            raise forms.ValidationError("Move-in date cannot be in the past.")
        return move_in_date

    def clean(self):
        cleaned_data = super().clean()
        budget_min = cleaned_data.get("budget_min")
        budget_max = cleaned_data.get("budget_max")

        if budget_min is not None and budget_max is not None:
            if budget_min > budget_max:
                raise forms.ValidationError(
                    "Minimum budget cannot be greater than maximum budget."
                )
            if budget_min < 0 or budget_max < 0:
                raise forms.ValidationError("Budget values cannot be negative.")

        return cleaned_data


class RoommateReportForm(forms.ModelForm):
    class Meta:
        model = RoommateReport
        fields = ["reason", "description"]
        widgets = {
            "description": forms.Textarea(attrs={
                "rows": 4,
                "placeholder": "Add any extra details that will help us review this report...",
            }),
        }
