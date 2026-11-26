from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html

from .models import GalleryImage, HeroSlide, SiteSettings


class PhotoAdminMixin:
    @admin.display(description="Preview")
    def preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:60px; border-radius:4px;">', obj.image.url)
        return "-"


@admin.register(GalleryImage)
class GalleryImageAdmin(PhotoAdminMixin, admin.ModelAdmin):
    list_display = ('preview', 'caption', 'order', 'is_active')
    list_editable = ('order', 'is_active')


@admin.register(HeroSlide)
class HeroSlideAdmin(PhotoAdminMixin, admin.ModelAdmin):
    list_display = ('preview', 'alt_text', 'order', 'is_active')
    list_editable = ('order', 'is_active')


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj = SiteSettings.load()
        return redirect(reverse('admin:core_sitesettings_change', args=[obj.pk]))