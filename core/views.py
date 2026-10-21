from datetime import date, datetime

from django.conf import settings
from django.db.models import Prefetch
from django.shortcuts import render

from barbers.models import Barber
from bookings.models import TimeBlock
from services.models import ServiceCategory, Service
from .models import GalleryImage


def _active_categories():
    return ServiceCategory.objects.prefetch_related(
        Prefetch('services', queryset=Service.objects.filter(is_active=True))
    )


def _fmt_minutes(m):
    h, r = divmod(m, 60)
    if h and r:
        return f"{h} hr {r} min"
    if h:
        return f"{h} hr"
    return f"{r} min"


def _block_label():
    today = date.today()
    lengths = [
        int((datetime.combine(today, b.end_time) - datetime.combine(today, b.start_time)).total_seconds() // 60)
        for b in TimeBlock.objects.all()
    ]
    if not lengths:
        return ''
    lo, hi = min(lengths), max(lengths)
    return _fmt_minutes(lo) if lo == hi else f"{_fmt_minutes(lo)} – {_fmt_minutes(hi)}"


def home(request):
    return render(request, 'home.html')


def services(request):
    return render(request, 'services.html', {
        'categories': _active_categories(),
        'block_label': _block_label(),
    })


def book(request):
    return render(request, 'book.html', {
        'categories': _active_categories(),
        'barbers': Barber.objects.filter(is_active=True),
        'selected_service_id': request.GET.get('service', ''),
        'hold_minutes': settings.BOOKING_HOLD_MINUTES,
        'block_label': _block_label(),
    })


def gallery(request):
    images = GalleryImage.objects.filter(is_active=True)
    return render(request, 'gallery.html', {'images': images})


def contact(request):
    return render(request, 'contact.html')