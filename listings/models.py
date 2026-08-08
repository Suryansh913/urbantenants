from django.db import models
from django.contrib.auth.models import User
from partner.models import Partner
from django.db.models import Avg
from cloudinary.models import CloudinaryField
from django.db import transaction  
class ListingIDCounter(models.Model):
    last_number = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Last ID: {self.last_number}"
# this is for room listing
class listings(models.Model):
    listing_id = models.CharField(max_length=20, unique=True, blank=True, null=True, editable=False, db_index=True)
    Room_title = models.CharField(max_length=100)
    Room_rent = models.IntegerField()
    Room_images1 = CloudinaryField('image', blank=False, null=True)
    Room_images2 = CloudinaryField('image', blank=False, null=True)
    Room_images3 = CloudinaryField('image', blank=True, null=True)
    Room_images4 = CloudinaryField('image', blank=True, null=True)
    Room_images5 = CloudinaryField('image', blank=True, null=True)
    Room_video1 = CloudinaryField('video', resource_type='video', blank=False, null=True)
    Room_video2 = CloudinaryField('video', resource_type='video', blank=True, null=True)
    Room_video3 = CloudinaryField('video', resource_type='video', blank=True, null=True)
    Room_video4 = CloudinaryField('video', resource_type='video', blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True, null=True)
    Room_details = models.TextField()
    Room_available = models.BooleanField(default=True)
    Room_type = models.CharField(max_length=50)
    Room_security = models.IntegerField(default=0)
    wifi = models.BooleanField(default=False)
    bed = models.BooleanField(default=False)
    mattres = models.BooleanField(default=False)
    table = models.BooleanField(default=False)
    chair = models.BooleanField(default=False)
    fan = models.BooleanField(default=False)
    Ac = models.BooleanField(default=False)
    ro = models.BooleanField(default=False)
    BATHROOM_TYPE_CHOICES = [
        ('none', 'No Bathroom'),
        ('attached', 'Attached'),
        ('shared', 'Shared'),
    ]
    bathroom_count = models.PositiveIntegerField(default=0)
    bathroom_type = models.CharField(max_length=10, choices=BATHROOM_TYPE_CHOICES, default='none')

    KITCHEN_TYPE_CHOICES = [
        ('none', 'No Kitchen'),
        ('private', 'Private'),
        ('shared', 'Shared'),
    ]
    kitchen_count = models.PositiveIntegerField(default=0)
    kitchen_type = models.CharField(max_length=10, choices=KITCHEN_TYPE_CHOICES, default='none')

    has_hall = models.BooleanField(default=False)
    hall_count = models.PositiveIntegerField(default=0)

    has_dining_hall = models.BooleanField(default=False)

    room_count = models.PositiveIntegerField(default=1) 
    location_name = models.CharField(max_length=255, blank=True, null=True)
    latitude  = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    partner = models.ForeignKey(
        'partner.Partner',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='listings'
    )
    def save(self, *args, **kwargs):
        if not self.listing_id:
            with transaction.atomic():
                counter, created = ListingIDCounter.objects.select_for_update().get_or_create(id=1)
                counter.last_number += 1
                counter.save()
                self.listing_id = f"UT{counter.last_number:07d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.Room_title
    @property
    def average_rating(self):
        return self.ratings.aggregate(Avg('rating'))['rating__avg'] or 0

    @property
    def total_reviews(self):
        return self.ratings.count()

class Booking(models.Model):
    listings = models.ForeignKey(listings, on_delete=models.CASCADE)
    booking_date = models.DateTimeField(auto_now_add=True)
    is_confirmed = models.BooleanField(default=True)
    

    def __str__(self):
        return f"Booking for {self.listings.Room_title}"

# this mode l is for room booking form
class RoomBooking(models.Model):
    room = models.ForeignKey(
        listings,
        on_delete=models.CASCADE,
        related_name='room_bookings',
        null=True,
        blank=True
    )

    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    check_in_date = models.DateField()
    is_verified = models.BooleanField(default=False)
    verified_on = models.DateField(null=True, blank=True)
    payment_done = models.BooleanField(default=False)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    payment_screenshot = CloudinaryField(
        'payment_screenshot',
        blank=True,
        null=True
    )
    payment_method = models.CharField(max_length=50, blank=True, null=True)

    partner_verified = models.BooleanField(default=False)

    status = models.CharField(
        max_length=30,
        choices=[
            ('pending_verification', 'Pending Verification'),
            ('confirmed', 'Confirmed'),
            ('rejected', 'Rejected'),
        ],
        default='pending_verification'
    )

    feedback = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        room_title = self.room.Room_title if self.room else "No Room"
        return f"{self.name} - {room_title} - {self.check_in_date}"
class Order(models.Model):
    booking = models.OneToOneField(RoomBooking, on_delete=models.CASCADE)

    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)

    amount = models.IntegerField(default=0)

    payment_status = models.CharField(
        max_length=30,
        choices=[
            ('created', 'Created'),
            ('paid', 'Paid'),
            ('failed', 'Failed'),
            ('refunded', 'Refunded'),
        ],
        default='created'
    )

    paid_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)


class SupportQuery(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.subject} - {self.name}"
    
class RoomRating(models.Model):
    room = models.ForeignKey(
        listings,
        on_delete=models.CASCADE,
        related_name='ratings'
    )

    booking = models.ForeignKey(
        RoomBooking,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

   
    rating = models.PositiveSmallIntegerField(default=5)
    review = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.room.Room_title} - {self.rating} Star"
    
@property
def average_rating(self):
    return self.ratings.aggregate(Avg('rating'))['rating__avg'] or 0
       
@property
def total_reviews(self):
    return self.ratings.count()




# offer model


class Offer(models.Model):
    listing = models.OneToOneField(
        'listings',
        on_delete=models.CASCADE,
        related_name='offer'
    )

    discount_percent = models.IntegerField(default=0)
    active = models.BooleanField(default=True)

    valid_from = models.DateTimeField(null=True, blank=True)
    valid_to = models.DateTimeField(null=True, blank=True)

    def is_valid(self):
        from django.utils import timezone
        now = timezone.now()

        if not self.active:
            return False

        if self.valid_from and now < self.valid_from:
            return False

        if self.valid_to and now > self.valid_to:
            return False

        return True
    

class Review(models.Model):
    name = models.CharField(max_length=60)
    rating = models.PositiveSmallIntegerField()  # 1 to 5
    text = models.CharField(max_length=220)
    created_at = models.DateTimeField(auto_now_add=True)
 
    # Keep True by default so reviews show instantly.
    # Set to False if you want to manually approve reviews from /admin/ before they go live.
    is_approved = models.BooleanField(default=True)
 
    class Meta:
        ordering = ['-created_at']
 
    def __str__(self):
        return f"{self.name} - {self.rating}\u2605"
 
from django.contrib.auth.models import User
 
 
class NeighborhoodPost(models.Model):
    """A post made from a specific listing, visible to nearby listings' users."""
    listing = models.ForeignKey(
        'listings.listings',
        on_delete=models.CASCADE,
        related_name='neighborhood_posts'
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='neighborhood_posts')
    title = models.CharField(max_length=150)
    content = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        ordering = ['-created_at']
 
    def __str__(self):
        return f"{self.title} (by {self.user.username})"
 
 
class NeighborhoodReply(models.Model):
    """A reply to a NeighborhoodPost."""
    post = models.ForeignKey(NeighborhoodPost, on_delete=models.CASCADE, related_name='replies')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='neighborhood_replies')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        ordering = ['created_at']
 
    def __str__(self):
        return f"Reply by {self.user.username} on '{self.post.title}'"


from django.utils import timezone
from datetime import timedelta
class Participant(models.Model):
    """A single Room Hunt Challenge attempt."""
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15 ,blank=True, default='')
    score = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        ordering = ['-score', 'created_at']
 
    def __str__(self):
        return f"{self.name} ({self.phone}) — {self.score}"
 
class ChatSubscription(models.Model):
    PLAN_BASIC = 'basic'
    PLAN_UNLIMITED = 'unlimited'
    PLAN_CHOICES = [
        (PLAN_BASIC, 'Basic - 20 Chats (14 days)'),
        (PLAN_UNLIMITED, 'Unlimited Chats (14 days)'),
    ]
 
    STATUS_CREATED = 'created'
    STATUS_ACTIVE = 'active'
    STATUS_FAILED = 'failed'
    STATUS_EXPIRED = 'expired'
    STATUS_CHOICES = [
        (STATUS_CREATED, 'Created'),
        (STATUS_ACTIVE, 'Active'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_EXPIRED, 'Expired'),
    ]
 
    PLAN_PRICES = {
        PLAN_BASIC: 1,
        PLAN_UNLIMITED: 19,
    }
    PLAN_CHAT_LIMIT = {
        PLAN_BASIC: 20,
        PLAN_UNLIMITED: None,  # unlimited
    }
    VALIDITY_DAYS = 14
 
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='chat_subscriptions'
    )
    room = models.ForeignKey(
        listings, on_delete=models.CASCADE, related_name='chat_subscriptions'
    )
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES)
    amount = models.PositiveIntegerField(default=0)
 
    cf_order_id = models.CharField(max_length=100, unique=True, db_index=True)
    cf_payment_session_id = models.CharField(max_length=255, blank=True, null=True)
 
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_CREATED
    )
 
    chats_limit = models.PositiveIntegerField(null=True, blank=True)  # null = unlimited
    chats_used = models.PositiveIntegerField(default=0)
 
    valid_until = models.DateTimeField(null=True, blank=True)
 
    created_at = models.DateTimeField(auto_now_add=True)
    activated_at = models.DateTimeField(null=True, blank=True)
 
    class Meta:
        ordering = ['-created_at']
 
    def __str__(self):
        return f"{self.user} - {self.room} - {self.get_plan_display()} - {self.status}"
 
    def activate(self):
        """Mark this subscription paid & active. Called after payment verification."""
        self.status = self.STATUS_ACTIVE
        self.chats_limit = self.PLAN_CHAT_LIMIT[self.plan]
        self.chats_used = 0
        self.activated_at = timezone.now()
        self.valid_until = self.activated_at + timedelta(days=self.VALIDITY_DAYS)
        self.save()
 
    def is_active(self):
        if self.status != self.STATUS_ACTIVE:
            return False
        if self.valid_until and timezone.now() > self.valid_until:
            return False
        if self.chats_limit is not None and self.chats_used >= self.chats_limit:
            return False
        return True
 
    def chats_remaining(self):
        if self.chats_limit is None:
            return None  # unlimited
        return max(0, self.chats_limit - self.chats_used)
 
    def consume_chat(self):
        """Increment usage. Only meaningful for the limited (basic) plan."""
        if self.chats_limit is not None:
            self.chats_used = models.F('chats_used') + 1
            self.save(update_fields=['chats_used'])
            self.refresh_from_db(fields=['chats_used'])
 
    @classmethod
    def get_active_for(cls, user, room):
        if not user or not user.is_authenticated:
            return None
        sub = (
            cls.objects.filter(
                user=user, room=room, status=cls.STATUS_ACTIVE
            )
            .order_by('-created_at')
            .first()
        )
        if sub and sub.is_active():
            return sub
        return None
