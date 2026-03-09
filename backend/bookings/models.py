"""
Booking and Parking Session Management

CRITICAL: Implements concurrency control to prevent double-booking
Using database-level locking with select_for_update()

Supports two flows:
1. Reservation-based (book in advance)
2. Drive-in (ticket at entry)
"""

import uuid
from django.db import models, transaction
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError


class BookingType(models.TextChoices):
    """Booking flow type"""
    RESERVATION = "RESERVATION", "Advance Reservation"
    DRIVE_IN = "DRIVE_IN", "Drive-In (Walk-up)"


class BookingStatus(models.TextChoices):
    """
    Booking lifecycle states
    
    PENDING → CONFIRMED → ACTIVE → COMPLETED
                       ↓
                    CANCELLED
    """
    PENDING = "PENDING", "Pending Payment"
    CONFIRMED = "CONFIRMED", "Confirmed"
    ACTIVE = "ACTIVE", "Currently Parked"
    COMPLETED = "COMPLETED", "Completed"
    CANCELLED = "CANCELLED", "Cancelled"
    NO_SHOW = "NO_SHOW", "No Show"


class Booking(models.Model):
    """
    Parking booking/session
    
    CONCURRENCY CONTROL:
    - Uses select_for_update() when checking spot availability
    - Database row-level locking prevents double booking
    - Transaction atomicity ensures consistency
    
    Design rationale for select_for_update():
    - Prevents race conditions in high-traffic scenarios
    - More reliable than optimistic locking for parking
    - Acceptable performance impact for critical operations
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # References
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="bookings"
    )
    vehicle = models.ForeignKey(
        "vehicles.Vehicle",
        on_delete=models.PROTECT,
        related_name="bookings"
    )
    spot = models.ForeignKey(
        "parking.ParkingSpot",
        on_delete=models.PROTECT,
        related_name="bookings"
    )
    facility = models.ForeignKey(
        "parking.Facility",
        on_delete=models.PROTECT,
        related_name="bookings"
    )
    
    # Booking details
    booking_type = models.CharField(
        max_length=20,
        choices=BookingType.choices,
        default=BookingType.DRIVE_IN
    )
    status = models.CharField(
        max_length=20,
        choices=BookingStatus.choices,
        default=BookingStatus.PENDING,
        db_index=True
    )
    
    # Ticket/confirmation number (for user reference)
    ticket_number = models.CharField(max_length=50, unique=True, db_index=True)
    
    # Timing
    entry_time = models.DateTimeField(db_index=True)
    expected_exit = models.DateTimeField(null=True, blank=True)
    actual_exit = models.DateTimeField(null=True, blank=True, db_index=True)
    
    # Grace period (minutes after expected_exit before penalty)
    grace_period_minutes = models.PositiveIntegerField(default=15)
    
    # Pricing
    estimated_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    final_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Payment reference
    payment = models.ForeignKey(
        "payments.Payment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="booking"
    )
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    # Audit
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "bookings"
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["facility", "status", "entry_time"]),
            models.Index(fields=["spot", "status"]),
            models.Index(fields=["ticket_number"]),
            models.Index(fields=["status", "entry_time"]),
        ]
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"{self.ticket_number} - {self.user.email}"
    
    def clean(self):
        """Validation logic"""
        if self.expected_exit and self.entry_time:
            if self.expected_exit <= self.entry_time:
                raise ValidationError("Expected exit must be after entry time")
    
    def is_overstay(self):
        """Check if booking has overstayed"""
        if not self.expected_exit or not self.actual_exit:
            return False
        
        grace_end = self.expected_exit + timezone.timedelta(
            minutes=self.grace_period_minutes
        )
        return self.actual_exit > grace_end
    
    def duration_minutes(self):
        """Calculate actual parking duration"""
        if not self.actual_exit:
            return None
        
        delta = self.actual_exit - self.entry_time
        return int(delta.total_seconds() / 60)


class BookingExtension(models.Model):
    """
    Booking extension requests
    
    User can extend their booking if needed
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="extensions"
    )
    
    previous_exit = models.DateTimeField()
    new_exit = models.DateTimeField()
    additional_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    is_approved = models.BooleanField(default=True)
    
    requested_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = "booking_extensions"
        ordering = ["-requested_at"]
    
    def __str__(self):
        return f"Extension for {self.booking.ticket_number}"
