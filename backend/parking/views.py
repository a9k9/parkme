from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

from .models import Facility, Zone, ParkingSpot, FacilityStaff, SpotStatus
from .serializers import (
    FacilitySerializer,
    FacilityListSerializer,
    ZoneSerializer,
    ParkingSpotSerializer,
    ParkingSpotAvailabilitySerializer,
    FacilityStaffSerializer
)
from accounts.permissions import IsAdmin, IsOwner, IsOwnerOrStaff


class FacilityViewSet(viewsets.ModelViewSet):
    """
    Facility management
    
    Public: List and search facilities
    Owner: Manage their facilities
    Admin: Manage all
    """
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["city", "facility_type", "has_ev_charging", "is_active"]
    search_fields = ["name", "city", "address"]
    ordering_fields = ["name", "created_at", "available_spots"]
    ordering = ["name"]
    
    def get_queryset(self):
        user = self.request.user
        
        # Public can see active facilities
        if not user.is_authenticated:
            return Facility.objects.filter(is_active=True, is_verified=True)
        
        # Admin sees all
        if user.role == "ADMIN":
            return Facility.objects.all()
        
        # Owners see their own
        if user.role == "PARKING_OWNER":
            return Facility.objects.filter(Q(owner=user) | Q(is_active=True, is_verified=True))
        
        # Others see active verified
        return Facility.objects.filter(is_active=True, is_verified=True)
    
    def get_serializer_class(self):
        if self.action == "list":
            return FacilityListSerializer
        return FacilitySerializer
    
    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        elif self.action == "create":
            return [IsAuthenticated(), IsOwner()]
        return [IsAuthenticated(), IsOwnerOrStaff()]
    
    @action(detail=True, methods=["get"])
    def availability(self, request, pk=None):
        """
        Get real-time availability for a facility
        
        GET /api/facilities/{id}/availability/
        """
        facility = self.get_object()
        spots = ParkingSpot.objects.filter(
            zone__facility=facility,
            is_active=True
        ).select_related("zone")
        
        serializer = ParkingSpotAvailabilitySerializer(spots, many=True)
        
        return Response({
            "facility": facility.name,
            "total_spots": facility.total_spots,
            "available_spots": facility.available_spots,
            "spots": serializer.data
        })
    
    @action(detail=True, methods=["post"])
    def search_spots(self, request, pk=None):
        """
        Search available spots with filters
        
        POST /api/facilities/{id}/search_spots/
        Body: {
            "vehicle_size": "medium",
            "needs_ev": true,
            "needs_accessible": false
        }
        """
        facility = self.get_object()
        
        vehicle_size = request.data.get("vehicle_size", "medium")
        needs_ev = request.data.get("needs_ev", False)
        needs_accessible = request.data.get("needs_accessible", False)
        
        # Start with available spots
        spots = ParkingSpot.objects.filter(
            zone__facility=facility,
            status=SpotStatus.AVAILABLE,
            is_active=True
        )
        
        # Apply filters
        if needs_ev:
            spots = spots.filter(has_ev_charger=True)
        
        if needs_accessible:
            spots = spots.filter(is_accessible=True)
        
        # Filter by size compatibility
        # This could be optimized with database-level logic
        compatible_spots = [
            spot for spot in spots.select_related("zone")
            if spot.can_accommodate(vehicle_size)
        ]
        
        serializer = ParkingSpotAvailabilitySerializer(compatible_spots, many=True)
        
        return Response({
            "count": len(compatible_spots),
            "spots": serializer.data
        })


class ZoneViewSet(viewsets.ModelViewSet):
    """Zone management - owner/staff only"""
    queryset = Zone.objects.all()
    serializer_class = ZoneSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrStaff]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["facility", "is_active"]
    search_fields = ["name", "code"]


class ParkingSpotViewSet(viewsets.ModelViewSet):
    """Spot management - owner/staff only"""
    queryset = ParkingSpot.objects.all()
    serializer_class = ParkingSpotSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrStaff]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["zone", "status", "size", "has_ev_charger", "is_accessible"]


class FacilityStaffViewSet(viewsets.ModelViewSet):
    """Staff assignment management"""
    queryset = FacilityStaff.objects.all()
    serializer_class = FacilityStaffSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["facility", "staff_member", "is_active"]
