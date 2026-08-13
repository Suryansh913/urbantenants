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
    path("partners/", views.partner_leads, name="partner_leads"),
    path("partners/add/", views.add_partner_lead, name="add_partner_lead"),
    path("partners/<str:listing_id>/toggle/", views.toggle_partner_contacted, name="toggle_partner_contacted"),
 
    # Customer Leads
    path("customers/", views.customer_leads, name="customer_leads"),
    path("customers/add/", views.add_customer_lead, name="add_customer_lead"),
    path("customers/<str:customer_id>/toggle/", views.toggle_customer_contacted, name="toggle_customer_contacted"),

]