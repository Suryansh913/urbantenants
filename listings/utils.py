import os
import requests
from partner.models import FCMToken

ONESIGNAL_API_KEY = os.getenv("ONESIGNAL_API_KEY")
ONESIGNAL_APP_ID = os.getenv("ONESIGNAL_APP_ID")


def send_booking_notification(booking):

    room = booking.room
    partner = room.partner

    tokens = FCMToken.objects.filter(partner=partner)

    for t in tokens:

        headers = {
            "Authorization": f"Key {ONESIGNAL_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "app_id": ONESIGNAL_APP_ID,
            "include_player_ids": [t.token],
            "headings": {
                "en": "New Booking"
            },
            "contents": {
                "en": f"{booking.name} booked your room. Verify payment now."
            }
        }

        requests.post(
            "https://onesignal.com/api/v1/notifications",
            json=payload,
            headers=headers
        )

import uuid
from django.conf import settings
 
 
def cashfree_headers():
    return {
        "x-client-id": settings.CASHFREE_APP_ID,
        "x-client-secret": settings.CASHFREE_SECRET_KEY,
        "x-api-version": settings.CASHFREE_API_VERSION,
        "Content-Type": "application/json",
    }
 
 
def cashfree_create_order(amount, user, return_url, order_note=""):
    """
    Creates an order on Cashfree and returns the parsed JSON response,
    which includes 'order_id' and 'payment_session_id'.
    """
    order_id = f"CHAT{uuid.uuid4().hex[:20]}"
 
    payload = {
        "order_id": order_id,
        "order_amount": amount,
        "order_currency": "INR",
        "customer_details": {
            "customer_id": f"user_{user.id}",
            "customer_email": user.email or f"user{user.id}@urbantenants.com",
            "customer_phone": getattr(user, "phone", None) or "9999999999",
        },
        "order_meta": {
            "return_url": return_url + f"?order_id={order_id}",
        },
        "order_note": order_note,
    }
    print("CASHFREE ENV:", settings.CASHFREE_ENV)
    print("CASHFREE URL:", settings.CASHFREE_BASE_URL)
    print("APP ID:", settings.CASHFREE_APP_ID[:10], "...")
    resp = requests.post(
        f"{settings.CASHFREE_BASE_URL}/orders",
        json=payload,
        headers=cashfree_headers(),
        timeout=15,
    )
    data = resp.json()
    data["_http_status"] = resp.status_code
    data["_order_id"] = order_id
    return data
 
 
def cashfree_get_order(cf_order_id):
    """Fetches order status from Cashfree to verify payment."""
    resp = requests.get(
        f"{settings.CASHFREE_BASE_URL}/orders/{cf_order_id}",
        headers=cashfree_headers(),
        timeout=15,
    )
    data = resp.json()
    data["_http_status"] = resp.status_code
    return data
