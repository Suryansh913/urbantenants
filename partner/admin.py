from django.contrib import admin
from .models import Partner
from .models import Partner, Coupon, ListingPayment
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

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "discount_percent",
        "discount_amount",
        "max_uses",
        "used_count",
        "valid_from",
        "valid_till",
        "active",
    )

    search_fields = ("code",)

    list_filter = (
        "active",
        "valid_from",
        "valid_till",
    )


@admin.register(ListingPayment)
class ListingPaymentAdmin(admin.ModelAdmin):
    list_display = (
        "partner",
        "cf_order_id",
        "coupon",
        "base_amount",
        "discount_amount",
        "final_amount",
        "status",
        "created_at",
    )

    search_fields = (
        "cf_order_id",
        "partner__full_name",
        "partner__email",
        "coupon__code",
    )

    list_filter = (
        "status",
        "created_at",
    )
