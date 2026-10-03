from django.urls import path
from .views import AvailabilityView, BookingCreateView

urlpatterns = [
    path('availability/', AvailabilityView.as_view(), name='availability'),
    path('bookings/', BookingCreateView.as_view(), name='booking-create'),
]