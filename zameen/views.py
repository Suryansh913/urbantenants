from django.http import HttpResponse
from django.shortcuts import render,get_object_or_404,redirect
from listings.models import listings, Booking , RoomBooking,Order,RoomRating
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
def room(request, id):
    roomd = get_object_or_404(listings,id=id)
    # room_obj = get_object_or_404(listings,id=id)

    listing=listings.objects.get(id=id)
    # # request.session['id']=listings.id
    listingdata=listings.objects.all()
    # Booking.objects.create(
    #     user=request.user,
    #     listings = room_obj
    # )

    reviews = roomd.ratings.all().order_by('-created_at')
    
    # Star breakdown
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

    
    data={
        'listingdata':listingdata,
        
    }
    
    
    images=[
        listing.Room_images1,
        listing.Room_images2,
        listing.Room_images3,
        listing.Room_images4,
        listing.Room_images5,
    ]
    print("AVG:", roomd.average_rating)
    print("TOTAL:", roomd.total_reviews)
   
    return render( request, "room.html",{'room': roomd ,'images':images,'data':data,'reviews': reviews,'star_bars': star_bars,'final_price':final_price})

def base(request):
    from django.db.models import Avg, Count

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
    return render(request, "base.html", {
        'listingdata': page_obj,
        'page_obj': page_obj,
        'title': title,
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