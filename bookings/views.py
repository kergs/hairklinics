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

class AvailabilityView(APIView):
    def get(self, request):
        serializer = AvailabilityQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        barber = serializer.validated_data['barber']
        service = serializer.validated_data['service']
        date = serializer.validated_data['date']

        weekday = date.weekday()  # Monday=0 ... Sunday=6

       # finding the barber's working window for this weekday
        try:
            availability = BarberAvailability.objects.get(barber=barber, weekday=weekday)
        except BarberAvailability.DoesNotExist:
            return Response({"slots": []})  # barber doesn't work this day

        # build the full list of possible slots, spaced by service duration
        duration = timedelta(minutes=service.duration_minutes)
        slot_start = timezone.make_aware(datetime.combine(date, availability.start_time))
        window_end = timezone.make_aware(datetime.combine(date, availability.end_time))
        
        possible_slots = []
        while slot_start + duration <= window_end:
            possible_slots.append(slot_start)
            slot_start += duration

        # pull existing bookings for this barber on this date
        existing_bookings = Booking.objects.filter(
            barber=barber,
            start_time__date=date,
        ).exclude(status='cancelled')

        # remove any slot that overlaps an existing booking
        free_slots = []
        for slot in possible_slots:
            slot_end = slot + duration
            overlaps = any(
                slot < b.end_time and slot_end > b.start_time
                for b in existing_bookings
            )
            if not overlaps:
                free_slots.append(slot.strftime('%H:%M'))

        return Response({"slots": free_slots})
    

class BookingCreateView(CreateAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer

    def perform_create(self, serializer):
        booking = serializer.save()
        send_mail(
            subject=f"Booking Confirmation: Hair Klinics (#{booking.id})",
            message=(
                f"Hi {booking.customer_name},\n\n"
                f"Your booking is confirmed:\n"
                f"Reference: {booking.reference}\n"
                f"Service: {booking.service.name}\n"
                f"Date & Time: {booking.start_time.strftime('%A, %d %B %Y at %H:%M')}\n\n"
                f"Please send proof of payment by email to fully secure your slot.\n\n"
                f"Thanks,\nHair Klinics"
            ),
            from_email=None,  
            recipient_list=[booking.customer_email],
            fail_silently=False,
        )