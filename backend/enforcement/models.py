"""
Violations and Enforcement

Tracks parking violations and penalties
"""

import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class ViolationType(models.TextChoices):
    """Types of violations"""
    OVERSTAY = "OVERSTAY", "Overstay"
    NO_TICKET = "NO_TICKET", "No Ticket/Unauthorized"
    WRONG_SPOT = "WRONG_SPOT", "Wrong Spot"
    BLOCKED_EXIT = "BLOCKED_EXIT", "Blocking Exit"
    HANDICAP_VIOLATION = "HANDICAP_VIOLATION", "Handicap Spot Violation"
    OTHER = "OTHER", "Other"


class ViolationStatus(models.TextChoices):
    """Violation states"""
    PENDING = "PENDING", "Pending Review"
    CONFIRMED = "CONFIRMED", "Confirmed"
    DISPUTED = "DISPUTED", "Under Dispute"
    RESOLVED = "RESOLVED", "Resolved"
    WAIVED = "WAIVED", "Waived"


class Violation(models.Model):
    """
    Parking violations
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # References
    facility = models.ForeignKey(
        "parking.Facility",
        on_delete=models.PROTECT,
        related_name="violations"
    )
    booking = models.ForeignKey(
        "bookings.Booking",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="violations"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="violations"
    )
    vehicle = models.ForeignKey(
        "vehicles.Vehicle",
        on_delete=models.PROTECT,
        related_name="violations"
    )
    
    # Violation details
    violation_type = models.CharField(
        max_length=30,
        choices=ViolationType.choices,
        db_index=True
    )
    description = models.TextField()
    
    # Penalty
    penalty_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Evidence
    photo_evidence = models.ImageField(upload_to="violations/", null=True, blank=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=ViolationStatus.choices,
        default=ViolationStatus.PENDING,
        db_index=True
    )
    
    # Who reported
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="reported_violations"
    )
    
    # Timestamps
    violation_time = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(default=timezone.now)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = "violations"
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["facility", "status"]),
            models.Index(fields=["violation_type", "status"]),
        ]
        ordering = ["-violation_time"]
    
    def __str__(self):
        return f"{self.violation_type} - {self.user.email}"
