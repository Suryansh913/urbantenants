from django.db import models
from django.contrib.auth.models import User
from partner.models import Partner
from django.db.models import Avg
from cloudinary.models import CloudinaryField
# this is for room listing
class listings(models.Model):
    Room_title = models.CharField(max_length=100)
    Room_rent = models.IntegerField()
    Room_images1 = CloudinaryField('image', blank=False, null=True)
    Room_images2 = CloudinaryField('image', blank=False, null=True)
    Room_images3 = CloudinaryField('image', blank=True, null=True)
    Room_images4 = CloudinaryField('image', blank=True, null=True)
    Room_images5 = CloudinaryField('image', blank=True, null=True)
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