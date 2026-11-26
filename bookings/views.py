from django.shortcuts import render
from datetime import datetime, timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status as http_status
from .serializers import AvailabilityQuerySerializer
from .models import BarberAvailability, Booking
from django.utils import timezone
from rest_framework.generics import CreateAPIView
from .serializers import BookingSerializer
from .models import Booking
from django.core.mail import send_mail
from django.conf import settings
from .scheduling import candidate_slots, blocking_bookings, run_cleanup
from rest_framework.throttling import ScopedRateThrottle
import logging
from core.models import SiteSettings
from emailing import send_email_async

logger = logging.getLogger(__name__)
class AvailabilityView(APIView):
    run_cleanup()
    def get(self, request):
        serializer = AvailabilityQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        barber = serializer.validated_data['barber']
        service = serializer.validated_data['service']
        date = serializer.validated_data['date']

        now = timezone.now()
        free = []
        for start, end in candidate_slots(barber, service, date):
            if start <= now:
                continue
            if blocking_bookings(barber, start, end).exists():
                continue
            free.append({"start": start.strftime('%H:%M'), "end": end.strftime('%H:%M')})

        return Response({"slots": free})
class BookingCreateView(CreateAPIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'booking'
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer

    def perform_create(self, serializer):
        booking = serializer.save()
        site = SiteSettings.load()

        payment_block = ""
        if site.has_bank_details:
            payment_block = (
                "Pay by bank transfer to:\n"
                f"  Bank: {site.bank_name}\n"
                f"  Account name: {site.account_name}\n"
                f"  Sort code: {site.sort_code}\n"
                f"  Account number: {site.account_number}\n"
                f"  Payment reference: {booking.reference}\n\n"
            )
        policy_block = f"Cancellation policy:\n{site.cancellation_policy}\n\n" if site.cancellation_policy else ""

        try:
            send_mail(
                subject=f"Booking Received: Payment Needed to Secure Your Slot ({booking.reference})",
                message=(
                    f"Hi {booking.customer_name},\n\n"
                    f"Thanks for booking with Hair Klinics. We've received your booking request, "
                    f"but it is NOT confirmed yet.\n\n"
                    f"Reference: {booking.reference}\n"
                    f"Service: {booking.service.name}\n"
                    f"When: {booking.when_display}\n\n"
                    f"IMPORTANT: this email is not proof of payment. Your slot is only held for "
                    f"{settings.BOOKING_HOLD_MINUTES} minutes. To secure and guarantee it, please pay by bank "
                    f"transfer and email your proof of payment to bookings@hairklinics.com, quoting "
                    f"{booking.reference}. If we don't receive payment in time, the slot is released and may "
                    f"be given to another customer.\n\n"
                    f"{payment_block}"
                    f"{policy_block}"
                    f"We'll email you again as soon as your payment is confirmed.\n\n"
                    f"Thanks,\nHair Klinics"
                ),
                from_email=None,
                recipient_list=[booking.customer_email],
                fail_silently=False,
            )
        except Exception:
            logger.exception("Booking email failed for %s", booking.reference)
            

class PaymentClaimView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'payment_claim'

    def post(self, request):
        reference = str(request.data.get('reference', '')).strip().upper()
        email = str(request.data.get('email', '')).strip()
        booking = Booking.objects.filter(reference=reference, customer_email__iexact=email).first()

        if booking is None or booking.status == 'cancelled':
            return Response({'detail': 'We could not find that booking.'}, status=404)
        if booking.status in ('confirmed', 'completed'):
            return Response({'ok': True})  # nothing to do

        # pending or expired: is the slot still free?
        clash = blocking_bookings(booking.barber, booking.start_time, booking.end_time).exclude(pk=booking.pk).exists()
        if clash:
            self._notify(request, booking, slot_lost=True)
            return Response({'slot_lost': True}, status=409)

        if booking.payment_claimed_at is None:
            booking.payment_claimed_at = timezone.now()
            booking.status = 'pending'  # an expired booking comes back to life
            booking.save(update_fields=['status', 'payment_claimed_at'])
            self._notify(request, booking, slot_lost=False)
        return Response({'ok': True})

    def _notify(self, request, booking, slot_lost):
        admin_link = request.build_absolute_uri(f"/admin/bookings/booking/?q={booking.reference}")
        if slot_lost:
            subject = f"Payment claimed but slot was released: {booking.reference}"
            note = ("Their hold ran out and the slot has since been booked by someone else. "
                    "Contact them to rebook or refund.")
        else:
            until = timezone.localtime(
                booking.payment_claimed_at + timedelta(hours=settings.BOOKING_CLAIMED_HOLD_HOURS)
            )
            subject = f"Payment claimed: {booking.reference} ({booking.customer_name})"
            note = ("Check the bank account. If the money is there, set the booking to Confirmed in the admin. "
                    f"The slot is held until {until:%H:%M on %d %B} unless you confirm or cancel it first.")
        try:
            send_mail(
                subject=subject,
                message=(
                    f"{booking.customer_name} says they've paid for booking {booking.reference}.\n\n"
                    f"Service: {booking.service.name}\n"
                    f"When: {booking.when_display}\n"
                    f"Phone: {booking.customer_phone}\n"
                    f"Email: {booking.customer_email}\n\n"
                    f"{note}\n\n"
                    f"Open in admin: {admin_link}\n"
                ),
                from_email=None,
                recipient_list=[settings.BOOKING_NOTIFY_EMAIL],
                fail_silently=False,
            )
        except Exception:
            logger.exception("Payment-claim email failed for %s", booking.reference)