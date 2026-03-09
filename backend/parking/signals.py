"""
Signals for maintaining denormalized counts

Updates total_spots and available_spots on Facility and Zone
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import ParkingSpot, Zone, SpotStatus


@receiver([post_save, post_delete], sender=ParkingSpot)
def update_zone_spot_counts(sender, instance, **kwargs):
    """Update zone spot counts when spots change"""
    zone = instance.zone
    
    total = zone.spots.filter(is_active=True).count()
    available = zone.spots.filter(status=SpotStatus.AVAILABLE, is_active=True).count()
    
    Zone.objects.filter(id=zone.id).update(
        total_spots=total,
        available_spots=available
    )
    
    # Also update facility counts
    facility = zone.facility
    facility_total = ParkingSpot.objects.filter(
        zone__facility=facility,
        is_active=True
    ).count()
    
    facility_available = ParkingSpot.objects.filter(
        zone__facility=facility,
        status=SpotStatus.AVAILABLE,
        is_active=True
    ).count()
    
    from parking.models import Facility
    Facility.objects.filter(id=facility.id).update(
        total_spots=facility_total,
        available_spots=facility_available
    )
