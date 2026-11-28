from django.db import models
from barbers.models import Barber
from services.models import Service
import random, string
from django.core.mail import send_mail
from django.utils import timezone
from django.core.exceptions import ValidationError
from .emailing import send_email_async

class BarberAvailability(models.Model):
    WEEKDAY_CHOICES = [
        (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'),
        (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday'),
    ]
    barber = models.ForeignKey(Barber, on_delete=models.CASCADE, related_name='availability')
    weekday = models.IntegerField(choices=WEEKDAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        verbose_name_plural = "Barber availabilities"

    def __str__(self):
        return f"{self.barber.name} - {self.get_weekday_display()} ({self.start_time}-{self.end_time})"


class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
        ('expired', 'expired'),
    ]
    payment_claimed_at = models.DateTimeField(null=True, blank=True)
    barber = models.ForeignKey(Barber, on_delete=models.CASCADE, related_name='bookings')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='bookings')
    customer_name = models.CharField(max_length=100)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reference = models.CharField(max_length=20, unique=True, blank=True)

    @property
    def when_display(self):
        start = timezone.localtime(self.start_time)
        end = timezone.localtime(self.end_time)
        return f"{start:%A, %d %B %Y}, {start:%H:%M} – {end:%H:%M}"

    def save(self, *args, **kwargs):
        if not self.reference:
           self.reference = self._generate_reference()

        status_changed_to_confirmed = False
        status_changed_to_completed = False
        status_changed_to_cancelled = False
        if self.pk:
           old = Booking.objects.filter(pk=self.pk).first()
           if old and old.status != 'confirmed' and self.status == 'confirmed':
              status_changed_to_confirmed = True
           if old and old.status != 'completed' and self.status == 'completed':
                status_changed_to_completed = True
           if old and old.status != 'cancelled' and self.status == 'cancelled':
                status_changed_to_cancelled = True

        super().save(*args, **kwargs)

        if status_changed_to_confirmed:
           self._send_payment_confirmed_email()
        if status_changed_to_completed:
           self._send_completed_email()
        if status_changed_to_cancelled:
           self._send_cancelled_email()
           
    def clean(self):
        if self.status != 'confirmed':
            return
        if not (self.barber_id and self.start_time and self.end_time):
            return

        clash = Booking.objects.filter(
            barber=self.barber,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time,
            status__in=['confirmed', 'completed'],
        ).exclude(pk=self.pk).first()

        if clash:
            raise ValidationError(
                f"This time overlaps booking {clash.reference} ({clash.customer_name}). Resolve that first."
            )
           
    def _generate_reference(self):
        while True:
            code = 'HK-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if not Booking.objects.filter(reference=code).exists():
                return code

    def _send_payment_confirmed_email(self):
        from decimal import Decimal
        from core.models import SiteSettings

        site = SiteSettings.load()
        intro = "We've received your payment and your booking is now confirmed."
        if site.has_deposit:
            intro = f"We've received your £{site.deposit_amount} deposit and your booking is now confirmed."
            if self.service.price_note:
                intro += " The deposit comes off your final price."
            else:
                balance = max(self.service.price - site.deposit_amount, Decimal('0'))
                intro += f" The deposit comes off the price, leaving £{balance} to pay on the day."

        send_email_async(
            subject=f"Payment Confirmed - Hair Klinics ({self.reference})",
            message=(
                f"Hi {self.customer_name},\n\n"
                f"{intro}\n\n"
                f"Reference: {self.reference}\n"
                f"Service: {self.service.name}\n"
                f"When: {self.when_display}\n\n"
                f"We'll see you then! Reply to this email if anything changes.\n\n"
                f"Thanks,\nHair Klinics"
            ),
            from_email=None,
            recipient_list=[self.customer_email],
            fail_silently=True,
        )
        
    def _send_completed_email(self):
        send_mail(
           subject=f"Thank You - Hair Klinics ({self.reference})",
           message=(
              f"Hi {self.customer_name},\n\n"
              f"Thank you for visiting Hair Klinics! We hope you loved your {self.service.name}.\n\n"
              f"We'd love to see you again soon. Follow us on Instagram and Facebook for our latest work.\n\n"
              f"Thank you,\nHair Klinics"
           ),
           
        from_email=None,
        recipient_list=[self.customer_email],
        fail_silently=True,
        )
        
    def _send_cancelled_email(self):
         send_mail(
            subject=f"Booking Cancelled - Hair Klinics ({self.reference})",
            message=(
                f"Hi {self.customer_name},\n\n"
                f"Your booking has been cancelled:\n"
                f"Reference: {self.reference}\n"
                f"Service: {self.service.name}\n"
                f"When: {self.when_display}\n\n"
                f"If this wasn't expected, or you'd like to rebook, please get in touch.\n\n"
                f"Thank you,\nHair Klinics"
            ),
        from_email=None,
        recipient_list=[self.customer_email],
        fail_silently=True,
    )
    class Meta:
        
        ordering = ['start_time']

    def __str__(self):
        return f"{self.customer_name} with {self.barber.name} at {self.start_time}"
    
class TimeBlock(models.Model):
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ['start_time']

    def __str__(self):
        return f"{self.start_time:%H:%M} – {self.end_time:%H:%M}"
