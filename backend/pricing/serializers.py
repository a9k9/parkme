from rest_framework import serializers
from .models import PricingRule, Subscription, UserSubscription


class PricingRuleSerializer(serializers.ModelSerializer):
    """Pricing rule configuration"""
    facility_name = serializers.CharField(source="facility.name", read_only=True)
    
    class Meta:
        model = PricingRule
        fields = [
            "id", "facility", "facility_name", "name", "strategy", "config",
            "applies_to_vehicle_types", "applies_to_spot_sizes", "priority",
            "free_minutes", "overstay_penalty_rate", "valid_from", "valid_until",
            "is_active", "created_at", "updated_at"
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class SubscriptionSerializer(serializers.ModelSerializer):
    """Subscription/pass plans"""
    facility_name = serializers.CharField(source="facility.name", read_only=True)
    
    class Meta:
        model = Subscription
        fields = [
            "id", "facility", "facility_name", "name", "description", "price",
            "duration_days", "entry_count", "max_duration_per_entry",
            "is_active", "created_at", "updated_at"
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class UserSubscriptionSerializer(serializers.ModelSerializer):
    """User's active subscriptions"""
    subscription_name = serializers.CharField(source="subscription.name", read_only=True)
    facility_name = serializers.CharField(source="subscription.facility.name", read_only=True)
    is_valid_now = serializers.BooleanField(source="is_valid", read_only=True)
    
    class Meta:
        model = UserSubscription
        fields = [
            "id", "user", "subscription", "subscription_name", "facility_name",
            "activated_at", "expires_at", "entries_remaining", "is_active",
            "is_valid_now"
        ]
        read_only_fields = ["id", "activated_at"]


class PriceEstimateRequestSerializer(serializers.Serializer):
    """Request for price estimation"""
    facility_id = serializers.UUIDField()
    duration_hours = serializers.FloatField(min_value=0.1)
    vehicle_type = serializers.CharField(required=False, allow_blank=True)


class PriceEstimateResponseSerializer(serializers.Serializer):
    """Price estimation response"""
    base_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    penalties = serializers.DecimalField(max_digits=10, decimal_places=2)
    discounts = serializers.DecimalField(max_digits=10, decimal_places=2)
    total = serializers.DecimalField(max_digits=10, decimal_places=2)
    duration_minutes = serializers.IntegerField()
    applied_rule = serializers.CharField()
    subscription_used = serializers.BooleanField()
