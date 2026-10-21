from django.contrib import admin
from .models import ServiceCategory, Service


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'order', 'booking_mode')
    list_editable = ('booking_mode',)
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('order',)
@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'category', 'duration_minutes', 'price', 'is_active')
    list_filter = ('category', 'is_active')
    list_editable = ('duration_minutes', 'price', 'is_active')
    search_fields = ('name',)
    ordering = ('category__order',)