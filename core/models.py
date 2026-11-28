import os
from io import BytesIO
from django.core.files.base import ContentFile
from django.db import models
from PIL import Image, ImageOps


def optimize_image(field_file, max_side=1800):
    """Shrink large phone photos so pages stay fast. Returns (new_name, ContentFile)."""
    img = Image.open(field_file)
    img = ImageOps.exif_transpose(img)
    img.thumbnail((max_side, max_side))
    if img.mode != 'RGB':
        img = img.convert('RGB')
    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=82, optimize=True)
    base = os.path.splitext(os.path.basename(field_file.name))[0]
    return f"{base}.jpg", ContentFile(buffer.getvalue())


class GalleryImage(models.Model):
    image = models.ImageField(upload_to='gallery/')
    caption = models.CharField(max_length=150, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.caption or f"Gallery image {self.id}"

    def save(self, *args, **kwargs):
        if self.image and not self.image._committed:  # only for newly uploaded files
            name, content = optimize_image(self.image)
            self.image.save(name, content, save=False)
        super().save(*args, **kwargs)


class HeroSlide(models.Model):
    image = models.ImageField(
        upload_to='hero/',
        help_text="Portrait photos work best (about 4:5, for example 1200 x 1500).",
    )
    alt_text = models.CharField(
        max_length=150, blank=True,
        help_text="Short description of the photo, e.g. 'Full head of starter locs'.",
    )
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.alt_text or f"Hero slide {self.id}"

    def save(self, *args, **kwargs):
        if self.image and not self.image._committed:
            name, content = optimize_image(self.image)
            self.image.save(name, content, save=False)
        super().save(*args, **kwargs)
        
class SiteSettings(models.Model):
    """One row only. The client edits this in the admin."""
    bank_name = models.CharField(max_length=100, blank=True)
    account_name = models.CharField(max_length=100, blank=True, default="Hair Klinics")
    sort_code = models.CharField(max_length=8, blank=True, help_text="For example 12-34-56")
    account_number = models.CharField(max_length=8, blank=True)
    cancellation_policy = models.TextField(
        blank=True,
        help_text="Shown on the booking page and in the booking email. A blank line starts a new paragraph.",
    )
    deposit_amount = models.DecimalField(
        max_digits=6, decimal_places=2, default=10,
        help_text="Deposit customers pay to secure a booking, in pounds. Set to 0 to turn it off.",
    )
    deposit_terms = models.CharField(
        max_length=250, blank=True,
        help_text="Optional. Shown next to the deposit, e.g. 'Deducted from your total on the day.'",
    )
    
    class Meta:
        verbose_name = "Site settings"
        verbose_name_plural = "Site settings"

    def __str__(self):
        return "Site settings"

    def save(self, *args, **kwargs):
        self.pk = 1  # there is only ever one row
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @property
    def has_bank_details(self):
        return all([self.bank_name, self.account_name, self.sort_code, self.account_number])
    
    @property
    def has_deposit(self):
        return self.deposit_amount > 0