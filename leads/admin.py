from django.contrib import admin

from .models import Employee, Lead, StatusUpdate


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