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
            'Room_video1',
            'Room_video2',
            'Room_video3',
            'Room_video4',
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
            'bathroom_count', 'bathroom_type',
            'kitchen_count', 'kitchen_type',
            'has_hall', 'hall_count',
            'has_dining_hall',
            'room_count',

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
            'Room_video1': forms.FileInput(attrs={'required': True, 'accept': 'video/*'}),
            'Room_video2': forms.FileInput(attrs={'accept': 'video/*'}),
            'Room_video3': forms.FileInput(attrs={'accept': 'video/*'}),
            'Room_video4': forms.FileInput(attrs={'accept': 'video/*'}),
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
        video1 = cleaned_data.get("Room_video1")

        is_edit = self.instance.pk is not None

        # ── IMAGES CHECK ──
        if is_edit:
            # Edit mode: naya upload nahi kiya to purana wala already hai to chalega
            if not img1 and not self.instance.Room_images1:
                raise forms.ValidationError("First image is required")
            if not img2 and not self.instance.Room_images2:
                raise forms.ValidationError("Second image is required")
        else:
            # New listing: dono images zaroori
            if not img1 or not img2:
                raise forms.ValidationError("First 2 images are required")

        # ── VIDEO CHECK ──
        if is_edit:
            if not video1 and not self.instance.Room_video1:
                raise forms.ValidationError("At least 1 video is required")
        else:
            if not video1:
                raise forms.ValidationError("At least 1 video is required")

        # ── SIZE CHECK ──
        max_video_size = 100 * 1024 * 1024  # 100MB
        for field_name in ['Room_video1', 'Room_video2', 'Room_video3', 'Room_video4']:
            video = cleaned_data.get(field_name)
            if video and hasattr(video, 'size') and video.size > max_video_size:
                raise forms.ValidationError(f"{field_name.replace('_', ' ')} exceeds 100MB limit")

        return cleaned_data