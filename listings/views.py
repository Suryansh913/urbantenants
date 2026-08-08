from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.urls import reverse
from django.conf import settings
from django.contrib import messages
 
from .models import listings, ChatSubscription
from .utils import cashfree_create_order, cashfree_get_order
 
 
@login_required(login_url='loginv')
def chat_unlock_plans(request, room_id):
    """Shows the two chat-unlock plans for a given room."""
    room = get_object_or_404(listings, id=room_id)
 
    active_sub = ChatSubscription.get_active_for(request.user, room)
    if active_sub:
        return redirect('room', id=room.id)
 
    plans = [
        {
            'key': ChatSubscription.PLAN_BASIC,
            'label': 'Basic',
            'price': ChatSubscription.PLAN_PRICES[ChatSubscription.PLAN_BASIC],
            'desc': '20 chats · valid for 14 days',
        },
        {
            'key': ChatSubscription.PLAN_UNLIMITED,
            'label': 'Unlimited',
            'price': ChatSubscription.PLAN_PRICES[ChatSubscription.PLAN_UNLIMITED],
            'desc': 'Unlimited chats · valid for 14 days',
        },
    ]
 
    return render(request, 'chat_unlock_plans.html', {
        'room': room,
        'plans': plans,
    })
 
 
@login_required(login_url='loginv')
@require_POST
def chat_unlock_create_order(request, room_id):
    """Creates a ChatSubscription (pending) + Cashfree order, returns payment_session_id."""
    print("🔥 CHAT UNLOCK FUNCTION CALLED", flush=True)
    room = get_object_or_404(listings, id=room_id)
    plan = request.POST.get('plan')
 
    if plan not in (ChatSubscription.PLAN_BASIC, ChatSubscription.PLAN_UNLIMITED):
        return JsonResponse({'success': False, 'error': 'Invalid plan selected.'}, status=400)
 
    amount = ChatSubscription.PLAN_PRICES[plan]
 
    return_url = settings.SITE_DOMAIN.rstrip('/') + reverse(
        'chat_unlock_verify', args=[room.id]
    )
    print("========== CASHFREE ==========")
    print("ENV:", settings.CASHFREE_ENV)
    print("URL:", settings.CASHFREE_BASE_URL)
    print("APP ID:", settings.CASHFREE_APP_ID[:12])
    print("================================")
    cf_response = cashfree_create_order(
        amount=amount,
        user=request.user,
        return_url=return_url,
        order_note=f"Chat unlock ({plan}) for room {room.id}",
    )
 
    if cf_response.get('_http_status') not in (200, 201) or 'payment_session_id' not in cf_response:
        return JsonResponse({
            'success': False,
            'error': cf_response.get('message', 'Could not create payment order. Please try again.'),
        }, status=400)
 
    sub = ChatSubscription.objects.create(
        user=request.user,
        room=room,
        plan=plan,
        amount=amount,
        cf_order_id=cf_response['_order_id'],
        cf_payment_session_id=cf_response['payment_session_id'],
        status=ChatSubscription.STATUS_CREATED,
    )
 
    return JsonResponse({
        'success': True,
        'payment_session_id': cf_response['payment_session_id'],
        'cf_order_id': sub.cf_order_id,
        'subscription_id': sub.id,
        'is_test': settings.CASHFREE_ENV == 'TEST',
    })
 
 
@login_required(login_url='loginv')
def chat_unlock_verify(request, room_id):
    """Cashfree redirects here after checkout. Verifies payment and activates subscription."""
    room = get_object_or_404(listings, id=room_id)
    cf_order_id = request.GET.get('order_id')
 
    sub = ChatSubscription.objects.filter(
        cf_order_id=cf_order_id, user=request.user, room=room
    ).first()
 
    if not sub:
        messages.error(request, "We couldn't find that payment. Please try again.")
        return redirect('room', id=room.id)
 
    if sub.status != ChatSubscription.STATUS_ACTIVE:
        cf_data = cashfree_get_order(cf_order_id)
        order_status = cf_data.get('order_status')
 
        if order_status == 'PAID':
            sub.activate()
            messages.success(
                request,
                f"Chat unlocked! You now have "
                f"{'unlimited chats' if sub.chats_limit is None else f'{sub.chats_limit} chats'} "
                f"for {ChatSubscription.VALIDITY_DAYS} days."
            )
        elif order_status in ('ACTIVE', 'PENDING'):
            messages.info(request, "Your payment is still processing. Please wait a moment and refresh.")
        else:
            sub.status = ChatSubscription.STATUS_FAILED
            sub.save(update_fields=['status'])
            messages.error(request, "Payment failed or was cancelled. Please try again.")
 
    return redirect('room', id=room.id)
 
 
@login_required(login_url='loginv')
@require_POST
def chat_unlock_use(request, room_id):
    """Called via AJAX right before opening the WhatsApp link, to consume one chat credit."""
    room = get_object_or_404(listings, id=room_id)
    sub = ChatSubscription.get_active_for(request.user, room)
 
    if not sub:
        return JsonResponse({'success': False, 'error': 'no_active_subscription'}, status=402)
 
    sub.consume_chat()
 
    return JsonResponse({
        'success': True,
        'chats_remaining': sub.chats_remaining(),
        'unlimited': sub.chats_limit is None,
    })
