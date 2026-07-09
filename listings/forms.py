from django import forms
from .models import RoomBooking

class RoomBookingForm(forms.ModelForm):
    class Meta:
        model = RoomBooking
        fields = [
            'name',
            'email',
            'phone',
            'check_in_date',
            'payment_done',
            'payment_method',
            'transaction_id',
            'payment_screenshot',
            'feedback',
            
        ]

        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Enter your name'
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'Enter your email'
            }),
            'phone': forms.TextInput(attrs={
                'placeholder': 'Enter phone number'
            }),
            'check_in_date': forms.DateInput(attrs={
                'type': 'date'
            }),
            'payment_method': forms.TextInput(attrs={
                'placeholder': 'Enter payment method (UPI / Bank / Paytm)'
            }),
            'transaction_id': forms.TextInput(attrs={
                'placeholder': 'Enter transaction ID'
            }),
            'feedback': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Any special request or feedback...'
            }),
            
        }
from django import forms
from .models import Review
 
 
class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['name', 'rating', 'text']
 
    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        return name[:60] if name else "Anonymous"
 
    def clean_text(self):
        text = self.cleaned_data.get('text', '').strip()
        if not text:
            raise forms.ValidationError("Please write your review.")
        return text[:220]
 
    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if rating is None or rating < 1 or rating > 5:
            raise forms.ValidationError("Rating must be between 1 and 5.")
        return rating
