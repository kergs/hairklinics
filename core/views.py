from django.shortcuts import render
from services.models import ServiceCategory
from .models import GalleryImage
from barbers.models import Barber

def home(request):
    return render(request, 'home.html')

def services(request):
    categories = ServiceCategory.objects.prefetch_related('services').all()
    barber = Barber.objects.filter(is_active=True).first()
    return render(request, 'services.html', {
        'categories': categories,
        'barber': barber,     
        })
    
def gallery(request):
    images = GalleryImage.objects.filter(is_active=True)
    return render(request, 'gallery.html', {'images': images})

def contact(request):
    return render(request, 'contact.html')