from django.db import models


# services/models.py

class ServiceCategory(models.Model):
    name = models.CharField(max_length=100)          # "Locs — Adult"
    slug = models.SlugField(unique=True)              # "locs-adult" — matches the #cat-locs-adult anchors
    order = models.PositiveIntegerField(default=0)    # controls display order in the nav

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

    class Meta:
        ordering = ['category__order', 'id']

    def __str__(self):
        return f"{self.category.name} — {self.name}"