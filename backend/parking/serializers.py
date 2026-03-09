from rest_framework import serializers
from .models import Facility, Zone, ParkingSpot, FacilityStaff


class FacilitySerializer(serializers.ModelSerializer):
    """Full facility details"""
    owner_name = serializers.CharField(source="owner.get_full_name", read_only=True)
    availability_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Facility
        fields = [
            "id", "owner", "owner_name", "name", "slug", "facility_type",
            "description", "address", "city", "state", "postal_code", "country",
            "latitude", "longitude", "phone", "email", "operating_hours",
            "has_ev_charging", "has_covered_parking", "has_security", 
            "has_cctv", "has_valet", "image", "total_spots", "available_spots",
            "availability_percentage", "is_active", "is_verified",
            "created_at", "updated_at"
        ]
        read_only_fields = [
            "id", "slug", "total_spots", "available_spots", 
            "is_verified", "created_at", "updated_at"
        ]
    
    def get_availability_percentage(self, obj):
        if obj.total_spots == 0:
            return 0
        return round((obj.available_spots / obj.total_spots) * 100, 2)


class FacilityListSerializer(serializers.ModelSerializer):
    """Lightweight for list views"""
    availability = serializers.SerializerMethodField()
    
    class Meta:
        model = Facility
        fields = [
            "id", "name", "city", "facility_type", "total_spots",
            "available_spots", "availability", "has_ev_charging",
            "latitude", "longitude", "is_active"
        ]
    
    def get_availability(self, obj):
        if obj.total_spots == 0:
            return "Unknown"
        percentage = (obj.available_spots / obj.total_spots) * 100
        if percentage > 50:
            return "High"
        elif percentage > 20:
            return "Medium"
        return "Low"


class ZoneSerializer(serializers.ModelSerializer):
    """Zone with spot counts"""
    facility_name = serializers.CharField(source="facility.name", read_only=True)
    
    class Meta:
        model = Zone
        fields = [
            "id", "facility", "facility_name", "name", "code", "description",
            "is_covered", "is_accessible", "display_order", "total_spots",
            "available_spots", "is_active", "created_at", "updated_at"
        ]
        read_only_fields = ["id", "total_spots", "available_spots", "created_at", "updated_at"]


class ParkingSpotSerializer(serializers.ModelSerializer):
    """Parking spot details"""
    zone_name = serializers.CharField(source="zone.name", read_only=True)
    facility_name = serializers.CharField(source="zone.facility.name", read_only=True)
    
    class Meta:
        model = ParkingSpot
        fields = [
            "id", "zone", "zone_name", "facility_name", "spot_number",
            "size", "has_ev_charger", "is_covered", "is_accessible", "is_vip",
            "status", "current_booking", "metadata", "is_active",
            "created_at", "updated_at"
        ]
        read_only_fields = ["id", "status", "current_booking", "created_at", "updated_at"]


class ParkingSpotAvailabilitySerializer(serializers.ModelSerializer):
    """Minimal serializer for availability checks"""
    
    class Meta:
        model = ParkingSpot
        fields = ["id", "spot_number", "size", "has_ev_charger", "is_accessible", "status"]


class FacilityStaffSerializer(serializers.ModelSerializer):
    """Staff assignment"""
    staff_name = serializers.CharField(source="staff_member.get_full_name", read_only=True)
    staff_email = serializers.EmailField(source="staff_member.email", read_only=True)
    facility_name = serializers.CharField(source="facility.name", read_only=True)
    
    class Meta:
        model = FacilityStaff
        fields = [
            "id", "facility", "facility_name", "staff_member", "staff_name",
            "staff_email", "can_manage_bookings", "can_manage_violations",
            "can_view_reports", "assigned_at", "is_active"
        ]
        read_only_fields = ["id", "assigned_at"]
