from django.shortcuts import render, redirect, get_object_or_404
from .form import PartnerRegisterForm
from listings.models import listings,Offer
from .form import AddListingForm
from .models import Partner
from django.contrib import messages
from listings.models import listings, RoomBooking
from django.contrib.auth.decorators import login_required
def partner_register(request):
    register_form = PartnerRegisterForm()
    login_error = None
    # 👇 NEW: agar Google se aaya hai to email prefill karo
    prefill_email = request.session.pop('google_prefill_email', None)
    if prefill_email:
        register_form = PartnerRegisterForm(initial={'email': prefill_email})

    if request.method == 'POST':
        # Register form submit
        if 'register_submit' in request.POST:
            register_form = PartnerRegisterForm(request.POST)
            if register_form.is_valid():
                partner = register_form.save()
                request.session['partner_id'] = partner.id
                return redirect('partner_dashboard')

        # Login form submit
        elif 'login_submit' in request.POST:
            email = request.POST.get('login_email')
            password = request.POST.get('login_password')

            try:
                partner = Partner.objects.get(email=email, password=password)
                request.session['partner_id'] = partner.id
                return redirect('partner_dashboard')
            except Partner.DoesNotExist:
                login_error = "Invalid email or password"

    return render(request, 'partner.html', {
        'form': register_form,
        'login_error': login_error
    })
def partner_dashboard(request):
    partner_id = request.session.get('partner_id')

    if not partner_id:
        return redirect('partner_register')

    partner_data = get_object_or_404(Partner, id=partner_id)
    all_listings = listings.objects.filter(partner=partner_data).order_by('-date')
    pending_bookings = RoomBooking.objects.filter(
        room__partner=partner_data,
        status='pending_verification'
    ).select_related('room').order_by('-created_at')

    bookings_data = RoomBooking.objects.filter(
        room__partner=partner_data
    ).select_related('room').order_by('-created_at')

    pending_bookings = bookings_data.filter(status='pending_verification')
    confirmed_bookings = bookings_data.filter(status='confirmed')
    rejected_bookings = bookings_data.filter(status='rejected')

    return render(request, 'partner_dashboard.html', {
         
        'partner_data': partner_data,
        'listings_data': all_listings,
        'bookings_data': bookings_data,
        'pending_bookings': pending_bookings,
        'confirmed_bookings': confirmed_bookings,
        'rejected_bookings': rejected_bookings,
        'pending_bookings': pending_bookings,
    })

def add_listing(request):
    partner_id = request.session.get('partner_id')

    if not partner_id:
        return redirect('partner_register')

    partner_data = get_object_or_404(Partner, id=partner_id)

    if request.method == 'POST':
        form = AddListingForm(request.POST, request.FILES)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.partner = partner_data
            listing.save()
            return redirect('partner_dashboard')
    else:
        form = AddListingForm()

    return render(request, 'add_listing.html', {'form': form})
def partner_logout(request):
    # Session से partner_id हटाएं
    request.session.flush()
    return redirect('partner_register')
def edit_listing(request, listing_id):
    partner_id = request.session.get('partner_id')

    # यदि Partner लॉगिन नहीं है
    if not partner_id:
        return redirect('partner_register')

    partner_data = get_object_or_404(Partner, id=partner_id)

    # केवल उसी Partner की Listing एडिट हो
    listing = get_object_or_404(
        listings,
        id=listing_id,
        partner=partner_data
    )

    if request.method == 'POST':
        form = AddListingForm(request.POST, request.FILES, instance=listing)
        if form.is_valid():
            updated_listing = form.save(commit=False)
            updated_listing.partner = partner_data
            updated_listing.save()
            return redirect('partner_dashboard')
    else:
        form = AddListingForm(instance=listing)

    return render(request, 'edit_listing.html', {'form': form})

# views.py
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import FCMToken
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
import json
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import FCMToken, Partner
from django.template.loader import render_to_string
@csrf_exempt
def save_fcm_token(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Invalid method"}, status=400)

    try:
        data = json.loads(request.body)
        token = data.get("token")

        if not token:
            return JsonResponse({"status": "error", "message": "Token missing"}, status=400)

        partner_id = request.session.get("partner_id")
        obj, created = FCMToken.objects.get_or_create(token=token)

        obj.partner = None
        obj.user = None

        if partner_id:
            obj.partner = Partner.objects.filter(id=partner_id).first()
        elif request.user.is_authenticated:
            obj.user = request.user

        obj.save()

        return JsonResponse({
            "status": "success",
            "token_id": obj.id,
            "user": obj.user.id if obj.user else None,
            "partner": obj.partner.id if obj.partner else None,
        })

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)

from django.http import JsonResponse

# def send_test_notification(request):
#     token_obj = FCMToken.objects.first()

#     if not token_obj:
#         return JsonResponse({"error": "No FCM token found"})

#     message = messaging.Message(
#         notification=messaging.Notification(
#             title="Hello from Firebase",
#             body="Tumhari website par notification successfully kaam kar rahi hai!"
#         ),
#         token=token_obj.token,
#     )

#     response = messaging.send(message)
#     return JsonResponse({"message_id": response})
def verify_booking(request, booking_id):
    partner_id = request.session.get('partner_id')
    if not partner_id:
        return redirect('partner_register')
    partner_data = get_object_or_404(Partner, id=partner_id)
    booking = get_object_or_404(
        RoomBooking,
        id=booking_id,
        room__partner=partner_data
    )
    booking.is_verified = True
    booking.partner_verified = True
    booking.status = 'confirmed'
    booking.verified_on = timezone.now().date()
    booking.save()

    context = {
        "name": booking.name,
        "room_title": booking.room.Room_title,
        "room_type": booking.room.Room_type,
        "rent": booking.room.Room_rent,
        "security": booking.room.Room_security,
        "check_in": booking.check_in_date,
        "partner_phone": booking.room.partner.phone,
    }
    html_content = render_to_string("booking_verified.html", context)

    def send_verified_email():
        import os, requests
        api_key = os.environ.get("BREVO_API_KEY", "")
        url = "https://api.brevo.com/v3/smtp/email"
        headers = {
            "api-key": api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "sender": {"name": "UrbanTenants", "email": "noreply@urbantenants.com"},
            "to": [
                {"email": booking.email},
                {"email": "urbantenants1@gmail.com"}
            ],
            "subject": "Booking Verified - Urban Tenants",
            "htmlContent": html_content
        }
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=10)
            print("BREVO VERIFIED EMAIL:", r.status_code, r.text)
        except Exception as e:
            print("BREVO ERROR:", e)

    import threading
    thread = threading.Thread(target=send_verified_email)
    thread.daemon = True
    thread.start()

    messages.success(request, "Booking verified! Email sent to user.")
    return redirect('partner/dashboard')
def reject_booking(request, booking_id):
    partner_id = request.session.get('partner_id')
    if not partner_id:
        return redirect('partner_register')
    partner_data = get_object_or_404(Partner, id=partner_id)
    booking = get_object_or_404(
        RoomBooking,
        id=booking_id,
        room__partner=partner_data
    )
    booking.partner_verified = False
    booking.status = 'rejected'
    booking.save()

    context = {
        "name": booking.name,
        "room_title": booking.room.Room_title,
        "room_type": booking.room.Room_type,
        "rent": booking.room.Room_rent,
        "check_in": booking.check_in_date,
        "partner_phone": booking.room.partner.phone,
    }
    html_content = render_to_string("booking_rejected.html", context)

    def send_rejected_email():
        import os, requests
        api_key = os.environ.get("BREVO_API_KEY", "")
        url = "https://api.brevo.com/v3/smtp/email"
        headers = {
            "api-key": api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "sender": {"name": "UrbanTenants", "email": "noreply@urbantenants.com"},
            "to": [
                {"email": booking.email},
                {"email": "urbantenants1@gmail.com"}
            ],
            "subject": "Booking Rejected - Urban Tenants",
            "htmlContent": html_content
        }
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=10)
            print("BREVO REJECT EMAIL:", r.status_code, r.text)
        except Exception as e:
            print("BREVO ERROR:", e)

    import threading
    thread = threading.Thread(target=send_rejected_email)
    thread.daemon = True
    thread.start()

    messages.success(request, "Booking rejected. User notified via email.")
    return redirect('partner/dashboard')
import json
from django.http import JsonResponse
from .models import FCMToken, Partner

def save_token(request):

    if request.method == "POST":

        data = json.loads(request.body)
        token = data.get("token")

        partner_id = request.session.get("partner_id")

        partner = Partner.objects.get(id=partner_id)

        FCMToken.objects.update_or_create(
            partner=partner,
            defaults={"token": token}
        )

        return JsonResponse({"status": "saved"})
def edit_listing(request, listing_id):
    partner_id = request.session.get('partner_id')

    if not partner_id:
        return redirect('partner_register')

    partner_data = get_object_or_404(Partner, id=partner_id)

    # 🔥 ONLY OWNER CAN EDIT
    listing = get_object_or_404(
        listings,
        id=listing_id,
        partner=partner_data
    )

    if request.method == 'POST':
        form = AddListingForm(request.POST, request.FILES, instance=listing)

        if form.is_valid():
            updated_listing = form.save(commit=False)
            updated_listing.partner = partner_data
            updated_listing.save()

            messages.success(request, "Listing updated successfully!")
            return redirect('partner_dashboard')

    else:
        form = AddListingForm(instance=listing)

    return render(request, 'edit_listing.html', {
        'form': form,
        'listing': listing
    })
def delete_listing(request, listing_id):
    partner_id = request.session.get('partner_id')

    if not partner_id:
        return redirect('partner_register')

    partner_data = get_object_or_404(Partner, id=partner_id)

    listing = get_object_or_404(
        listings,
        id=listing_id,
        partner=partner_data
    )

    listing.delete()
    messages.success(request, "Listing deleted successfully!")

    return redirect('partner_dashboard')

def set_offer(request, id):
    listing = listings.objects.get(id=id)

    offer, created = Offer.objects.get_or_create(listing=listing)

    if request.method == "POST":
        discount = request.POST.get("discount_percent")

        offer.discount_percent = discount
        offer.active = True
        offer.save()

        return redirect("partner_dashboard")

    return render(request, "set_offer.html", {"listing": listing, "offer": offer})
def remove_offer(request, listing_id):
    listing = get_object_or_404(listings, id=listing_id)

    if hasattr(listing, 'offer'):
        listing.offer.delete()

    return redirect("partner_dashboard")

@login_required
def partner_google_complete(request):
    """
    Google se login hone ke baad yahan aata hai.
    Check karta hai ki is email se koi Partner already registered hai ya nahi.
    """
    email = request.user.email

    try:
        partner = Partner.objects.get(email__iexact=email)
        # Existing partner mil gaya — seedha login kara do
        request.session['partner_id'] = partner.id
        return redirect('partner_dashboard')
    except Partner.DoesNotExist:
        messages.info(request, "You are not a partner yet. Please register first to become a partner, then you can login.")
        request.session['google_prefill_email'] = email
        return redirect('partner_register')


