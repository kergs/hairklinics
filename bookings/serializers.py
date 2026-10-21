from rest_framework import serializers
from barbers.models import Barber
from services.models import Service
from .models import Booking
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
from .scheduling import blocking_bookings, candidate_slots


class AvailabilityQuerySerializer(serializers.Serializer):
    barber = serializers.PrimaryKeyRelatedField(queryset=Barber.objects.filter(is_active=True))
    service = serializers.PrimaryKeyRelatedField(queryset=Service.objects.filter(is_active=True))
    date = serializers.DateField()
  
    
class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = [
            'id','reference', 'barber', 'service',
            'customer_name', 'customer_email', 'customer_phone',
            'start_time', 'end_time', 'status',
        ]
        read_only_fields = ['end_time', 'status', 'reference']
        
    def validate(self, data):
        service = data['service']
        barber = data['barber']
        start = data['start_time']

        if start <= timezone.now():
            raise serializers.ValidationError("That time has already passed. Please choose a later slot.")

        local_date = timezone.localtime(start).date()
        match = next((s for s in candidate_slots(barber, service, local_date) if s[0] == start), None)
        if not match:
            raise serializers.ValidationError("That time isn't available for this service. Please choose one of the listed times.")

        end = match[1]
        if blocking_bookings(barber, start, end).exists():
            raise serializers.ValidationError("This time slot is no longer available. Please choose another.")

        data['end_time'] = end
        return data