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