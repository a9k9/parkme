from django.contrib import admin
from .models import Facility, Zone, ParkingSpot, FacilityStaff


class ZoneInline(admin.TabularInline):
    model = Zone
    extra = 0
    fields = ["name", "code", "is_covered", "total_spots", "available_spots", "is_active"]
    readonly_fields = ["total_spots", "available_spots"]


@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = ["name", "city", "facility_type", "owner", "total_spots", "available_spots", "is_active", "is_verified"]
    list_filter = ["facility_type", "city", "is_active", "is_verified", "has_ev_charging"]
    search_fields = ["name", "city", "address", "owner__email"]
    readonly_fields = ["id", "slug", "total_spots", "available_spots", "created_at", "updated_at"]
    inlines = [ZoneInline]
    
    fieldsets = (
        (None, {"fields": ("id", "owner", "name", "slug", "facility_type", "description")}),
        ("Location", {"fields": ("address", "city", "state", "postal_code", "country", "latitude", "longitude")}),
        ("Contact", {"fields": ("phone", "email")}),
        ("Features", {"fields": ("has_ev_charging", "has_covered_parking", "has_security", "has_cctv", "has_valet")}),
        ("Stats", {"fields": ("total_spots", "available_spots")}),
        ("Status", {"fields": ("is_active", "is_verified")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "facility", "total_spots", "available_spots", "is_active"]
    list_filter = ["facility", "is_active", "is_covered"]
    search_fields = ["name", "code", "facility__name"]
    readonly_fields = ["id", "total_spots", "available_spots", "created_at", "updated_at"]


@admin.register(ParkingSpot)
class ParkingSpotAdmin(admin.ModelAdmin):
    list_display = ["spot_number", "zone", "size", "status", "has_ev_charger", "is_accessible", "is_active"]
    list_filter = ["status", "size", "has_ev_charger", "is_accessible", "is_active"]
    search_fields = ["spot_number", "zone__name", "zone__facility__name"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(FacilityStaff)
class FacilityStaffAdmin(admin.ModelAdmin):
    list_display = ["staff_member", "facility", "is_active", "assigned_at"]
    list_filter = ["facility", "is_active"]
    search_fields = ["staff_member__email", "facility__name"]
    readonly_fields = ["id", "assigned_at"]
