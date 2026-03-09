"""
Booking Service Layer with Concurrency Control

CRITICAL SECTION: Uses database-level locking to prevent double-booking
"""

from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal
import secrets

from .models import Booking, BookingStatus, BookingType
from parking.models import ParkingSpot, SpotStatus
from pricing.services import PricingCalculator


class BookingService:
    """
    Business logic for booking operations
    
    CONCURRENCY STRATEGY: select_for_update()
    
    Why select_for_update()?
    1. Prevents double-booking in high-traffic scenarios
    2. Database-level pessimistic locking
    3. Works across multiple application instances
    4. Simple and reliable for critical operations
    
    Alternative considered:
    - Optimistic locking: Would require version fields, retry logic
    - Redis locks: Added complexity, another dependency
    - Database constraints: Limited flexibility for business rules
    
    Trade-off: Small performance hit on writes, but ensures data integrity
    """
    
    @staticmethod
    @transaction.atomic
    def create_reservation(user, vehicle, spot_id, entry_time, expected_exit):
        """
        Create advance reservation
        
        Uses database transaction + row locking for atomicity
        
        Steps:
        1. Lock the spot row (select_for_update)
        2. Verify availability
        3. Create booking
        4. Update spot status
        5. Commit transaction (releases lock)
        """
        
        # CRITICAL: Lock the spot row for update
        # This prevents other transactions from booking the same spot
        try:
            spot = ParkingSpot.objects.select_for_update(nowait=False).get(
                id=spot_id,
                is_active=True
            )
        except ParkingSpot.DoesNotExist:
            raise ValidationError("Parking spot not found")
        
        # Check if spot is available
        if spot.status != SpotStatus.AVAILABLE:
            raise ValidationError(f"Spot is {spot.status}, cannot book")
        
        # Check if spot can accommodate vehicle
        vehicle_size = vehicle.get_size_category()
        if not spot.can_accommodate(vehicle_size):
            raise ValidationError(
                f"Spot size {spot.size} cannot accommodate {vehicle_size} vehicle"
            )
        
        # Check for conflicting reservations
        conflicting = Booking.objects.filter(
            spot=spot,
            status__in=[BookingStatus.CONFIRMED, BookingStatus.ACTIVE],
            entry_time__lt=expected_exit,
            expected_exit__gt=entry_time
        ).exists()
        
        if conflicting:
            raise ValidationError("Spot has conflicting reservation")
        
        # Generate unique ticket number
        ticket_number = BookingService._generate_ticket_number()
        
        # Calculate estimated price
        pricing = PricingCalculator.calculate_price(
            facility_id=spot.zone.facility.id,
            entry_time=entry_time,
            exit_time=expected_exit,
            vehicle_type=vehicle.vehicle_type,
            spot_size=spot.size,
            user_id=user.id
        )
        
        # Create booking
        booking = Booking.objects.create(
            user=user,
            vehicle=vehicle,
            spot=spot,
            facility=spot.zone.facility,
            booking_type=BookingType.RESERVATION,
            status=BookingStatus.CONFIRMED,
            ticket_number=ticket_number,
            entry_time=entry_time,
            expected_exit=expected_exit,
            estimated_price=pricing["total"]
        )
        
        # Update spot status
        spot.status = SpotStatus.RESERVED
        spot.current_booking = booking
        spot.save()
        
        return booking
    
    @staticmethod
    @transaction.atomic
    def create_drive_in(user, vehicle, spot_id):
        """
        Create drive-in booking (immediate entry)
        
        Similar concurrency control as reservations
        """
        
        # Lock spot
        try:
            spot = ParkingSpot.objects.select_for_update(nowait=False).get(
                id=spot_id,
                is_active=True
            )
        except ParkingSpot.DoesNotExist:
            raise ValidationError("Parking spot not found")
        
        # Must be available
        if spot.status != SpotStatus.AVAILABLE:
            raise ValidationError(f"Spot is {spot.status}")
        
        # Check size compatibility
        if not spot.can_accommodate(vehicle.get_size_category()):
            raise ValidationError("Vehicle too large for spot")
        
        ticket_number = BookingService._generate_ticket_number()
        
        # Create booking
        booking = Booking.objects.create(
            user=user,
            vehicle=vehicle,
            spot=spot,
            facility=spot.zone.facility,
            booking_type=BookingType.DRIVE_IN,
            status=BookingStatus.ACTIVE,
            ticket_number=ticket_number,
            entry_time=timezone.now()
        )
        
        # Update spot
        spot.status = SpotStatus.OCCUPIED
        spot.current_booking = booking
        spot.save()
        
        return booking
    
    @staticmethod
    @transaction.atomic
    def complete_booking(booking_id):
        """
        Complete a booking (vehicle exits)
        
        Calculate final price and release spot
        """
        
        try:
            booking = Booking.objects.select_for_update().get(id=booking_id)
        except Booking.DoesNotExist:
            raise ValidationError("Booking not found")
        
        if booking.status == BookingStatus.COMPLETED:
            raise ValidationError("Booking already completed")
        
        # Set actual exit time
        booking.actual_exit = timezone.now()
        
        # Calculate final price
        pricing = PricingCalculator.calculate_price(
            facility_id=booking.facility.id,
            entry_time=booking.entry_time,
            exit_time=booking.actual_exit,
            vehicle_type=booking.vehicle.vehicle_type,
            spot_size=booking.spot.size,
            user_id=booking.user.id
        )
        
        booking.final_price = pricing["total"]
        booking.status = BookingStatus.COMPLETED
        booking.save()
        
        # Release spot
        spot = booking.spot
        spot.status = SpotStatus.AVAILABLE
        spot.current_booking = None
        spot.save()
        
        return booking
    
    @staticmethod
    def _generate_ticket_number():
        """Generate unique ticket number"""
        prefix = "PKM"
        random_part = secrets.token_hex(4).upper()
        return f"{prefix}-{random_part}"
