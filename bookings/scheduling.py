from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from services.models import ServiceCategory
from .models import BarberAvailability, TimeBlock, Booking

SLOT_STEP = timedelta(minutes=30)


def _aware(date, t):
    return timezone.make_aware(datetime.combine(date, t))


def candidate_slots(barber, service, date):
    """Every (start, end) this service could be booked into on this date, ignoring existing bookings."""
    windows = [
        (_aware(date, a.start_time), _aware(date, a.end_time))
        for a in BarberAvailability.objects.filter(barber=barber, weekday=date.weekday())
    ]
    if not windows:
        return []

    duration = timedelta(minutes=service.duration_minutes)
    slots = []
    if service.category.booking_mode == ServiceCategory.MODE_BLOCKS:
        block_times = [(_aware(date, b.start_time), _aware(date, b.end_time)) for b in TimeBlock.objects.all()]
        longest = max((e - s for s, e in block_times), default=timedelta())
        needed = min(duration, longest)  # services longer than every block use the longest blocks
        for start, end in block_times:
            if end - start < needed:
                continue
            if any(start >= ws and end <= we for ws, we in windows):
                slots.append((start, end))
    else:
        for ws, we in windows:
            start = ws
            while start + duration <= we:
                slots.append((start, start + duration))
                start += SLOT_STEP
    return sorted(slots)


def blocking_bookings(barber, start, end):
    """Bookings that clash with this window. Expired unpaid holds don't count."""
    cutoff = timezone.now() - timedelta(minutes=settings.BOOKING_HOLD_MINUTES)
    return (
        Booking.objects.filter(barber=barber, start_time__lt=end, end_time__gt=start)
        .exclude(status='cancelled')
        .exclude(status='pending', created_at__lt=cutoff)
    )