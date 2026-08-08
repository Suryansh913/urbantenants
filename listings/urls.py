from django.urls import path
from . import views

urlpatterns = [
    # path('create-order/<int:booking_id>/', views.create_razorpay_order, name='create_booking_order'),
    # path('verify-payment/<int:booking_id>/', views.verify_payment, name='verify_payment'),
 
    # ── Chat unlock (WhatsApp paywall via Cashfree) ──────────────────
    path('room/<int:room_id>/chat-unlock/', views.chat_unlock_plans, name='chat_unlock_plans'),
    path('room/<int:room_id>/chat-unlock/order/', views.chat_unlock_create_order, name='chat_unlock_create_order'),
    path('room/<int:room_id>/chat-unlock/verify/', views.chat_unlock_verify, name='chat_unlock_verify'),
    path('room/<int:room_id>/chat-unlock/use/', views.chat_unlock_use, name='chat_unlock_use'),
]
 
