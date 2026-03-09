from django.contrib import admin
from .models import Booking, BookingExtension


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ["ticket_number", "user", "facility", "status", "entry_time", "actual_exit"]
    list_filter = ["status", "booking_type", "facility", "created_at"]
    search_fields = ["ticket_number", "user__email", "vehicle__plate_number"]
    readonly_fields = ["id", "ticket_number", "created_at", "updated_at"]
    ordering = ["-created_at"]


@admin.register(BookingExtension)
class BookingExtensionAdmin(admin.ModelAdmin):
    list_display = ["booking", "previous_exit", "new_exit", "is_approved", "requested_at"]
    list_filter = ["is_approved", "requested_at"]
    readonly_fields = ["id", "requested_at"]
