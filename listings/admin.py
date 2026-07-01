from django.contrib import admin

from .models import listings,RoomBooking,Offer

admin.site.register(listings)

# Register your models here.
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user","amount","is_paid","created_at")
    

@admin.register(RoomBooking)
class RoomBookingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "email",
        "room",
        "status",
        "payment_done",
        "created_at",
    )

    readonly_fields = (
        "payment_screenshot",
    )

from .models import SupportQuery

@admin.register(SupportQuery)
class SupportQueryAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at', 'resolved')
    list_filter = ('resolved', 'created_at')
    search_fields = ('name', 'email', 'subject')


admin.site.register(Offer)