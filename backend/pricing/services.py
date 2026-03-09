"""
Pricing Calculation Engine

Service layer that implements actual price calculation logic
Separated from models for clean architecture
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Optional
from django.utils import timezone
import math

from .models import PricingRule, PricingStrategy, UserSubscription


class PricingCalculator:
    """
    Core pricing calculation engine
    
    Design: Strategy pattern for different pricing models
    Extensible for new strategies without modifying existing code
    """
    
    @staticmethod
    def calculate_price(
        facility_id,
        entry_time: datetime,
        exit_time: Optional[datetime] = None,
        vehicle_type: str = None,
        spot_size: str = None,
        user_id = None
    ) -> Dict:
        """
        Calculate parking price
        
        Returns:
        {
            "base_price": Decimal,
            "penalties": Decimal,
            "discounts": Decimal,
            "total": Decimal,
            "duration_minutes": int,
            "applied_rule": str,
            "subscription_used": bool
        }
        """
        
        # Check for active subscription first
        if user_id:
            subscription = PricingCalculator._check_subscription(user_id, facility_id)
            if subscription:
                return {
                    "base_price": Decimal("0.00"),
                    "penalties": Decimal("0.00"),
                    "discounts": Decimal("0.00"),
                    "total": Decimal("0.00"),
                    "duration_minutes": 0,
                    "applied_rule": "Subscription",
                    "subscription_used": True,
                    "subscription_id": str(subscription.id)
                }
        
        # Use current time if exit not provided (for estimate)
        if not exit_time:
            exit_time = timezone.now()
        
        # Calculate duration
        duration = exit_time - entry_time
        duration_minutes = int(duration.total_seconds() / 60)
        duration_hours = duration_minutes / 60.0
        
        # Find applicable pricing rule
        rule = PricingCalculator._find_applicable_rule(
            facility_id, vehicle_type, spot_size
        )
        
        if not rule:
            # Fallback to default hourly rate
            base_price = Decimal("5.00") * Decimal(str(math.ceil(duration_hours)))
            return {
                "base_price": base_price,
                "penalties": Decimal("0.00"),
                "discounts": Decimal("0.00"),
                "total": base_price,
                "duration_minutes": duration_minutes,
                "applied_rule": "Default Hourly",
                "subscription_used": False
            }
        
        # Apply free minutes
        chargeable_minutes = max(0, duration_minutes - rule.free_minutes)
        chargeable_hours = chargeable_minutes / 60.0
        
        # Calculate base price based on strategy
        if rule.strategy == PricingStrategy.FLAT_RATE:
            base_price = PricingCalculator._calculate_flat_rate(rule, chargeable_hours)
        elif rule.strategy == PricingStrategy.HOURLY:
            base_price = PricingCalculator._calculate_hourly(rule, chargeable_hours)
        elif rule.strategy == PricingStrategy.SLAB:
            base_price = PricingCalculator._calculate_slab(rule, chargeable_hours)
        elif rule.strategy == PricingStrategy.DYNAMIC:
            base_price = PricingCalculator._calculate_dynamic(
                rule, entry_time, exit_time, chargeable_hours
            )
        else:
            base_price = Decimal("0.00")
        
        # Calculate penalties (if applicable)
        penalties = Decimal("0.00")
        
        total = base_price + penalties
        
        return {
            "base_price": base_price,
            "penalties": penalties,
            "discounts": Decimal("0.00"),
            "total": total,
            "duration_minutes": duration_minutes,
            "applied_rule": rule.name,
            "subscription_used": False
        }
    
    @staticmethod
    def _find_applicable_rule(facility_id, vehicle_type, spot_size):
        """Find the highest priority applicable pricing rule"""
        from .models import PricingRule
        
        rules = PricingRule.objects.filter(
            facility_id=facility_id,
            is_active=True
        ).order_by("-priority")
        
        for rule in rules:
            if not rule.is_valid_now():
                continue
            
            # Check vehicle type filter
            if rule.applies_to_vehicle_types:
                if vehicle_type not in rule.applies_to_vehicle_types:
                    continue
            
            # Check spot size filter
            if rule.applies_to_spot_sizes:
                if spot_size not in rule.applies_to_spot_sizes:
                    continue
            
            return rule
        
        return None
    
    @staticmethod
    def _check_subscription(user_id, facility_id):
        """Check if user has active subscription for this facility"""
        subscription = UserSubscription.objects.filter(
            user_id=user_id,
            subscription__facility_id=facility_id,
            is_active=True
        ).select_related("subscription").first()
        
        if subscription and subscription.is_valid():
            return subscription
        
        return None
    
    @staticmethod
    def _calculate_flat_rate(rule, hours) -> Decimal:
        """Flat rate per entry"""
        return Decimal(str(rule.config.get("flat_rate", 10.00)))
    
    @staticmethod
    def _calculate_hourly(rule, hours) -> Decimal:
        """
        Hourly rate calculation
        
        Config example:
        {
            "base_rate": 5.00,  # First hour
            "after_hours": 1,  # After this many hours
            "hourly_rate": 3.00  # Rate per additional hour
        }
        """
        config = rule.config
        base_rate = Decimal(str(config.get("base_rate", 5.00)))
        after_hours = config.get("after_hours", 1)
        hourly_rate = Decimal(str(config.get("hourly_rate", 3.00)))
        
        if hours <= after_hours:
            return base_rate * Decimal(str(math.ceil(hours)))
        
        # Base rate for first hours + hourly rate for rest
        additional_hours = hours - after_hours
        return (base_rate * Decimal(str(after_hours))) + \
               (hourly_rate * Decimal(str(math.ceil(additional_hours))))
    
    @staticmethod
    def _calculate_slab(rule, hours) -> Decimal:
        """
        Slab-based pricing
        
        Config example:
        {
            "slabs": [
                {"max_hours": 1, "price": 5},
                {"max_hours": 3, "price": 12},
                {"max_hours": 6, "price": 20},
                {"max_hours": null, "price": 30}
            ]
        }
        """
        slabs = rule.config.get("slabs", [])
        
        for slab in slabs:
            max_hours = slab.get("max_hours")
            if max_hours is None or hours <= max_hours:
                return Decimal(str(slab.get("price", 0)))
        
        # Fallback
        return Decimal("10.00")
    
    @staticmethod
    def _calculate_dynamic(rule, entry_time, exit_time, hours) -> Decimal:
        """
        Dynamic pricing based on time of day
        
        Config example:
        {
            "peak_hours": [
                {
                    "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                    "start": "08:00",
                    "end": "18:00",
                    "rate": 8.00
                }
            ],
            "off_peak_rate": 4.00
        }
        
        Note: Simplified implementation. Production would calculate
        hour-by-hour based on entry/exit spanning peak/off-peak
        """
        config = rule.config
        
        # Check if entry is during peak hours
        day_name = entry_time.strftime("%A").lower()
        entry_hour = entry_time.hour
        
        peak_hours = config.get("peak_hours", [])
        off_peak_rate = Decimal(str(config.get("off_peak_rate", 5.00)))
        
        for peak in peak_hours:
            if day_name in [d.lower() for d in peak.get("days", [])]:
                start_hour = int(peak.get("start", "00:00").split(":")[0])
                end_hour = int(peak.get("end", "23:59").split(":")[0])
                
                if start_hour <= entry_hour < end_hour:
                    # Peak rate applies
                    peak_rate = Decimal(str(peak.get("rate", 8.00)))
                    return peak_rate * Decimal(str(math.ceil(hours)))
        
        # Off-peak rate
        return off_peak_rate * Decimal(str(math.ceil(hours)))


class PriceEstimator:
    """
    Provide price estimates before parking
    """
    
    @staticmethod
    def estimate_for_duration(facility_id, duration_hours: float, 
                             vehicle_type: str = None, user_id = None) -> Dict:
        """
        Estimate price for a given duration
        """
        now = timezone.now()
        future = now + timedelta(hours=duration_hours)
        
        return PricingCalculator.calculate_price(
            facility_id=facility_id,
            entry_time=now,
            exit_time=future,
            vehicle_type=vehicle_type,
            user_id=user_id
        )
