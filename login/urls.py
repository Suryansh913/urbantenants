from django.urls import path
from .import views

urlpatterns = [
    path('register/', views.registerv, name='registerv'),
    path('login/', views.loginv, name='loginv'),
    path('logout/', views.logoutv, name='logoutv'),
    
   
]