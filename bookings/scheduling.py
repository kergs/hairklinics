from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from services.models import ServiceCategory
from .models import BarberAvailability, TimeBlock, Booking
from django.db.models import Q
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


def stale_pending():
    """Pending bookings whose hold has run out."""
    now = timezone.now()
    hold_cutoff = now - timedelta(minutes=settings.BOOKING_HOLD_MINUTES)
    claimed_cutoff = now - timedelta(hours=settings.BOOKING_CLAIMED_HOLD_HOURS)
    return Q(status='pending') & Q(created_at__lt=hold_cutoff) & (
        Q(payment_claimed_at__isnull=True) | Q(payment_claimed_at__lt=claimed_cutoff)
    )


def blocking_bookings(barber, start, end):
    """Bookings that clash with this window."""
    return (
        Booking.objects.filter(barber=barber, start_time__lt=end, end_time__gt=start)
        .exclude(status__in=['cancelled', 'expired'])
        .exclude(stale_pending())
    )


def expire_stale_bookings():
    """Mark unpaid bookings whose hold ran out as Expired. Returns how many."""
    return Booking.objects.filter(stale_pending()).update(status='expired', updated_at=timezone.now())


def purge_old_expired_bookings():
    """Delete Expired and Cancelled bookings once they are older than the retention period."""
    cutoff = timezone.now() - timedelta(days=settings.BOOKING_EXPIRED_RETENTION_DAYS)
    deleted, _ = Booking.objects.filter(status__in=['expired', 'cancelled'], updated_at__lt=cutoff).delete()
    return deleted


def run_cleanup():
    """Expire stale unpaid bookings, then delete old expired ones."""
    expire_stale_bookings()
    purge_old_expired_bookings()