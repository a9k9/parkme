from rest_framework import serializers
from .models import Booking, BookingExtension


class BookingSerializer(serializers.ModelSerializer):
    """Full booking details"""
    user_email = serializers.EmailField(source="user.email", read_only=True)
    vehicle_plate = serializers.CharField(source="vehicle.plate_number", read_only=True)
    spot_number = serializers.CharField(source="spot.spot_number", read_only=True)
    facility_name = serializers.CharField(source="facility.name", read_only=True)
    duration = serializers.IntegerField(source="duration_minutes", read_only=True)
    is_overstay = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Booking
        fields = [
            "id", "user", "user_email", "vehicle", "vehicle_plate",
            "spot", "spot_number", "facility", "facility_name",
            "booking_type", "status", "ticket_number", "entry_time",
            "expected_exit", "actual_exit", "grace_period_minutes",
            "estimated_price", "final_price", "payment", "duration",
            "is_overstay", "metadata", "created_at", "updated_at"
        ]
        read_only_fields = [
            "id", "ticket_number", "final_price", "created_at", "updated_at"
        ]


class CreateReservationSerializer(serializers.Serializer):
    """Request to create reservation"""
    vehicle_id = serializers.UUIDField()
    spot_id = serializers.UUIDField()
    entry_time = serializers.DateTimeField()
    expected_exit = serializers.DateTimeField()


class CreateDriveInSerializer(serializers.Serializer):
    """Request to create drive-in booking"""
    vehicle_id = serializers.UUIDField()
    spot_id = serializers.UUIDField()


class BookingExtensionSerializer(serializers.ModelSerializer):
    """Booking extension"""
    booking_ticket = serializers.CharField(source="booking.ticket_number", read_only=True)
    
    class Meta:
        model = BookingExtension
        fields = [
            "id", "booking", "booking_ticket", "previous_exit",
            "new_exit", "additional_price", "is_approved", "requested_at"
        ]
        read_only_fields = ["id", "requested_at"]
