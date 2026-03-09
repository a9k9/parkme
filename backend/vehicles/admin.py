from django.contrib import admin
from .models import Vehicle


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ["plate_number", "vehicle_type", "user", "is_verified", "is_active", "created_at"]
    list_filter = ["vehicle_type", "is_verified", "is_active", "created_at"]
    search_fields = ["plate_number", "user__email", "make", "model"]
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering = ["-created_at"]
    
    fieldsets = (
        (None, {"fields": ("id", "user", "plate_number", "vehicle_type")}),
        ("Details", {"fields": ("make", "model", "year", "color", "image")}),
        ("Status", {"fields": ("is_active", "is_verified")}),
        ("Metadata", {"fields": ("metadata",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
