import uuid
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class RegisterForm(UserCreationForm):
    name = forms.CharField(max_length=150, required=True, label="Name")
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['name', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Account already exist. Login karo ya doosra email use karo.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['name']
        user.email = self.cleaned_data['email']
        base = "".join(self.cleaned_data['name'].split()).lower() or "user"
        username = f"{base}{uuid.uuid4().hex[:6]}"
        while User.objects.filter(username=username).exists():
            username = f"{base}{uuid.uuid4().hex[:6]}"
        user.username = username
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    username = forms.CharField(max_length=150, label="Email")
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        username_field = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        if username_field and password:
            try:
                user_obj = User.objects.get(email=username_field)
                self.cleaned_data['username'] = user_obj.username
            except User.DoesNotExist:
                pass
        return super().clean()


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