from django.contrib import admin
from .models import BarberAvailability, Booking

# Register your models here.
@admin.register(BarberAvailability)
class BarberAvailabilityAdmin(admin.ModelAdmin):
    list_display = ('barber', 'weekday', 'start_time', 'end_time')
    list_filter = ('barber', 'weekday')
    search_fields = ('barber__name',)

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('reference', 'customer_name', 'barber', 'service', 'start_time', 'status', 'updated_at')
    list_filter = ('status', 'barber')
    list_editable = ('status',)
    search_fields = ('reference', 'customer_name', 'customer_email', 'customer_phone')
    ordering = ('-start_time',)
    actions = ['mark_confirmed', 'mark_cancelled', 'mark_completed']

    @admin.action(description="Mark selected bookings as Confirmed")
    def mark_confirmed(self, request, queryset):
        queryset.update(status='confirmed')

    @admin.action(description="Mark selected bookings as Cancelled")
    def mark_cancelled(self, request, queryset):
        queryset.update(status='cancelled')

    @admin.action(description="Mark selected bookings as Completed")
    def mark_completed(self, request, queryset):
        queryset.update(status='completed')