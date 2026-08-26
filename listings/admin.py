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
from .models import Review
admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('name', 'rating', 'created_at', 'is_approved')
    list_filter = ('rating', 'is_approved', 'created_at')
    search_fields = ('name', 'text')
    list_editable = ('is_approved',)



from .models import Participant

@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ("name", "score", "created_at")
    search_fields = ("name",)
    ordering = ("-score", "created_at")




from .models import RakhiRegistration, RakhiSubmission

@admin.register(RakhiRegistration)
class RakhiRegistrationAdmin(admin.ModelAdmin):
    list_display = ('name', 'college', 'contact', 'instagram_handle', 'registered_at')
    search_fields = ('name', 'college', 'contact', 'instagram_handle')
    list_filter = ('registered_at',)
 
 
@admin.register(RakhiSubmission)
class RakhiSubmissionAdmin(admin.ModelAdmin):
    list_display = ('name', 'college', 'output_type', 'submitted_at')
    list_filter = ('output_type', 'submitted_at')
    search_fields = ('name', 'college', 'instagram_handle', 'gemini_prompt')
    readonly_fields = ('submitted_at',)
 