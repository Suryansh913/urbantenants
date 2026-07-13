from django.urls import path
from . import views
from .views import save_fcm_token

urlpatterns = [
    path('register/', views.partner_register, name='partner_register'),
    path('dashboard/', views.partner_dashboard, name='partner_dashboard'),
    path('add-listing/', views.add_listing, name='add_listing'),
    path('logout/', views.partner_logout, name='partner_logout'),
    path("save-fcm-token/", save_fcm_token, name="save_fcm_token"),
    path("save-token/", views.save_token, name="save_token"),
    path('delete-listing/<int:listing_id>/', views.delete_listing, name='delete_listing'),
    path('verify-booking/<int:booking_id>/', views.verify_booking, name='verify_booking'),
    path('reject-booking/<int:booking_id>/', views.reject_booking, name='reject_booking'),
    path('partner/edit-listing/<int:listing_id>/', views.edit_listing, name='edit_listing'),
    path("set-offer/<int:id>/", views.set_offer, name="set_offer"),
    path("remove-offer/<int:listing_id>/", views.remove_offer, name="remove_offer"),
    path('google-complete/', views.partner_google_complete, name='partner_google_complete'),
    
    
 

]