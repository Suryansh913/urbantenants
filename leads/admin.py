from django.contrib import admin

from .models import Employee, Lead, StatusUpdate,CustomerContactLog,CustomerLead,PartnerContactLog,PartnerLead


class StatusUpdateInline(admin.TabularInline):
    model = StatusUpdate
    extra = 0
    readonly_fields = ["created_at"]


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ["lead_id", "name", "phone", "city", "budget", "status", "created_at"]
    list_filter = ["status", "city"]
    search_fields = ["lead_id", "name", "phone", "city"]
    inlines = [StatusUpdateInline]


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ["name", "created_at"]


@admin.register(StatusUpdate)
class StatusUpdateAdmin(admin.ModelAdmin):
    list_display = ["lead", "status", "employee", "created_at"]
    list_filter = ["status"]

# ============================================================
# ADD THIS TO admin.py
# Update the top import line:
#   from .models import Employee, Lead, StatusUpdate, PartnerLead, PartnerContactLog, CustomerLead, CustomerContactLog
# ============================================================

class PartnerContactLogInline(admin.TabularInline):
    model = PartnerContactLog
    extra = 0
    readonly_fields = ["contacted_date"]


class CustomerContactLogInline(admin.TabularInline):
    model = CustomerContactLog
    extra = 0
    readonly_fields = ["contacted_date"]


@admin.register(PartnerLead)
class PartnerLeadAdmin(admin.ModelAdmin):
    list_display = ["listing_id", "partner_name", "phone", "location", "status", "contacted", "created_at"]
    list_filter = ["status", "contacted"]
    search_fields = ["listing_id", "partner_name", "phone", "location"]
    inlines = [PartnerContactLogInline]


@admin.register(CustomerLead)
class CustomerLeadAdmin(admin.ModelAdmin):
    list_display = ["customer_id", "customer_name", "phone", "requirement", "contacted", "created_at"]
    list_filter = ["contacted"]
    search_fields = ["customer_id", "customer_name", "phone", "requirement"]
    inlines = [CustomerContactLogInline]