from django import forms
from .models import Partner

class PartnerRegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = Partner
        fields = [
            'full_name', 'email', 'phone',
            'address', 'service_type', 'password','upi_id'
        ]

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")

        return cleaned_data
    



from listings.models import listings

class AddListingForm(forms.ModelForm):

    class Meta:
        model = listings
        fields = [
            'Room_title',
            'Room_rent',
            'Room_images1',
            'Room_images2',
            'Room_images3',
            'Room_images4',
            'Room_images5',
            'Room_details',
            'Room_available',
            'Room_type',
            'Room_security',
            'wifi',
            'bed',
            'mattres',
            'table',
            'chair',
            'fan',
            'Ac',
            'ro',
            'location_name',
            'latitude',
            'longitude',

        ]

        widgets = {
            'Room_title': forms.TextInput(attrs={'placeholder': 'Enter room title'}),
            'Room_rent': forms.NumberInput(attrs={'placeholder': 'Enter room rent'}),
            'Room_details': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Enter room details'
            }),
            'Room_type': forms.TextInput(attrs={'placeholder': 'Enter room type'}),
            'Room_security': forms.NumberInput(attrs={'placeholder': 'Enter security amount'}),
            'Room_images1': forms.FileInput(attrs={'required': True}),
            'Room_images2': forms.FileInput(attrs={'required': True}),
            'location_name': forms.TextInput(
                attrs={
                    'placeholder': 'Enter location',
                    'class': 'form-control'
                }
            ),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
        }

    def clean(self):
        cleaned_data = super().clean()

        img1 = cleaned_data.get("Room_images1")
        img2 = cleaned_data.get("Room_images2")

        if not img1 or not img2:
            raise forms.ValidationError("First 2 images are required")

        return cleaned_data