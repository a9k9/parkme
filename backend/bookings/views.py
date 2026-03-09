from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.core.exceptions import ValidationError as DjangoValidationError

from .models import Booking, BookingExtension
from .serializers import (
    BookingSerializer,
    CreateReservationSerializer,
    CreateDriveInSerializer,
    BookingExtensionSerializer
)
from .services import BookingService
from vehicles.models import Vehicle


class BookingViewSet(viewsets.ModelViewSet):
    """
    Booking management
    
    Drivers: their bookings
    Staff: facility bookings
    """
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["status", "facility", "booking_type"]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role in ["ADMIN"]:
            return Booking.objects.all()
        
        if user.role in ["PARKING_OWNER", "PARKING_STAFF"]:
            # Return bookings for their facilities
            # Simplified - would need proper facility assignment check
            return Booking.objects.all()
        
        # Drivers see their own
        return Booking.objects.filter(user=user)
    
    @action(detail=False, methods=["post"])
    def reserve(self, request):
        """
        Create advance reservation
        
        POST /api/bookings/reserve/
        Body: {
            "vehicle_id": "...",
            "spot_id": "...",
            "entry_time": "2026-02-10T14:00:00Z",
            "expected_exit": "2026-02-10T18:00:00Z"
        }
        """
        serializer = CreateReservationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            vehicle = Vehicle.objects.get(
                id=serializer.validated_data["vehicle_id"],
                user=request.user
            )
        except Vehicle.DoesNotExist:
            return Response(
                {"error": "Vehicle not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            booking = BookingService.create_reservation(
                user=request.user,
                vehicle=vehicle,
                spot_id=serializer.validated_data["spot_id"],
                entry_time=serializer.validated_data["entry_time"],
                expected_exit=serializer.validated_data["expected_exit"]
            )
        except DjangoValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        response_serializer = BookingSerializer(booking)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=["post"])
    def drive_in(self, request):
        """
        Create drive-in booking (immediate entry)
        
        POST /api/bookings/drive_in/
        Body: {
            "vehicle_id": "...",
            "spot_id": "..."
        }
        """
        serializer = CreateDriveInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            vehicle = Vehicle.objects.get(
                id=serializer.validated_data["vehicle_id"],
                user=request.user
            )
        except Vehicle.DoesNotExist:
            return Response(
                {"error": "Vehicle not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            booking = BookingService.create_drive_in(
                user=request.user,
                vehicle=vehicle,
                spot_id=serializer.validated_data["spot_id"]
            )
        except DjangoValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        response_serializer = BookingSerializer(booking)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        """
        Complete booking (exit)
        
        POST /api/bookings/{id}/complete/
        """
        try:
            booking = BookingService.complete_booking(pk)
        except DjangoValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = BookingSerializer(booking)
        return Response(serializer.data)


class BookingExtensionViewSet(viewsets.ModelViewSet):
    """Booking extensions"""
    queryset = BookingExtension.objects.all()
    serializer_class = BookingExtensionSerializer
    permission_classes = [IsAuthenticated]
