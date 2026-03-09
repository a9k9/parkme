"""
Flexible Pricing Engine

Design philosophy:
- Schema-agnostic pricing rules (stored as JSON)
- Multiple strategy support
- Time-based pricing (peak/off-peak)
- Tiered/slab pricing
- Subscriptions and passes
- Penalty support

This design allows pricing to evolve WITHOUT database migrations
"""

import uuid
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
import parking.models


class PricingStrategy(models.TextChoices):
    """Pricing calculation methods"""
    FLAT_RATE = "FLAT_RATE", "Flat Rate (per entry)"
    HOURLY = "HOURLY", "Hourly Rate"
    SLAB = "SLAB", "Slab-based (tiered)"
    DYNAMIC = "DYNAMIC", "Dynamic (peak/off-peak)"
    SUBSCRIPTION = "SUBSCRIPTION", "Subscription/Pass"


class PricingRule(models.Model):
    """
    Pricing rules for facilities
    
    JSON-based configuration allows unlimited flexibility:
    
    HOURLY:
    {
        "base_rate": 5.00,
        "after_hours": 3,
        "hourly_rate": 3.00
    }
    
    SLAB:
    {
        "slabs": [
            {"max_hours": 1, "price": 5},
            {"max_hours": 3, "price": 12},
            {"max_hours": 6, "price": 20},
            {"max_hours": null, "price": 30}  # null = unlimited
        ]
    }
    
    DYNAMIC:
    {
        "peak_hours": [
            {"days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
             "start": "08:00", "end": "18:00", "rate": 8.00}
        ],
        "off_peak_rate": 4.00
    }
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    facility = models.ForeignKey(
        "parking.Facility",
        on_delete=models.CASCADE,
        related_name="pricing_rules"
    )
    
    name = models.CharField(max_length=200)
    strategy = models.CharField(
        max_length=20,
        choices=PricingStrategy.choices,
        default=PricingStrategy.HOURLY
    )
    
    # Configuration stored as JSON - fully flexible
    config = models.JSONField(default=dict)
    
    # Optional filters - when this rule applies
    applies_to_vehicle_types = models.JSONField(
        default=list,
        blank=True,
        help_text="Empty = all types. E.g., ['CAR', 'SUV']"
    )
    applies_to_spot_sizes = models.JSONField(
        default=list,
        blank=True,
        help_text="Empty = all sizes. E.g., ['MEDIUM', 'LARGE']"
    )
    
    # Priority for rule selection (higher = higher priority)
    priority = models.IntegerField(default=0)
    
    # Free minutes (grace period)
    free_minutes = models.PositiveIntegerField(
        default=0,
        help_text="First X minutes are free"
    )
    
    # Overstay penalty
    overstay_penalty_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))]
    )
    
    # Active period
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "pricing_rules"
        indexes = [
            models.Index(fields=["facility", "is_active", "priority"]),
            models.Index(fields=["strategy", "is_active"]),
        ]
        ordering = ["-priority", "name"]
    
    def __str__(self):
        return f"{self.facility.name} - {self.name}"
    
    def is_valid_now(self):
        """Check if rule is currently valid"""
        now = timezone.now()
        
        if not self.is_active:
            return False
        
        if self.valid_from and now < self.valid_from:
            return False
        
        if self.valid_until and now > self.valid_until:
            return False
        
        return True


class Subscription(models.Model):
    """
    Subscription/Pass system
    
    Examples:
    - Monthly pass
    - Weekly pass
    - Unlimited parking for 30 days
    - 50 entry pass
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    facility = models.ForeignKey(
        "parking.Facility",
        on_delete=models.CASCADE,
        related_name="subscriptions"
    )
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Pricing
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))]
    )
    
    # Duration or entry count
    duration_days = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Validity in days (null if entry-based)"
    )
    entry_count = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Number of entries allowed (null if time-based)"
    )
    
    # Restrictions
    max_duration_per_entry = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Max hours per single parking session"
    )
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "subscriptions"
        indexes = [
            models.Index(fields=["facility", "is_active"]),
        ]
        ordering = ["price"]
    
    def __str__(self):
        return f"{self.facility.name} - {self.name}"


class UserSubscription(models.Model):
    """
    Active user subscriptions
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="subscriptions"
    )
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name="user_subscriptions"
    )
    
    # Activation
    activated_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Usage tracking
    entries_remaining = models.PositiveIntegerField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = "user_subscriptions"
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["subscription", "is_active"]),
            models.Index(fields=["expires_at"]),
        ]
        ordering = ["-activated_at"]
    
    def __str__(self):
        return f"{self.user.email} - {self.subscription.name}"
    
    def is_valid(self):
        """Check if subscription is still valid"""
        if not self.is_active:
            return False
        
        now = timezone.now()
        
        # Check expiration
        if self.expires_at and now > self.expires_at:
            return False
        
        # Check entries remaining
        if self.entries_remaining is not None and self.entries_remaining <= 0:
            return False
        
        return True
