from django.urls import path
from . import views

urlpatterns = [
    path("chat/", views.chat_page, name="chatbot"),
    path("chat-api/", views.chat_api, name="chat_api"),
     
]