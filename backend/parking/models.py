"""
Parking Facility Management Models

Hierarchical structure: Facility → Zone/Floor → Spot

This design supports:
- Multiple facility types (malls, airports, private lots)
- Complex layouts with zones and floors
- Per-spot attributes (size, EV, accessibility)
- Real-time availability tracking
"""

import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal


class FacilityType(models.TextChoices):
    """Types of parking facilities"""
    COMMERCIAL_LOT = "COMMERCIAL_LOT", "Commercial Parking Lot"
    MALL = "MALL", "Shopping Mall"
    AIRPORT = "AIRPORT", "Airport"
    OFFICE_BUILDING = "OFFICE_BUILDING", "Office Building"
    HOTEL = "HOTEL", "Hotel"
    RESIDENTIAL = "RESIDENTIAL", "Residential"
    PRIVATE_LOT = "PRIVATE_LOT", "Private Lot"
    STREET_PARKING = "STREET_PARKING", "Street Parking"


class Facility(models.Model):
    """
    Top-level parking facility
    
    Owned by parking owner, managed by staff
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,  # Don't allow owner deletion if facility exists
        related_name="owned_facilities",
        limit_choices_to={"role": "PARKING_OWNER"}
    )
    
    # Basic info
    name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=200, unique=True, db_index=True)
    facility_type = models.CharField(
        max_length=30,
        choices=FacilityType.choices,
        default=FacilityType.COMMERCIAL_LOT
    )
    description = models.TextField(blank=True)
    
    # Location
    address = models.TextField()
    city = models.CharField(max_length=100, db_index=True)
    state = models.CharField(max_length=100, db_index=True)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default="USA")
    
    # Geographic coordinates for mobile apps
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        help_text="For map integration"
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        help_text="For map integration"
    )
    
    # Contact
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    
    # Operational hours (stored as JSON for flexibility)
    # Format: {"monday": {"open": "08:00", "close": "22:00"}, ...}
    operating_hours = models.JSONField(default=dict, blank=True)
    
    # Features
    has_ev_charging = models.BooleanField(default=False)
    has_covered_parking = models.BooleanField(default=False)
    has_security = models.BooleanField(default=True)
    has_cctv = models.BooleanField(default=False)
    has_valet = models.BooleanField(default=False)
    
    # Images
    image = models.ImageField(upload_to="facilities/", null=True, blank=True)
    
    # Stats (denormalized for performance - updated by signals/tasks)
    total_spots = models.PositiveIntegerField(default=0)
    available_spots = models.PositiveIntegerField(default=0)
    
    # Status
    is_active = models.BooleanField(default=True, db_index=True)
    is_verified = models.BooleanField(default=False)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    # Audit
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "facilities"
        verbose_name_plural = "Facilities"
        indexes = [
            models.Index(fields=["city", "is_active"]),
            models.Index(fields=["owner", "is_active"]),
            models.Index(fields=["slug"]),
        ]
        ordering = ["name"]
    
    def __str__(self):
        return f"{self.name} - {self.city}"


class Zone(models.Model):
    """
    Zone or Floor within a facility
    
    Examples:
    - Level 1, Level 2, Level B1 (floors)
    - Section A, Section B (zones)
    - VIP Area, Economy Area
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    facility = models.ForeignKey(
        Facility,
        on_delete=models.CASCADE,
        related_name="zones"
    )
    
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)  # e.g., "L1", "A", "B2"
    description = models.TextField(blank=True)
    
    # Zone properties
    is_covered = models.BooleanField(default=False)
    is_accessible = models.BooleanField(
        default=True,
        help_text="Accessibility for disabled persons"
    )
    
    # Display order for UI
    display_order = models.PositiveIntegerField(default=0)
    
    # Stats (denormalized)
    total_spots = models.PositiveIntegerField(default=0)
    available_spots = models.PositiveIntegerField(default=0)
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "zones"
        unique_together = [["facility", "code"]]
        indexes = [
            models.Index(fields=["facility", "is_active"]),
        ]
        ordering = ["display_order", "name"]
    
    def __str__(self):
        return f"{self.facility.name} - {self.name}"


class SpotSize(models.TextChoices):
    """Spot size categories"""
    SMALL = "SMALL", "Small (Motorcycle/Bicycle)"
    MEDIUM = "MEDIUM", "Medium (Car)"
    LARGE = "LARGE", "Large (SUV/Van)"
    XLARGE = "XLARGE", "Extra Large (Truck/Bus)"


class SpotStatus(models.TextChoices):
    """Real-time spot status"""
    AVAILABLE = "AVAILABLE", "Available"
    OCCUPIED = "OCCUPIED", "Occupied"
    RESERVED = "RESERVED", "Reserved"
    MAINTENANCE = "MAINTENANCE", "Under Maintenance"
    DISABLED = "DISABLED", "Disabled"


class ParkingSpot(models.Model):
    """
    Individual parking spot
    
    Critical for availability and booking logic
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    zone = models.ForeignKey(
        Zone,
        on_delete=models.CASCADE,
        related_name="spots"
    )
    
    # Identification
    spot_number = models.CharField(max_length=20)  # e.g., "A-101"
    
    # Spot characteristics
    size = models.CharField(
        max_length=10,
        choices=SpotSize.choices,
        default=SpotSize.MEDIUM,
        db_index=True
    )
    
    # Special features
    has_ev_charger = models.BooleanField(default=False, db_index=True)
    is_covered = models.BooleanField(default=False)
    is_accessible = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Handicap accessible"
    )
    is_vip = models.BooleanField(default=False)
    
    # Real-time status
    status = models.CharField(
        max_length=20,
        choices=SpotStatus.choices,
        default=SpotStatus.AVAILABLE,
        db_index=True
    )
    
    # Current occupancy (for quick checks)
    current_booking = models.ForeignKey(
        "bookings.Booking",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="occupied_spot"
    )
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    is_active = models.BooleanField(default=True, db_index=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "parking_spots"
        unique_together = [["zone", "spot_number"]]
        indexes = [
            models.Index(fields=["zone", "status", "is_active"]),
            models.Index(fields=["status", "size", "is_active"]),
            models.Index(fields=["has_ev_charger", "status"]),
        ]
        ordering = ["spot_number"]
    
    def __str__(self):
        return f"{self.zone.facility.name} - {self.zone.name} - {self.spot_number}"
    
    def is_available(self):
        """Check if spot is truly available"""
        return self.status == SpotStatus.AVAILABLE and self.is_active
    
    def can_accommodate(self, vehicle_size):
        """
        Check if spot can fit a vehicle size
        
        Logic: larger spots can accommodate smaller vehicles
        """
        size_hierarchy = {
            "small": 1,
            "medium": 2,
            "large": 3,
            "xlarge": 4
        }
        
        spot_level = size_hierarchy.get(self.size.lower(), 2)
        vehicle_level = size_hierarchy.get(vehicle_size.lower(), 2)
        
        return spot_level >= vehicle_level


class FacilityStaff(models.Model):
    """
    Staff assigned to facilities
    
    Allows multi-facility assignment for staff members
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    facility = models.ForeignKey(
        Facility,
        on_delete=models.CASCADE,
        related_name="staff_assignments"
    )
    staff_member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="facility_assignments",
        limit_choices_to={"role": "PARKING_STAFF"}
    )
    
    # Permissions can be extended
    can_manage_bookings = models.BooleanField(default=True)
    can_manage_violations = models.BooleanField(default=True)
    can_view_reports = models.BooleanField(default=False)
    
    assigned_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = "facility_staff"
        unique_together = [["facility", "staff_member"]]
        indexes = [
            models.Index(fields=["facility", "is_active"]),
            models.Index(fields=["staff_member", "is_active"]),
        ]
    
    def __str__(self):
        return f"{self.staff_member.get_full_name()} @ {self.facility.name}"
