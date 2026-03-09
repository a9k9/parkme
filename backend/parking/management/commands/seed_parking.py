import random
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from accounts.models import User, UserRole
from parking.models import Facility, FacilityType, ParkingSpot, SpotSize, Zone


CITY_SETS = [
    ("San Francisco", "CA", "94103"),
    ("Austin", "TX", "78701"),
    ("Seattle", "WA", "98101"),
    ("Chicago", "IL", "60601"),
    ("Miami", "FL", "33101"),
    ("Denver", "CO", "80202"),
    ("Boston", "MA", "02108"),
    ("Phoenix", "AZ", "85001"),
    ("Portland", "OR", "97201"),
    ("Atlanta", "GA", "30301"),
]


class Command(BaseCommand):
    help = "Seed facilities, zones, and parking spots."

    def add_arguments(self, parser):
        parser.add_argument("--facilities", type=int, default=10)
        parser.add_argument("--zones-per-facility", type=int, default=5)
        parser.add_argument("--spots-per-zone", type=int, default=30)
        parser.add_argument("--owner-email", type=str, default="owner@parkme.com")
        parser.add_argument("--reset", action="store_true")

    def handle(self, *args, **options):
        facility_count = options["facilities"]
        zones_per_facility = options["zones_per_facility"]
        spots_per_zone = options["spots_per_zone"]
        owner_email = options["owner_email"]
        reset = options["reset"]

        if reset:
            self.stdout.write("Resetting parking data...")
            ParkingSpot.objects.all().delete()
            Zone.objects.all().delete()
            Facility.objects.all().delete()

        owner = User.objects.filter(email=owner_email).first()
        if not owner:
            owner = User.objects.create_user(
                email=owner_email,
                password="owner123",
                first_name="Seed",
                last_name="Owner",
                role=UserRole.PARKING_OWNER,
                is_email_verified=True,
            )

        created_facilities = 0

        with transaction.atomic():
            for index in range(facility_count):
                city, state, postal_code = CITY_SETS[index % len(CITY_SETS)]
                name = f"Facility {index + 1}"
                base_slug = slugify(name)
                slug = base_slug
                suffix = 1
                while Facility.objects.filter(slug=slug).exists():
                    suffix += 1
                    slug = f"{base_slug}-{suffix}"

                facility = Facility.objects.create(
                    owner=owner,
                    name=name,
                    slug=slug,
                    facility_type=random.choice(FacilityType.values),
                    description=f"Seeded facility in {city}.",
                    address=f"{100 + index} Main St",
                    city=city,
                    state=state,
                    postal_code=postal_code,
                    country="USA",
                    latitude=Decimal("37.77") + Decimal(str(index * 0.01)),
                    longitude=Decimal("-122.41") - Decimal(str(index * 0.01)),
                    phone="555-0100",
                    email=f"facility{index + 1}@parkme.com",
                    has_ev_charging=bool(index % 2),
                    has_covered_parking=bool(index % 3),
                    has_security=True,
                    has_cctv=bool(index % 2),
                    has_valet=bool(index % 4 == 0),
                    is_active=True,
                    is_verified=True,
                )

                created_facilities += 1

                zones = []
                for zone_index in range(zones_per_facility):
                    zones.append(
                        Zone(
                            facility=facility,
                            name=f"Zone {zone_index + 1}",
                            code=f"Z{zone_index + 1}",
                            description=f"Seeded zone {zone_index + 1}.",
                            display_order=zone_index + 1,
                            is_active=True,
                            is_accessible=True,
                            is_covered=bool(zone_index % 2),
                        )
                    )

                Zone.objects.bulk_create(zones)

                for zone in Zone.objects.filter(facility=facility):
                    for spot_index in range(spots_per_zone):
                        ParkingSpot.objects.create(
                            zone=zone,
                            spot_number=f"{zone.code}-{spot_index + 1:03d}",
                            size=random.choice(SpotSize.values),
                            has_ev_charger=bool(spot_index % 7 == 0),
                            is_accessible=bool(spot_index % 10 == 0),
                            is_covered=zone.is_covered,
                            is_vip=bool(spot_index % 15 == 0),
                            is_active=True,
                        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {created_facilities} facilities with {zones_per_facility} zones "
                f"and {spots_per_zone} spots each."
            )
        )
