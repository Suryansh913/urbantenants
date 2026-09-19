import json
import uuid
import threading
import re

import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.conf import settings
from django.db import models as db_models
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.mail import send_mail, EmailMultiAlternatives

from .form import PartnerRegisterForm, AddListingForm
from .models import Partner, FCMToken, Coupon, ListingPayment
from listings.models import listings, Offer, RoomBooking


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
    })


def partner_logout(request):
    # Session से partner_id हटाएं
    request.session.flush()
    return redirect('partner_register')


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
            messages.error(request, "Please fix the errors below.")
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


# ═══════════════════════════════════════════════════════════
# ₹49 listing-fee payment flow — Cashfree, pay BEFORE listing
# ═══════════════════════════════════════════════════════════

LISTING_FEE = 49  # rupees — change this in one place if the price ever changes
COUPON_SESSION_KEY = 'new_listing_coupon'   # holds coupon choice while on the payment page
UNLOCK_SESSION_KEY = 'unlocked_payment_id'  # proves this partner just paid, lets them fill the form once

CASHFREE_BASE_URL = (
    "https://sandbox.cashfree.com/pg" if settings.CASHFREE_ENV == "TEST" else "https://api.cashfree.com/pg"
)
CASHFREE_HEADERS = {
    "x-client-id": settings.CASHFREE_APP_ID,
    "x-client-secret": settings.CASHFREE_SECRET_KEY,
    "x-api-version": "2023-08-01",  # check Cashfree's docs for the current stable version
    "Content-Type": "application/json",
}


def _clean_phone_for_cashfree(raw_phone):
    """
    Cashfree's customer_phone field requires a plain 10-digit Indian
    mobile number — no '+91', spaces, dashes or brackets. Partner.phone
    is a free-text CharField, so it can contain any of those and Cashfree
    will reject the whole order with a 400 if we pass it through as-is.
    """
    digits = re.sub(r'\D', '', str(raw_phone or ''))
    if len(digits) == 10:
        return digits
    if len(digits) == 12 and digits.startswith('91'):
        return digits[2:]
    if len(digits) == 11 and digits.startswith('0'):
        return digits[1:]
    # Fallback dummy — lets the order still go through instead of hard-failing
    # on a partner who registered with a malformed phone number.
    return '9999999999'


def cashfree_create_order(order_id, amount, partner, request):
    """Creates an order on Cashfree and returns the parsed JSON (includes payment_session_id)."""
    # Built from the incoming request, so this works on localhost, ngrok, and production
    # without needing a SITE_URL setting.
    return_url = request.build_absolute_uri(reverse('start_listing_payment')) + "?cf_order_id={order_id}"

    # Cashfree's production API requires an HTTPS return_url. If the app is
    # running behind a proxy (Render, etc.) that doesn't tell Django the
    # original request was HTTPS, build_absolute_uri() can come back as
    # plain http:// even though the site itself is served over https — which
    # Cashfree's production API silently rejects with a 400. Force it here
    # whenever we're not in TEST mode.
    if settings.CASHFREE_ENV != "TEST" and return_url.startswith("http://"):
        return_url = "https://" + return_url[len("http://"):]

    payload = {
        "order_id": order_id,
        "order_amount": amount,
        "order_currency": "INR",
        "customer_details": {
            "customer_id": str(partner.id),
            "customer_name": partner.full_name,
            "customer_email": partner.email,
            "customer_phone": _clean_phone_for_cashfree(partner.phone),
        },
        "order_meta": {
            # "{order_id}" below is a literal Cashfree placeholder — it substitutes it themselves,
            # this is NOT a Python f-string variable.
            "return_url": return_url,
        },
    }
    resp = requests.post(f"{CASHFREE_BASE_URL}/orders", json=payload, headers=CASHFREE_HEADERS, timeout=15)

    if resp.status_code not in (200, 201):
        # Surface Cashfree's actual error message instead of a bare "400 Bad Request"
        # so the real reason (bad phone, bad amount, etc.) is visible in the logs
        # and in the error shown on the payment page.
        try:
            detail = resp.json().get("message", resp.text)
        except Exception:
            detail = resp.text
        print("🔥 CASHFREE ORDER CREATE FAILED:", resp.status_code, detail, flush=True)
        print("🔥 Payload sent:", payload, flush=True)
        raise Exception(detail)

    return resp.json()


def cashfree_get_order(order_id):
    """Server-to-server status check — this is the source of truth, never trust the client alone."""
    resp = requests.get(f"{CASHFREE_BASE_URL}/orders/{order_id}", headers=CASHFREE_HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.json()


def _mark_payment_paid(payment):
    payment.status = 'paid'
    payment.save()
    if payment.coupon_id:
        Coupon.objects.filter(id=payment.coupon_id).update(used_count=db_models.F('used_count') + 1)


def start_listing_payment(request):
    """Landing point for the 'Add Listing' button: pay first, form comes after."""
    partner_id = request.session.get('partner_id')
    if not partner_id:
        return redirect('partner_register')
    partner_data = get_object_or_404(Partner, id=partner_id)

    # Already paid in this session and haven't used it yet? Skip straight to the form.
    unlocked_id = request.session.get(UNLOCK_SESSION_KEY)
    if unlocked_id and ListingPayment.objects.filter(
        id=unlocked_id, partner=partner_data, status='paid', listing__isnull=True
    ).exists():
        return redirect('add_listing')

    # Cashfree redirected the whole page back here (happens with some UPI apps) instead of
    # resolving inside the modal — check that order's status and unlock if it went through.
    cf_order_id = request.GET.get('cf_order_id')
    if cf_order_id:
        payment = ListingPayment.objects.filter(cf_order_id=cf_order_id, partner=partner_data).first()
        if payment and payment.status != 'paid':
            try:
                order = cashfree_get_order(cf_order_id)
                if order.get('order_status') == 'PAID':
                    _mark_payment_paid(payment)
                    request.session[UNLOCK_SESSION_KEY] = payment.id
                    request.session.pop(COUPON_SESSION_KEY, None)
                    return redirect('add_listing')
            except Exception:
                pass  # fall through to showing the payment page again

    coupon_info = request.session.get(COUPON_SESSION_KEY, {})
    final_amount = coupon_info.get('final_amount', LISTING_FEE)

    return render(request, 'listing_payment.html', {
        'base_amount': LISTING_FEE,
        'final_amount': final_amount,
        'discount': coupon_info.get('discount', 0),
        'coupon_code': coupon_info.get('coupon_code', ''),
        'cashfree_mode': 'sandbox' if settings.CASHFREE_ENV == 'TEST' else 'production',
    })


def apply_coupon(request):
    """AJAX endpoint: validates a coupon code and stashes the discount in session."""
    partner_id = request.session.get('partner_id')
    if not partner_id:
        return JsonResponse({'valid': False, 'message': 'Please log in again.'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'valid': False, 'message': 'Invalid method'}, status=400)

    code = request.POST.get('coupon_code', '').strip().upper()

    if not code:
        request.session.pop(COUPON_SESSION_KEY, None)
        return JsonResponse({'valid': False, 'message': 'Enter a coupon code', 'final_amount': LISTING_FEE})

    try:
        coupon = Coupon.objects.get(code__iexact=code)
    except Coupon.DoesNotExist:
        return JsonResponse({'valid': False, 'message': 'Invalid coupon code'})

    if not coupon.is_valid():
        return JsonResponse({'valid': False, 'message': 'This coupon has expired or is no longer active'})

    discount = coupon.calculate_discount(LISTING_FEE)
    final_amount = max(0, LISTING_FEE - discount)

    request.session[COUPON_SESSION_KEY] = {
        'coupon_id': coupon.id,
        'coupon_code': coupon.code,
        'discount': discount,
        'final_amount': final_amount,
    }

    return JsonResponse({
        'valid': True,
        'message': f'Coupon applied — you saved ₹{discount}',
        'discount': discount,
        'final_amount': final_amount,
    })


def create_listing_order(request):
    """AJAX endpoint: creates the Cashfree order (or unlocks instantly on a 100%-off coupon)."""
    import traceback

    partner_id = request.session.get('partner_id')
    if not partner_id:
        return JsonResponse({'error': 'Not logged in'}, status=403)
    partner_data = get_object_or_404(Partner, id=partner_id)

    coupon_info = request.session.get(COUPON_SESSION_KEY, {})
    final_amount = coupon_info.get('final_amount', LISTING_FEE)
    coupon_id = coupon_info.get('coupon_id')

    print("🔥 CREATE_LISTING_ORDER CALLED — partner:", partner_id, "final_amount:", final_amount, flush=True)

    # Everything below can fail for many different reasons (Cashfree API,
    # DB constraint, etc.) — wrap the whole thing so the browser ALWAYS gets
    # back JSON with the real reason, never a raw Django 500 HTML page that
    # breaks response.json() on the frontend.
    try:
        if final_amount <= 0:
            payment = ListingPayment.objects.create(
                partner=partner_data,
                cf_order_id=f"free_{uuid.uuid4().hex[:12]}",
                coupon_id=coupon_id,
                base_amount=LISTING_FEE,
                discount_amount=coupon_info.get('discount', 0),
                final_amount=0,
                status='paid',
            )
            if coupon_id:
                Coupon.objects.filter(id=coupon_id).update(used_count=db_models.F('used_count') + 1)
            request.session[UNLOCK_SESSION_KEY] = payment.id
            request.session.pop(COUPON_SESSION_KEY, None)
            return JsonResponse({'free': True, 'redirect_url': reverse('add_listing')})

        order_id = f"listing_{partner_data.id}_{uuid.uuid4().hex[:10]}"

        cf_order = cashfree_create_order(order_id, final_amount, partner_data, request)
        print("🔥 CASHFREE ORDER CREATED OK:", cf_order, flush=True)

        ListingPayment.objects.create(
            partner=partner_data,
            cf_order_id=order_id,
            coupon_id=coupon_id,
            base_amount=LISTING_FEE,
            discount_amount=coupon_info.get('discount', 0),
            final_amount=final_amount,
            status='created',
        )

        if not cf_order.get('payment_session_id'):
            print("🔥 WARNING: Cashfree response had NO payment_session_id:", cf_order, flush=True)
            return JsonResponse({'error': f"Cashfree did not return a payment session. Response: {cf_order}"}, status=502)

        return JsonResponse({
            'payment_session_id': cf_order.get('payment_session_id'),
            'cf_order_id': order_id,
            'amount': final_amount,
        })

    except Exception as e:
        print("🔥🔥🔥 CREATE_LISTING_ORDER CRASHED:", repr(e), flush=True)
        traceback.print_exc()
        return JsonResponse({'error': f'Could not start payment: {e}'}, status=502)


def verify_listing_payment(request):
    """AJAX endpoint: called after the Cashfree checkout closes. Confirms with Cashfree server-side."""
    import traceback

    partner_id = request.session.get('partner_id')
    if not partner_id:
        return JsonResponse({'success': False, 'message': 'Not logged in'}, status=403)
    partner_data = get_object_or_404(Partner, id=partner_id)

    cf_order_id = request.POST.get('cf_order_id')
    payment = get_object_or_404(ListingPayment, cf_order_id=cf_order_id, partner=partner_data)

    if payment.status == 'paid':
        request.session[UNLOCK_SESSION_KEY] = payment.id
        return JsonResponse({'success': True, 'redirect_url': reverse('add_listing')})

    try:
        order = cashfree_get_order(cf_order_id)

        if order.get('order_status') == 'PAID':
            _mark_payment_paid(payment)
            request.session[UNLOCK_SESSION_KEY] = payment.id
            request.session.pop(COUPON_SESSION_KEY, None)
            return JsonResponse({'success': True, 'redirect_url': reverse('add_listing')})

        payment.status = 'failed'
        payment.save()
        return JsonResponse({'success': False, 'message': 'Payment was not completed. Please try again.'})

    except Exception as e:
        print("🔥🔥🔥 VERIFY_LISTING_PAYMENT CRASHED:", repr(e), flush=True)
        traceback.print_exc()
        return JsonResponse({'success': False, 'message': f'Could not confirm payment: {e}'}, status=502)


def add_listing(request):
    """Only reachable after start_listing_payment has unlocked this partner for one listing."""
    partner_id = request.session.get('partner_id')
    if not partner_id:
        return redirect('partner_register')
    partner_data = get_object_or_404(Partner, id=partner_id)

    unlocked_id = request.session.get(UNLOCK_SESSION_KEY)
    payment = ListingPayment.objects.filter(
        id=unlocked_id, partner=partner_data, status='paid', listing__isnull=True
    ).first() if unlocked_id else None

    if not payment:
        messages.info(request, "Pay the ₹49 listing fee first — then you can add your listing.")
        return redirect('start_listing_payment')

    if request.method == 'POST':
        form = AddListingForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                listing = form.save(commit=False)
                listing.partner = partner_data
                listing.payment_status = 'paid'  # fee was already collected before this form
                listing.save()

                payment.listing = listing
                payment.save()
                request.session.pop(UNLOCK_SESSION_KEY, None)

                messages.success(request, "Listing published successfully!")
                return redirect('partner_dashboard')
            except Exception as e:
                messages.error(request, f"Upload failed, please try again. ({str(e)})")
                return render(request, 'add_listing.html', {'form': form})
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = AddListingForm()

    return render(request, 'add_listing.html', {'form': form})


# ═══════════════════════════════════════════════════════════
# Your existing FCM / booking-verification code, unchanged
# ═══════════════════════════════════════════════════════════

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
        import os
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
        import os
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

    thread = threading.Thread(target=send_rejected_email)
    thread.daemon = True
    thread.start()

    messages.success(request, "Booking rejected. User notified via email.")
    return redirect('partner/dashboard')


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