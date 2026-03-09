from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Vehicle
from .serializers import VehicleSerializer, VehicleListSerializer
from accounts.permissions import IsObjectOwner


class VehicleViewSet(viewsets.ModelViewSet):
    """
    Vehicle management endpoints
    
    Drivers can only manage their own vehicles
    Staff can view all for verification purposes
    """
    permission_classes = [IsAuthenticated, IsObjectOwner]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["vehicle_type", "is_verified", "is_active"]
    search_fields = ["plate_number", "make", "model"]
    ordering_fields = ["created_at", "plate_number"]
    ordering = ["-created_at"]
    
    def get_queryset(self):
        """
        Filter vehicles based on user role
        
        Drivers: only their vehicles
        Staff/Admin: all vehicles
        """
        user = self.request.user
        
        if user.role in ["ADMIN", "PARKING_STAFF", "PARKING_OWNER"]:
            return Vehicle.objects.all()
        
        return Vehicle.objects.filter(user=user)
    
    def get_serializer_class(self):
        if self.action == "list":
            return VehicleListSerializer
        return VehicleSerializer
    
    @action(detail=True, methods=["post"])
    def verify(self, request, pk=None):
        """
        Verify a vehicle (staff/admin only)
        
        POST /api/vehicles/{id}/verify/
        """
        if request.user.role not in ["ADMIN", "PARKING_STAFF"]:
            return Response(
                {"error": "Only staff can verify vehicles"},
                status=403
            )
        
        vehicle = self.get_object()
        vehicle.is_verified = True
        vehicle.save()
        
        return Response({"status": "verified"})
    
    @action(detail=False, methods=["get"])
    def my_vehicles(self, request):
        """
        Get current user's vehicles
        
        GET /api/vehicles/my_vehicles/
        """
        vehicles = Vehicle.objects.filter(user=request.user, is_active=True)
        serializer = VehicleListSerializer(vehicles, many=True)
        return Response(serializer.data)
