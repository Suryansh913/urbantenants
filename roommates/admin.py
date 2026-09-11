from django.contrib import admin

from .models import (
    RoommateBlock,
    RoommateChatSubscription,
    RoommateConnectionRequest,
    RoommateProfile,
    RoommateReport,
)


@admin.register(RoommateProfile)
class RoommateProfileAdmin(admin.ModelAdmin):
    list_display = (
        "full_name", "user", "college", "preferred_location",
        "gender", "budget_min", "budget_max", "is_active", "created_at",
    )
    list_filter = ("gender", "is_active", "accommodation_type", "sharing_type", "college")
    search_fields = ("full_name", "college", "preferred_location", "user__username", "user__email")
    readonly_fields = ("created_at", "updated_at")
    list_per_page = 30


@admin.register(RoommateConnectionRequest)
class RoommateConnectionRequestAdmin(admin.ModelAdmin):
    list_display = ("sender", "receiver", "status", "created_at", "updated_at")
    list_filter = ("status",)
    search_fields = ("sender__username", "receiver__username")
    readonly_fields = ("created_at", "updated_at")


@admin.register(RoommateReport)
class RoommateReportAdmin(admin.ModelAdmin):
    list_display = ("reporter", "reported_user", "reason", "status", "created_at")
    list_filter = ("reason", "status")
    search_fields = ("reporter__username", "reported_user__username", "description")
    list_editable = ("status",)
    readonly_fields = ("created_at",)


@admin.register(RoommateBlock)
class RoommateBlockAdmin(admin.ModelAdmin):
    list_display = ("blocker", "blocked", "created_at")
    search_fields = ("blocker__username", "blocked__username")


@admin.register(RoommateChatSubscription)
class RoommateChatSubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "user", "plan", "amount", "chats_limit", "chats_used",
        "status", "cf_order_id", "created_at",
    )
    list_filter = ("status", "plan")
    search_fields = ("user__username", "cf_order_id")
    readonly_fields = ("created_at", "updated_at")
