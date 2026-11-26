from django.contrib import admin, messages
from .models import BarberAvailability, Booking, TimeBlock
from django.core.exceptions import ValidationError
from .scheduling import run_cleanup
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
  
  
    @admin.display(boolean=True, description="Says paid")
    def says_paid(self, obj):
        return obj.payment_claimed_at is not None
    
    def changelist_view(self, request, extra_context=None):
        run_cleanup()
        return super().changelist_view(request, extra_context)
    
    def _set_status(self, request, queryset, status):
        done = 0
        for booking in queryset:
            if booking.status == status:
                continue
            booking.status = status
            try:
                booking.clean()
            except ValidationError as e:
                self.message_user(request, f"{booking.reference}: {'; '.join(e.messages)}", level=messages.ERROR)
                continue
            booking.save()  # save() sends the status emails
            done += 1
        self.message_user(request, f"{done} booking(s) marked as {status}.")

    @admin.action(description="Mark selected bookings as Confirmed")
    def mark_confirmed(self, request, queryset):
        self._set_status(request, queryset, 'confirmed')

    @admin.action(description="Mark selected bookings as Cancelled")
    def mark_cancelled(self, request, queryset):
        self._set_status(request, queryset, 'cancelled')

    @admin.action(description="Mark selected bookings as Completed")
    def mark_completed(self, request, queryset):
        self._set_status(request, queryset, 'completed')
        
@admin.register(TimeBlock)
class TimeBlockAdmin(admin.ModelAdmin):
    list_display = ('start_time', 'end_time')