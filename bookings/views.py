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
from .scheduling import candidate_slots, blocking_bookings

class AvailabilityView(APIView):
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
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer

    def perform_create(self, serializer):
        booking = serializer.save()
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
                f"{settings.BOOKING_HOLD_MINUTES} minutes. To secure and guarantee it, please pay by bank transfer "
                f"and email your proof of payment to bookings@hairklinics.com, quoting {booking.reference}. "
                f"If we don't receive payment in time, the slot is released and may be given to another customer.\n\n"
                f"We'll email you again as soon as your payment is confirmed.\n\n"
                f"Thanks,\nHair Klinics"
            ),
            from_email=None,
            recipient_list=[booking.customer_email],
            fail_silently=False,
        )