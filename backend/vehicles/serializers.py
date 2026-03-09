from rest_framework import serializers
from .models import Vehicle, VehicleType


class VehicleSerializer(serializers.ModelSerializer):
    """
    Vehicle serializer with automatic user assignment
    """
    user_email = serializers.EmailField(source="user.email", read_only=True)
    size_category = serializers.CharField(source="get_size_category", read_only=True)
    is_electric_vehicle = serializers.BooleanField(source="is_electric", read_only=True)
    
    class Meta:
        model = Vehicle
        fields = [
            "id", "user", "user_email", "plate_number", "vehicle_type",
            "make", "model", "year", "color", "image", "metadata",
            "is_active", "is_verified", "size_category", "is_electric_vehicle",
            "created_at", "updated_at"
        ]
        read_only_fields = ["id", "user", "is_verified", "created_at", "updated_at"]
    
    def validate_plate_number(self, value):
        """
        Validate plate number format (can be customized per region)
        """
        value = value.strip().upper()
        if len(value) < 3:
            raise serializers.ValidationError("Plate number too short")
        return value
    
    def create(self, validated_data):
        # Automatically assign current user
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class VehicleListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for vehicle lists
    """
    vehicle_type_display = serializers.CharField(source="get_vehicle_type_display", read_only=True)
    
    class Meta:
        model = Vehicle
        fields = [
            "id", "plate_number", "vehicle_type", "vehicle_type_display",
            "make", "model", "color", "is_verified", "created_at"
        ]
