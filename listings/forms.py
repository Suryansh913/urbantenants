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
        