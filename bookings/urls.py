from django.urls import path
from .views import AvailabilityView, BookingCreateView, PaymentClaimView

urlpatterns = [
    path('availability/', AvailabilityView.as_view(), name='availability'),
    path('bookings/', BookingCreateView.as_view(), name='booking-create'),
    path('bookings/claim-payment/', PaymentClaimView.as_view(), name='payment-claim'),
]