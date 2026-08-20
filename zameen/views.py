from django.http import HttpResponse
from django.shortcuts import render,get_object_or_404,redirect
from listings.models import listings, Booking , RoomBooking,Order,RoomRating,ChatSubscription
from listings.forms import RoomBookingForm
from django.contrib.auth.decorators import login_required
from listings.models import RoomBooking
from django.template.loader import get_template
from xhtml2pdf import pisa
from listings.utils import send_booking_notification
import razorpay
import qrcode
from django.db.models import Avg
from django.core.mail import EmailMessage
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from io import BytesIO
from base64 import b64encode
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.core.mail import send_mail
import requests
import os
def send_brevo_email(to_emails, subject, html_content):
    
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "api-key": os.environ.get("BREVO_API_KEY", ""), # Step 4 mein replace karenge
        "Content-Type": "application/json"
    }
    payload = {
        "sender": {"name": "UrbanTenants", "email": "noreply@urbantenants.com"},
        "to": [{"email": e} for e in to_emails],
        "subject": subject,
        "htmlContent": html_content
    }
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=10)
        print("BREVO RESPONSE:", r.status_code, r.text)
    except Exception as e:
        print("BREVO ERROR:", e)





def submit_review(request, room_id):
    print("VIEW HIT")
    if request.method == "POST":

        room = listings.objects.get(id=room_id)

        rating = request.POST.get("rating")
        review = request.POST.get("review")
       

        RoomRating.objects.create(
            room=room,
            
            rating=rating,
            review=review
        )
        messages.success(request, "Rating Submitted Successfully!")
    print("RATING SAVED")
    return redirect(request.META.get("HTTP_REFERER"))

 















def login(request):
    final=0
    data={}
    try:
        if request.method=="post":
        
            user = request.POST.get['user']
            phone = request.POST.get['phone']
            adhar = request.POST.get['adhar']
            password = request.POST.get['password']
            final=phone
            data={
                'u':user,
                'phone': phone,
                'password':password,
                'adhar': adhar,
            }
    except:
        pass

    
    return render(request, "login.html",data)
# is view se mai ek listing ka data dekh sakat ahu
import re

def get_clean_whatsapp_number(phone):
    """Return a valid wa.me number: country code + 10 digit number, digits only."""
    default_number = "918303970186"
    if not phone:
        return default_number

    digits = re.sub(r'\D', '', str(phone))  # remove +, spaces, dashes, brackets etc.

    if len(digits) == 10:
        # plain 10 digit number -> add country code
        return "91" + digits
    elif len(digits) == 12 and digits.startswith("91"):
        # already has country code
        return digits
    elif len(digits) == 11 and digits.startswith("0"):
        # leading zero, strip it, add country code
        return "91" + digits[1:]
    else:
        # fallback if format is weird/unexpected
        return default_number


def room(request, id):
    roomd = get_object_or_404(listings, id=id)
    listing = listings.objects.get(id=id)
    listingdata = listings.objects.all()

    reviews = roomd.ratings.all().order_by('-created_at')

    star_counts = {}
    for s in range(1, 6):
        star_counts[s] = roomd.ratings.filter(rating=s).count()

    total = roomd.total_reviews
    star_bars = []
    for s in [5, 4, 3, 2, 1]:
        count = star_counts.get(s, 0)
        pct = round((count / total * 100) if total > 0 else 0)
        star_bars.append({'star': s, 'count': count, 'pct': pct})

    final_price = listing.Room_rent
    if hasattr(listing, 'offer') and listing.offer.active:
        discount = listing.offer.discount_percent
        final_price = listing.Room_rent - (listing.Room_rent * discount / 100)

    data = {
        'listingdata': listingdata,
    }

    images = [
        listing.Room_images1,
        listing.Room_images2,
        listing.Room_images3,
        listing.Room_images4,
        listing.Room_images5,
    ]

    # ---- WhatsApp number cleanup ----
    partner_phone = None
    if hasattr(listing, 'partner') and listing.partner and listing.partner.phone:
        partner_phone = listing.partner.phone

    whatsapp_number = get_clean_whatsapp_number(partner_phone)

    # ---- Chat unlock (WhatsApp paywall via Cashfree) ----
    chat_sub = None
    if request.user.is_authenticated:
        chat_sub = ChatSubscription.get_active_for(request.user, roomd)

    chat_plans = [
        {
            'key': ChatSubscription.PLAN_BASIC,
            'label': 'Basic',
            'price': ChatSubscription.PLAN_PRICES[ChatSubscription.PLAN_BASIC],
            'desc': f'{ChatSubscription.PLAN_CHAT_LIMIT[ChatSubscription.PLAN_BASIC]} chats · valid {ChatSubscription.VALIDITY_DAYS} days',
        },
        {
            'key': ChatSubscription.PLAN_UNLIMITED,
            'label': 'Unlimited',
            'price': ChatSubscription.PLAN_PRICES[ChatSubscription.PLAN_UNLIMITED],
            'desc': f'Unlimited chats · valid {ChatSubscription.VALIDITY_DAYS} days',
        },
    ]
    is_liked = False
    if request.user.is_authenticated:
        is_liked = roomd.likes.filter(user=request.user).exists()
    return render(request, "room.html", {
        'room': roomd,
        'images': images,
        'data': data,
        'reviews': reviews,
        'is_liked': is_liked,
        'star_bars': star_bars,
        'final_price': final_price,
        'whatsapp_number': whatsapp_number,
        'chat_sub': chat_sub,
        'chat_plans': chat_plans,
        'cashfree_mode': 'sandbox' if settings.CASHFREE_ENV == 'TEST' else 'production',
    })
def base(request):
    from django.db.models import Avg, Count
    from listings.models import Review          # <-- NEW: import your Review model

    User = get_user_model()
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            email='your@email.com',
            password='StrongPassword123'
        )
    title = request.GET.get('search')
    listingdata = listings.objects.filter(Room_available=True).order_by('-date').annotate(
        avg_rating=Avg('ratings__rating'),
        review_count=Count('ratings')
    )
    if title:
        listingdata = listingdata.filter(Room_title__icontains=title)
    paginator = Paginator(listingdata, 30)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    for listing in page_obj:
        avg = listing.avg_rating or 0
        listing.filled_stars = range(1, round(avg) + 1)
        listing.empty_stars  = range(round(avg) + 1, 6)
        if hasattr(listing, 'offer') and listing.offer and listing.offer.discount_percent:
            discount = (listing.Room_rent * listing.offer.discount_percent) / 100
            listing.final_price = round(listing.Room_rent - discount)
        else:
            listing.final_price = listing.Room_rent

    # === NEW: fetch site reviews for the homepage marquee ===
    site_reviews = Review.objects.filter(is_approved=True)[:30]
    site_review_count = Review.objects.filter(is_approved=True).count()
    site_avg_rating = Review.objects.filter(is_approved=True).aggregate(Avg('rating'))['rating__avg'] or 0

    return render(request, "base.html", {
        'listingdata': page_obj,
        'page_obj': page_obj,
        'title': title,
        # === NEW: pass reviews to template ===
        'reviews': site_reviews,
        'review_count': site_review_count,
        'avg_rating': site_avg_rating,
    })
def bhk2(request):
    listingdata = listings.objects.filter(
        Room_title__icontains="2"
    )
    title=request.GET.get('search')
    if title:
        listingdata=listingdata.filter(Room_title__icontains=title)
    data={
        'listingdata':listingdata,
        'title':title
    }

    return render(request, "bhk2.html",data)
def AboutUs(response):
    

    return render(response, "About-Us.html")
def bhk3(response):
    listingdata=listings.objects.filter(Room_title__icontains="3")
    data={
        'listingdata':listingdata
    }

    return render(response, "bhk3.html",data)
def pg(response):
    listingdata=listings.objects.filter(Room_title__icontains="pg")
    data={
        'listingdata':listingdata
    }

    return render(response, "pg.html",data)
from django.shortcuts import render, get_object_or_404

# def bookingcon(request, id):
#     bookingdata = get_object_or_404(RoomBooking, id=id)
#     roomt = bookingdata.room   # yahan room foreign key ka field name use hoga

#     return render(request, "bookingconfirm.html", {
#         'room': roomt,
#         'bookingd': bookingdata
#     })
@login_required
def mybooking(request):
    bookings = RoomBooking.objects.select_related('room').filter(
        email=request.user.email,
         status='confirmed'
    ).order_by('-created_at')

    return render(request, 'mybooking.html', {
        'bookings': bookings
    })


def more(request):
    listingdata=listings.objects.all()
    
    data={
        'listingdata':listingdata,
        
    }

    

    return render(request, "more.html",data )
def bookingform(request, id):
    roomd = get_object_or_404(listings, id=id)
    
    upi_id = "8303970186@ybl"
    qr_code = None
    if roomd.partner:
        upi_id = roomd.partner.upi_id if roomd.partner and roomd.partner.upi_id else "8303970186@ybl"

        print("UPI ID =", repr(upi_id))
        print("Rent =", repr(roomd.Room_rent))

        upi_url = f"upi://pay?pa={upi_id}&pn=UrbanTenants&am={roomd.Room_rent}&cu=INR"
        qr = qrcode.make(upi_url)
        buffer = BytesIO()
        qr.save(buffer, format='PNG')

        qr_code = b64encode(buffer.getvalue()).decode()
        context = {
        'room': roomd,
        'upi_id': upi_id,
        'qr_code': qr_code,
        'upi_url': upi_url,
    }



    if request.method == 'POST':
        form = RoomBookingForm(request.POST, request.FILES)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.room = roomd
            booking.partner_verified = False
            booking.status = 'pending_verification'

            

            booking.save()
            if roomd.partner:

                subject = "New Booking Request - Verify Now"

                email_context = {
                    "partner_name": roomd.partner.full_name,
                    "partner_phone": roomd.partner.phone,
                    "user_name": booking.name,
                    "user_email": booking.email,
                    "user_phone": booking.phone,
                    "room_title": roomd.Room_title,
                    "room_rent": roomd.Room_rent,
                    "check_in": booking.check_in_date,
                    "verify_link": request.build_absolute_uri("/partner-dashboard/"),
                }

                # try:
                #     html_content = render_to_string(
                #         "booking_request.html",
                #         email_context
                #     )
                # except Exception as e:
                #     print("TEMPLATE ERROR:", e)

                # email = EmailMultiAlternatives(
                #     subject,
                #     "New booking request received",
                #     settings.EMAIL_HOST_USER,
                #     [roomd.partner.email, "UrbanTenants1@gmail.com"]
                # )

                # try:
                #     email.attach_alternative(html_content, "text/html")
                #     email.send(fail_silently=False)
                #     print("EMAIL SENT SUCCESSFULLY")
                # except Exception as e:
                #     print("EMAIL ERROR:", str(e))
               







                html_content = render_to_string("booking_request.html", email_context)

                def send_async():
                    send_brevo_email(
                        to_emails=[roomd.partner.email, "urbantenants1@gmail.com"],
                        subject="New Booking Request - Verify Now",
                        html_content=html_content
                    )

                import threading
                thread = threading.Thread(target=send_async)
                thread.daemon = True
                thread.start()
                print("EMAIL THREAD STARTED")

            # send_booking_notification(booking)
            partner_obj = roomd.partner
            if partner_obj:
                
                return redirect('bookingconfirm', id=booking.id)
    else:
        form = RoomBookingForm()

    return render(request, "bookingform.html", {
        'form': form,
        'room': roomd,
        'upi_id': upi_id,
        'qr_code': qr_code,
    })


def bookingcon(request, id):
    bookingdata = get_object_or_404(RoomBooking, id=id)

    return render(request, "bookingconfirm.html", {
        'bookingd': bookingdata,
        'room': bookingdata.room
    })
# invoice
@login_required
def invoice_view(request, booking_id):
    booking = get_object_or_404(
        RoomBooking,
        id=booking_id,
        email=request.user.email,
        status='confirmed'
    )

    subtotal = booking.room.Room_rent
    gst = subtotal * 0.18
    total = subtotal + gst

    return render(request, 'invoice.html', {
        'booking': booking,
        'subtotal': subtotal,
        'gst': gst,
        'total': total,
    })


@login_required
def download_invoice(request, booking_id):
    booking = get_object_or_404(
        RoomBooking,
        id=booking_id,
        email=request.user.email,
        status='confirmed'
    )

    subtotal = booking.room.Room_rent
    gst = subtotal * 0.18
    total = subtotal + gst

    template = get_template('invoice_pdf.html')
    html = template.render({
        'booking': booking,
        'subtotal': subtotal,
        'gst': gst,
        'total': total,
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{booking.id}.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('PDF banane me error aaya')

    return response
def onesignal_worker(request):
    return HttpResponse(
        "importScripts('https://cdn.onesignal.com/sdks/web/v16/OneSignalSDK.sw.js');",
        content_type="application/javascript"
    )
from django.conf import settings
from django.views import View
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

# @method_decorator(csrf_exempt,name='dispatch')

# class CreatePaymentView(LoginRequiredMixin, View):
#     def post(self, request, id):
#         try:
#             room = get_object_or_404(listings, id=id)

#             order_data = {
#                 "amount": int(room.Room_rent * 100),
#                 "currency": "INR",
#                 "payment_capture": "1"
#             }

           

#             return JsonResponse({
#                 "order_id": razorpay_order["id"],
#                 "razorpay_key_id": settings.RAZORPAY_ID,
#                 "amount": order_data["amount"],
#                 "razorpay_callback_url": settings.RAZORPAY_CALLBACK_URL
#             })

#         except Exception as e:
#             return JsonResponse({"error": str(e)})
# @method_decorator(csrf_exempt,name='dispatch')
# class PaymentCallbackView(View):
#     def post(self,request):
        
#         if "razorpay_signature" in request.POST:
#             order_id= request.POST.get("razorpay_order_id")
#             payment_id = request.POST.get("razorpay_payment_id")
#             signature= request.POST.get("razorpay_signature")


#             order = get_object_or_404(Order,razorpay_order_id=order_id)
#             if client.utility.verify_payment_signature({
#                 'razorpay_order_id': order_id,
#                 'razorpay_payment_id': payment_id,
#                 'razorpay_signature': signature
#             }):
                
#                 order.razorpay_payment_id = payment_id
#                 order.razorpay_signature = signature
#                 order.is_paid = True
#                 order.save()
#                 return JsonResponse({"status":"sucess"})
#             else:
#                 order.is_paid  = False
#                 order.save()
#                 return JsonResponse({"status":"failed"})
            
#         else:
#             return JsonResponse({"status":"failed"})
        
#     print("CALLBACK RECEIVED")

def terms_conditions(request):
    return render(request, "term.html")

def privacy_policy(request):
    return render(request, "privacy-policy.html")


def booking_request(request, room_id):
    room = get_object_or_404(listings, id=id)

    # booking object create hone ke baad ya form save ke baad use karo
    booking = RoomBooking.objects.filter(room=room).last()

    subject = "New Booking Request - Action Required"
    if request.get_host().startswith("127.0.0.1") or request.get_host().startswith("localhost"):
        verify_link = "http://127.0.0.1:8000/partner/register/"
    else:
        verify_link = "https://urbantenants.com/partner/register/"
    context = {
        "user_name": booking.name,
        "user_email": booking.email,
        "user_phone": booking.phone,
        "room_title": room.Room_title,
        "room_type": room.Room_type,
        "rent": room.Room_rent,
        "check_in": booking.check_in_date,
        "transaction_id": booking.transaction_id,
        "partner_name": room.partner.full_name,
         "verify_link": verify_link,
            
        
    }

    html_content = render_to_string("emails/booking_request.html", context)

    email = EmailMultiAlternatives(
        subject,
        "New booking request received",
        settings.EMAIL_HOST_USER,
        [room.partner.email, "UrbanTenants1@gmail.com"]
    )

    email.attach_alternative(html_content, "text/html")
    email.send()

    return redirect("success_page")
def csrf_failure(request, reason=""):
    return render(
        request,
        "csrf_error.html",
        {"reason": reason},
        status=403
    )
def help_support(request):
    return render(request, 'help_support.html')
def how_to_book(request):
    return render(request, 'how-to-book.html')
from django.views.decorators.http import require_POST
from listings.models import SupportQuery

@require_POST
def submit_support_query(request):
    name = request.POST.get('name', '').strip()
    email = request.POST.get('email', '').strip()
    subject = request.POST.get('subject', '').strip()
    message = request.POST.get('message', '').strip()

    if not all([name, email, subject, message]):
        return JsonResponse({'success': False, 'error': 'All fields are required.'}, status=400)

    SupportQuery.objects.create(name=name, email=email, subject=subject, message=message)

    return JsonResponse({'success': True})



# support team


# views.py
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from listings.models import SupportQuery,Offer


def is_support_user(user):
    return user.is_authenticated and (
        user.is_superuser or user.groups.filter(name="Support Team").exists()
    )


class SupportAuthForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        if not is_support_user(user):
            raise ValidationError(
                "You don't have access to the support dashboard.",
                code="no_permission",
            )


class SupportLoginView(LoginView):
    template_name = "support/login.html"
    authentication_form = SupportAuthForm
    redirect_authenticated_user = True

    def get_success_url(self):
        return "/support/dashboard/"


def support_logout(request):
    logout(request)
    return redirect("support_login")


@user_passes_test(is_support_user, login_url="support_login")
def support_dashboard(request):
    status = request.GET.get("status", "all")
    queries = SupportQuery.objects.all().order_by("-created_at")

    if status == "open":
        queries = queries.filter(resolved=False)
    elif status == "resolved":
        queries = queries.filter(resolved=True)

    context = {
        "queries": queries,
        "status": status,
        "open_count": SupportQuery.objects.filter(resolved=False).count(),
        "resolved_count": SupportQuery.objects.filter(resolved=True).count(),
        "total_count": SupportQuery.objects.count(),
    }
    return render(request, "support/dashboard.html", context)


@user_passes_test(is_support_user, login_url="support_login")
@require_POST
def toggle_resolved(request, query_id):
    query = SupportQuery.objects.get(id=query_id)
    query.resolved = not query.resolved
    query.save()
    return JsonResponse({"success": True, "resolved": query.resolved})




# rating view
from django.contrib import messages

def submit_review(request, room_id):
    print("VIEW HIT")
    if request.method == "POST":

        room = listings.objects.get(id=room_id)

        rating = request.POST.get("rating")
        review = request.POST.get("review")
       

        RoomRating.objects.create(
            room=room,
            
            rating=rating,
            review=review
        )
        messages.success(request, "Rating Submitted Successfully!")
    print("RATING SAVED")
    return redirect(request.META.get("HTTP_REFERER"))



# offer view

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

from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def user_list(request):
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'user_list.html', {'users': users})

from django.views.generic import TemplateView

def founder_message(request):
    return render(request, "founder_message.html")

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Avg
from listings.models import Review
from listings.forms import ReviewForm
 
 
# === New view: handles the AJAX form submit from the modal popup ===
@require_POST
def create_review(request):
    form = ReviewForm(request.POST)
    if form.is_valid():
        form.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'errors': form.errors}, status=400)
import requests
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404

# =====================================================================
# ADD/REPLACE THIS IN zameen/views.py
# Robust version: tries multiple Overpass servers, sends proper headers,
# and gives clear error messages if all fail.
# =====================================================================

import requests
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404

# Map categories to OpenStreetMap tags (free, no API key needed)
# Broadened to catch more tag variants commonly used in Indian OSM data
PLACE_TAG_MAP = {
    "hotel": [
        ("tourism", "hotel"), ("tourism", "guest_house"),
        ("tourism", "motel"), ("tourism", "hostel"),
        ("building", "hotel"),
    ],
    "restaurant": [
        ("amenity", "restaurant"), ("amenity", "fast_food"),
        ("amenity", "cafe"), ("amenity", "food_court"),
    ],
    "laundry": [
        ("shop", "laundry"), ("shop", "dry_cleaning"),
        ("craft", "dry_cleaning"),
    ],
    "shopping_mart": [
        ("shop", "mall"), ("shop", "department_store"),
        ("shop", "general"), ("shop", "variety_store"),
        ("shop", "clothes"),
    ],
    "food_supplier": [
        ("shop", "supermarket"), ("shop", "convenience"),
        ("shop", "grocery"), ("shop", "greengrocer"),
    ],
    "school": [
        ("amenity", "school"), ("amenity", "college"),
        ("amenity", "university"), ("amenity", "kindergarten"),
        ("amenity", "coaching_centre"),
    ],
}

# OSM place tags used to build the "areas & localities" label layer
# (things like Kalyanpur, Govind Nagar, villages, cities, etc.)
LOCALITY_TAG_PAIRS = [
    ("place", "suburb"), ("place", "neighbourhood"),
    ("place", "quarter"), ("place", "locality"),
    ("place", "hamlet"), ("place", "town"),
    ("place", "village"), ("place", "city"),
    ("place", "city_block"), ("place", "borough"),
]

# Colonies in Indian cities are usually mapped as *named residential
# landuse areas* (not "place" nodes), so they need a separate query
# that includes ways/relations (polygons), not just point nodes.
COLONY_TAG_PAIRS = [
    ("landuse", "residential"),
]

# Multiple public Overpass mirrors — if one is down/slow/blocking us,
# we automatically try the next one.
OVERPASS_SERVERS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.openstreetmap.ru/api/interpreter",
]

# Overpass sometimes rejects requests that don't look like they're
# coming from a real browser/app — this header fixes that.
OVERPASS_HEADERS = {
    "User-Agent": "UrbanTenants/1.0 (contact: urbantenants1@gmail.com)"
}


def _build_overpass_query(lat, lng, radius, tag_pairs):
    clauses = []
    for key, value in tag_pairs:
        clauses.append(f'node["{key}"="{value}"](around:{radius},{lat},{lng});')
        clauses.append(f'way["{key}"="{value}"](around:{radius},{lat},{lng});')
        clauses.append(f'relation["{key}"="{value}"](around:{radius},{lat},{lng});')
    return f"""
    [out:json][timeout:25];
    (
        {''.join(clauses)}
    );
    out center 100;
    """
def list_and_earn(request):
    return render(request, "list_and_earn.html")

def _extract_address(tags):
    parts = []
    if tags.get("addr:housenumber"):
        parts.append(tags["addr:housenumber"])
    if tags.get("addr:street"):
        parts.append(tags["addr:street"])
    if tags.get("addr:suburb"):
        parts.append(tags["addr:suburb"])
    if tags.get("addr:city"):
        parts.append(tags["addr:city"])
    return ", ".join(parts) if parts else None


def _query_overpass(query):
    """
    Tries each Overpass mirror in order until one succeeds.
    Returns the parsed JSON data, or raises the last error if all fail.
    """
    last_error = None
    for server_url in OVERPASS_SERVERS:
        try:
            resp = requests.post(
                server_url,
                data={"data": query},
                headers=OVERPASS_HEADERS,
                timeout=20,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            last_error = e
            continue  # try the next mirror
    # all mirrors failed
    raise last_error


def nearby_places_api(request):
    """
    AJAX endpoint consumed by the room page's JS.
    Fetches nearby places from the free OpenStreetMap Overpass API
    (tries multiple mirrors) and returns a clean JSON payload.

    Query params:
        lat       (required)
        lng       (required)
        category  (optional, default="hotel") -> one of PLACE_TAG_MAP keys
        radius    (optional, default=3000 meters)
    """
    lat = request.GET.get("lat")
    lng = request.GET.get("lng")
    category = request.GET.get("category", "hotel")
    radius = request.GET.get("radius", 3000)

    if not lat or not lng:
        return JsonResponse({"error": "lat and lng are required"}, status=400)

    tag_pairs = PLACE_TAG_MAP.get(category)
    if not tag_pairs:
        return JsonResponse({"error": f"Unknown category '{category}'"}, status=400)

    query = _build_overpass_query(lat, lng, radius, tag_pairs)

    try:
        data = _query_overpass(query)
    except Exception as e:
        return JsonResponse(
            {"error": f"Could not reach any Overpass server: {e}"},
            status=502,
        )

    category_display = {
        "hotel": "Hotel", "restaurant": "Restaurant", "laundry": "Laundry",
        "shopping_mart": "Shopping Mart", "food_supplier": "Store",
        "school": "School",
    }

    results = []
    for element in data.get("elements", []):
        tags = element.get("tags", {})
        name = tags.get("name") or f"Unnamed {category_display.get(category, 'Place')}"

        if element["type"] == "node":
            place_lat = element.get("lat")
            place_lng = element.get("lon")
        else:
            center = element.get("center", {})
            place_lat = center.get("lat")
            place_lng = center.get("lon")

        if place_lat is None or place_lng is None:
            continue

        results.append({
            "name": name,
            "address": _extract_address(tags),
            "lat": place_lat,
            "lng": place_lng,
            "phone": tags.get("phone") or tags.get("contact:phone"),
            "opening_hours": tags.get("opening_hours"),
            "website": tags.get("website") or tags.get("contact:website"),
            "email": tags.get("email") or tags.get("contact:email"),
            "cuisine": tags.get("cuisine"),
            "stars": tags.get("stars"),
            "wheelchair": tags.get("wheelchair"),
            "internet_access": tags.get("internet_access"),
            "outdoor_seating": tags.get("outdoor_seating"),
            "delivery": tags.get("delivery"),
            "takeaway": tags.get("takeaway"),
            "air_conditioning": tags.get("air_conditioning"),
        })

    return JsonResponse({"results": results, "category": category})


def _build_locality_query(lat, lng, radius, tag_pairs):
    """place=* tags are almost always nodes (single points)."""
    clauses = []
    for key, value in tag_pairs:
        clauses.append(f'node["{key}"="{value}"](around:{radius},{lat},{lng});')
    return f"""
    [out:json][timeout:25];
    (
        {''.join(clauses)}
    );
    out body;
    """


def _build_colony_query(lat, lng, radius, tag_pairs):
    """
    Colonies are usually mapped as named residential landuse *areas*
    (ways/relations), so we need their centroid via 'out center'.
    """
    clauses = []
    for key, value in tag_pairs:
        clauses.append(f'way["{key}"="{value}"]["name"](around:{radius},{lat},{lng});')
        clauses.append(f'relation["{key}"="{value}"]["name"](around:{radius},{lat},{lng});')
    return f"""
    [out:json][timeout:25];
    (
        {''.join(clauses)}
    );
    out center;
    """


def nearby_localities_api(request):
    """
    AJAX endpoint that returns named areas / localities / villages / cities /
    colonies around a given point (e.g. Kalyanpur, Govind Nagar), so they can
    be shown as text labels on the property map.

    Query params:
        lat, lng  (required)
        radius    (optional, default=8000 meters — localities need a wider radius than shops)
    """
    lat = request.GET.get("lat")
    lng = request.GET.get("lng")
    radius = request.GET.get("radius", 8000)

    if not lat or not lng:
        return JsonResponse({"error": "lat and lng are required"}, status=400)

    place_query = _build_locality_query(lat, lng, radius, LOCALITY_TAG_PAIRS)
    colony_query = _build_colony_query(lat, lng, radius, COLONY_TAG_PAIRS)

    try:
        place_data = _query_overpass(place_query)
    except Exception as e:
        return JsonResponse(
            {"error": f"Could not reach any Overpass server: {e}"},
            status=502,
        )

    # Colonies are a best-effort extra — if this call fails, we still
    # return the place-node results rather than failing the whole request.
    try:
        colony_data = _query_overpass(colony_query)
    except Exception:
        colony_data = {"elements": []}

    place_type_display = {
        "suburb": "Suburb", "neighbourhood": "Neighbourhood",
        "quarter": "Quarter", "locality": "Locality",
        "hamlet": "Hamlet", "town": "Town",
        "village": "Village", "city": "City",
        "city_block": "Block", "borough": "Borough",
    }

    results = []
    seen_names = set()

    for element in place_data.get("elements", []):
        tags = element.get("tags", {})
        name = tags.get("name")
        if not name or name in seen_names:
            continue
        place_lat = element.get("lat")
        place_lng = element.get("lon")
        if place_lat is None or place_lng is None:
            continue
        seen_names.add(name)
        results.append({
            "name": name,
            "place_type": place_type_display.get(tags.get("place"), "Area"),
            "lat": place_lat,
            "lng": place_lng,
        })

    for element in colony_data.get("elements", []):
        tags = element.get("tags", {})
        name = tags.get("name")
        if not name or name in seen_names:
            continue

        if element["type"] == "way" or element["type"] == "relation":
            center = element.get("center", {})
            place_lat = center.get("lat")
            place_lng = center.get("lon")
        else:
            place_lat = element.get("lat")
            place_lng = element.get("lon")

        if place_lat is None or place_lng is None:
            continue

        seen_names.add(name)
        results.append({
            "name": name,
            "place_type": "Colony",
            "lat": place_lat,
            "lng": place_lng,
        })

    return JsonResponse({"results": results})


import math
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from listings.models import listings as Listings, NeighborhoodPost, NeighborhoodReply
 
 
def _haversine_km(lat1, lng1, lat2, lng2):
    R = 6371
    lat1, lng1, lat2, lng2 = map(float, [lat1, lng1, lat2, lng2])
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2)
    c = 2 * math.asin(math.sqrt(a))
    return R * c
 
 
def _nearby_listing_ids(listing, radius_km=2):
    """Returns IDs of all listings (including this one) within radius_km of the given listing."""
    if not listing.latitude or not listing.longitude:
        return [listing.id]
 
    ids = [listing.id]
    others = Listings.objects.exclude(id=listing.id).exclude(latitude=None).exclude(longitude=None)
    for other in others:
        dist = _haversine_km(listing.latitude, listing.longitude, other.latitude, other.longitude)
        if dist <= radius_km:
            ids.append(other.id)
    return ids
 
 
@login_required
def neighborhood_board(request, listing_id):
    """
    Shows a discussion board for a listing, combining posts from all
    listings within a 2km radius. Handles new post creation on POST.
    """
    listing = get_object_or_404(Listings, id=listing_id)
    nearby_ids = _nearby_listing_ids(listing, radius_km=2)
 
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        content = request.POST.get("content", "").strip()
        if title and content:
            NeighborhoodPost.objects.create(
                listing=listing,
                user=request.user,
                title=title,
                content=content,
            )
        return redirect('neighborhood_board', listing_id=listing.id)
 
    posts = (
        NeighborhoodPost.objects
        .filter(listing_id__in=nearby_ids)
        .select_related('user', 'listing')
        .prefetch_related('replies__user')
    )
 
    return render(request, "neighborhood_board.html", {
        "listing": listing,
        "posts": posts,
        "nearby_count": len(nearby_ids),
    })
 
 
@login_required
def neighborhood_reply(request, post_id):
    """Handles adding a reply to a NeighborhoodPost."""
    post = get_object_or_404(NeighborhoodPost, id=post_id)
    if request.method == "POST":
        content = request.POST.get("content", "").strip()
        if content:
            NeighborhoodReply.objects.create(
                post=post,
                user=request.user,
                content=content,
            )
    return redirect('neighborhood_board', listing_id=post.listing.id)
 
 
@login_required
def neighborhood_toggle_resolved(request, post_id):
    """Lets the original poster mark their post as resolved/unresolved."""
    post = get_object_or_404(NeighborhoodPost, id=post_id)
    if request.method == "POST" and post.user == request.user:
        post.is_resolved = not post.is_resolved
        post.save()
    return redirect('neighborhood_board', listing_id=post.listing.id)




def robots_txt(request):
    lines = [
        "User-agent: *",
        "Allow: /",
        "",
        "Disallow: /admin/",
        "Disallow: /business/dashboard/",
        "Disallow: /support/dashboard/",
        "",
        f"Sitemap: {request.scheme}://{request.get_host()}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")




from django.http import JsonResponse

def all_listings_map(request):
    return render(request, 'all_listings_map.html')


from django.urls import reverse

def listings_geojson(request):
    rooms = listings.objects.filter(
        latitude__isnull=False,
        longitude__isnull=False
    ).only(
        'id', 'Room_title', 'listing_id', 'location_name', 'Room_rent',
        'latitude', 'longitude',
        'Room_images1', 'Room_images2', 'Room_images3'
    )

    data = []
    for room in rooms:
        # pick the first available image
        image_url = None
        for field in [room.Room_images1, room.Room_images2, room.Room_images3]:
            if field:
                try:
                    image_url = field.url
                    break
                except Exception:
                    continue

        data.append({
            'id': room.id,
            'title': room.Room_title,
            'listing_id': room.listing_id or 'No',
            'location_name': room.location_name or '',
            'rent': room.Room_rent,
            'lat': float(room.latitude),
            'lng': float(room.longitude),
            'image': image_url,
            'url': reverse('room', args=[room.id]),
        })

    return JsonResponse({'results': data})



import json
import re

from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from listings.models import Participant

MAX_SCORE = 5000


def room_hunt_view(request):
    """Renders the Room Hunt Challenge quiz page."""
    return render(request, 'urbantents-room-hunt-quiz.html')


def _clean_phone(raw):
    return re.sub(r'\s+', '', raw or '').strip()


@require_POST
def submit_score(request):
    """
    Saves a participant's finished-quiz score. Phone number is stored
    only to inform winners later — no format validation is enforced.
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
        name = (data.get('name') or '').strip()[:100]
        phone = _clean_phone(data.get('phone'))[:15]
        score = int(data.get('score', 0))
    except (json.JSONDecodeError, ValueError, TypeError):
        return JsonResponse({'error': 'Invalid payload'}, status=400)

    if not name:
        return JsonResponse({'error': 'Name is required'}, status=400)
    if not phone:
        return JsonResponse({'error': 'Phone number is required'}, status=400)

    score = max(0, min(score, MAX_SCORE))

    try:
        participant = Participant.objects.create(name=name, phone=phone, score=score)
    except IntegrityError:
        return JsonResponse({'error': 'This phone number has already played'}, status=409)

    return JsonResponse({'id': participant.id})



from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from listings.models import RoomLike

@login_required
@require_POST
def toggle_like(request, room_id):
    room = get_object_or_404(listings, id=room_id)
    like, created = RoomLike.objects.get_or_create(room=room, user=request.user)

    if not created:
        like.delete()
        liked = False
    else:
        liked = True

    return JsonResponse({
        'success': True,
        'liked': liked,
        'like_count': room.likes.count()
    })
def robots_txt(request):
    lines = [
        "User-agent: *",
        "Allow: /",
        "",
        "Disallow: /admin/",
        "Disallow: /business/dashboard/",
        "Disallow: /support/dashboard/",
        "",
        f"Sitemap: {request.scheme}://{request.get_host()}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")
def refund_cancellation(request):
    return render(request, "refund-cancellation.html")

def ads_txt(request):
    # Google AdSense verification file - must be served at domain root exactly as /ads.txt
    lines = [
        "google.com, pub-2357487058280395, DIRECT, f08c47fec0942fa0",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")