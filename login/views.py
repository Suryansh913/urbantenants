from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from .forms import RegisterForm, LoginForm, SetNewPasswordForm
from django.urls import reverse

def registerv(request):
    if request.user.is_authenticated:
        return redirect('base')
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('base')
        else:
            print(form.errors)
    else:
        form = RegisterForm()
    return render(request, 'pauth/register.html', {'form': form})


def loginv(request):
    if request.user.is_authenticated:
        return redirect('base')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('base')
        else:
            return render(request, 'pauth/login.html', {
                'form': form,
                'error': 'Invalid username or password'
            })
    else:
        form = LoginForm()
    return render(request, 'pauth/login.html', {'form': form})


def logoutv(request):
    logout(request)
    return redirect('loginv')



