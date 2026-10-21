from django.db import models


# services/models.py

class ServiceCategory(models.Model):
    
    MODE_FLEXIBLE = 'flexible'
    MODE_BLOCKS = 'blocks'
    BOOKING_MODE_CHOICES = [
        (MODE_FLEXIBLE, 'Flexible slots (every 30 min, uses the service duration)'),
        (MODE_BLOCKS, 'Fixed time blocks (e.g. Locs)'),
     ] 
        
    name = models.CharField(max_length=100)          # "Locs — Adult"
    slug = models.SlugField(unique=True)              # "locs-adult" — matches the #cat-locs-adult anchors
    order = models.PositiveIntegerField(default=0)    # controls display order in the nav
    
    booking_mode = models.CharField(
        max_length=10,
        choices=BOOKING_MODE_CHOICES,
        default=MODE_FLEXIBLE
    )
    class Meta:
        ordering = ['order']
        verbose_name_plural = "Service categories"

    def __str__(self):
        return self.name


class Service(models.Model):
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name='services')
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    price_note = models.CharField(max_length=100, blank=True)  # for oddballs like "£20 (1st hr), £10/hr after"
    is_active = models.BooleanField(default=True)
    
    @property
    def duration_label(self):
        if self.category.booking_mode == ServiceCategory.MODE_BLOCKS:
            return ''
        return self.duration_display
    
    @property
    def duration_display(self):
        h, m = divmod(self.duration_minutes, 60)
        if h and m:
            return f"{h} hr {m} min"
        if h:
            return f"{h} hr"
        return f"{m} min"
    class Meta:
        ordering = ['category__order', 'id']

    def __str__(self):
        return f"{self.category.name} — {self.name}"