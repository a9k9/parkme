"""
Vehicle Management Models

Supports multiple vehicle types with extensible design
"""

import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class VehicleType(models.TextChoices):
    """
    Vehicle type enumeration - easily extensible for new types
    
    Design consideration: Using TextChoices over IntegerChoices
    for better readability in logs and API responses
    """
    MOTORCYCLE = "MOTORCYCLE", "Motorcycle"
    CAR = "CAR", "Car"
    SUV = "SUV", "SUV"
    TRUCK = "TRUCK", "Truck"
    ELECTRIC_CAR = "ELECTRIC_CAR", "Electric Car"
    ELECTRIC_SUV = "ELECTRIC_SUV", "Electric SUV"
    BICYCLE = "BICYCLE", "Bicycle"
    VAN = "VAN", "Van"
    BUS = "BUS", "Bus"
    # Future types can be added here without breaking existing data


class Vehicle(models.Model):
    """
    Vehicle model - belongs to a user (driver)
    
    Design decisions:
    - UUID for security (don't expose sequential IDs)
    - Indexed plate_number for fast lookups during entry/exit
    - Support for images (for verification)
    - Soft delete via is_active
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vehicles"
    )
    
    # Vehicle identification
    plate_number = models.CharField(max_length=20, db_index=True)
    vehicle_type = models.CharField(
        max_length=20,
        choices=VehicleType.choices,
        db_index=True
    )
    
    # Vehicle details
    make = models.CharField(max_length=50, blank=True)  # e.g., Toyota
    model = models.CharField(max_length=50, blank=True)  # e.g., Camry
    year = models.PositiveIntegerField(null=True, blank=True)
    color = models.CharField(max_length=30, blank=True)
    
    # Images for verification (e.g., at entry gates)
    image = models.ImageField(upload_to="vehicles/", null=True, blank=True)
    
    # Additional metadata (extensible JSON field)
    # Can store: insurance_expiry, registration_expiry, special_permits, etc.
    metadata = models.JSONField(default=dict, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True, db_index=True)
    is_verified = models.BooleanField(
        default=False,
        help_text="Verified by admin or through document upload"
    )
    
    # Audit fields
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "vehicles"
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["plate_number", "is_active"]),
            models.Index(fields=["vehicle_type", "is_active"]),
        ]
        unique_together = [["user", "plate_number"]]
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"{self.plate_number} - {self.get_vehicle_type_display()}"
    
    def is_electric(self):
        """Check if vehicle requires EV charging"""
        return "ELECTRIC" in self.vehicle_type
    
    def get_size_category(self):
        """
        Determine vehicle size for spot compatibility
        
        Returns: small, medium, large, xlarge
        """
        size_map = {
            VehicleType.BICYCLE: "small",
            VehicleType.MOTORCYCLE: "small",
            VehicleType.CAR: "medium",
            VehicleType.ELECTRIC_CAR: "medium",
            VehicleType.SUV: "large",
            VehicleType.ELECTRIC_SUV: "large",
            VehicleType.VAN: "large",
            VehicleType.TRUCK: "xlarge",
            VehicleType.BUS: "xlarge",
        }
        return size_map.get(self.vehicle_type, "medium")
