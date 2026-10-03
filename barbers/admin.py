from django.contrib import admin
from.models import Barber
# Register your models here.


@admin.register(Barber)
class BarberAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('name',)