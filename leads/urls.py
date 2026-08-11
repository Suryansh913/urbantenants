from django.urls import path

from . import views

app_name = "leads"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("", views.dashboard, name="dashboard"),
    path("leads/add/", views.add_lead, name="add_lead"),
    path("leads/<str:lead_id>/edit/", views.edit_lead, name="edit_lead"),
    path("leads/<str:lead_id>/delete/", views.delete_lead, name="delete_lead"),
    path("leads/<str:lead_id>/status/", views.set_status, name="set_status"),
    path("leads/<str:lead_id>/update/", views.add_update, name="add_update"),
]