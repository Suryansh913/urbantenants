from django.contrib import admin
from .models import Partner
# Register your models here.
@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "email",
        "phone",
        "service_type",
        "upi_id",
    )

    search_fields = (
        "full_name",
        "email",
        "phone",
        "upi_id",
    )


