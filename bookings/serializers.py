from rest_framework import serializers
from barbers.models import Barber
from services.models import Service
from .models import Booking
from datetime import datetime, timedelta

class AvailabilityQuerySerializer(serializers.Serializer):
    barber = serializers.PrimaryKeyRelatedField(queryset=Barber.objects.filter(is_active=True))
    service = serializers.PrimaryKeyRelatedField(queryset=Service.objects.filter(is_active=True))
    date = serializers.DateField()
  
    
class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = [
            'id', 'barber', 'service',
            'customer_name', 'customer_email', 'customer_phone',
            'start_time', 'end_time', 'status',
        ]
        read_only_fields = ['end_time', 'status']
        
    def validate(self, data):
        service = data['service']
        barber = data['barber']
        start_time = data['start_time']
        end_time = start_time + timedelta(minutes=service.duration_minutes)

        overlapping = Booking.objects.filter(
            barber=barber,
            start_time__lt=end_time,
            end_time__gt=start_time,
        ).exclude(status='cancelled')

        if overlapping.exists():
            raise serializers.ValidationError("This time slot is no longer available. Please choose another.")

        data['end_time'] = end_time
        return data