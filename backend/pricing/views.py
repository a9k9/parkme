from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .models import PricingRule, Subscription, UserSubscription
from .serializers import (
    PricingRuleSerializer,
    SubscriptionSerializer,
    UserSubscriptionSerializer,
    PriceEstimateRequestSerializer
)
from .services import PriceEstimator
from accounts.permissions import IsOwner, IsOwnerOrStaff


class PricingRuleViewSet(viewsets.ModelViewSet):
    """Pricing rule management - owner/admin only"""
    queryset = PricingRule.objects.all()
    serializer_class = PricingRuleSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrStaff]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["facility", "strategy", "is_active"]


class SubscriptionViewSet(viewsets.ModelViewSet):
    """Subscription plans"""
    queryset = Subscription.objects.filter(is_active=True)
    serializer_class = SubscriptionSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["facility", "is_active"]
    
    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsOwner()]


class UserSubscriptionViewSet(viewsets.ModelViewSet):
    """User's subscriptions"""
    serializer_class = UserSubscriptionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserSubscription.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=["post"])
    def purchase(self, request):
        """
        Purchase a subscription
        
        POST /api/user-subscriptions/purchase/
        Body: {"subscription_id": "..."}
        """
        subscription_id = request.data.get("subscription_id")
        
        if not subscription_id:
            return Response(
                {"error": "subscription_id required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            subscription = Subscription.objects.get(id=subscription_id, is_active=True)
        except Subscription.DoesNotExist:
            return Response(
                {"error": "Subscription not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Calculate expiration
        from django.utils import timezone
        from datetime import timedelta
        
        expires_at = None
        if subscription.duration_days:
            expires_at = timezone.now() + timedelta(days=subscription.duration_days)
        
        # Create user subscription
        user_sub = UserSubscription.objects.create(
            user=request.user,
            subscription=subscription,
            expires_at=expires_at,
            entries_remaining=subscription.entry_count
        )
        
        # In production, this would integrate with payment gateway
        
        serializer = self.get_serializer(user_sub)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PricingEstimateViewSet(viewsets.ViewSet):
    """
    Price estimation endpoints
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=["post"])
    def estimate(self, request):
        """
        Get price estimate
        
        POST /api/pricing/estimate/
        Body: {
            "facility_id": "...",
            "duration_hours": 2.5,
            "vehicle_type": "CAR"
        }
        """
        serializer = PriceEstimateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        estimate = PriceEstimator.estimate_for_duration(
            facility_id=serializer.validated_data["facility_id"],
            duration_hours=serializer.validated_data["duration_hours"],
            vehicle_type=serializer.validated_data.get("vehicle_type"),
            user_id=request.user.id
        )
        
        return Response(estimate)
