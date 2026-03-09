# ParkMe - Universal Parking Management Platform

## 🏗️ Architecture Overview

This is a **production-ready Django + Django Rest Framework** backend for a universal parking management platform designed to handle thousands of daily vehicle movements across multiple facilities.

### Design Philosophy

- **Clean Architecture**: Separation of concerns with service layers
- **Security First**: UUID-based IDs, JWT authentication, role-based permissions
- **Scalability**: Designed for horizontal scaling with caching and async tasks
- **Extensibility**: Schema-agnostic pricing, flexible vehicle types, multi-provider payments
- **Data Integrity**: Database-level concurrency control prevents double-booking

---

## 📦 Project Structure

```
backend/
├── accounts/          # User management & RBAC
├── vehicles/          # Vehicle registration & types
├── parking/           # Facilities, zones, spots (hierarchical)
├── pricing/           # Flexible pricing engine
├── bookings/          # Reservations & drive-in sessions
├── payments/          # Abstract payment provider
├── enforcement/       # Violations & penalties
├── app/
│   ├── settings/
│   │   ├── base.py   # Shared settings
│   │   ├── dev.py    # Development
│   │   └── prod.py   # Production
│   └── urls.py       # API routing
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

---

## 🎯 Core Features

### 1. **Multi-Role User System**

- **Admin**: Full system access
- **Parking Owner**: Facility management
- **Parking Staff**: Operational access
- **Driver**: Booking & vehicle management

Custom user model with email authentication.

### 2. **Hierarchical Parking Structure**

```
Facility (Mall, Airport, Private Lot)
  ↓
Zone/Floor (Level 1, Section A)
  ↓
Parking Spot (A-101, B-205)
```

Each spot supports:

- Size constraints (small/medium/large/xlarge)
- EV charging capability
- Accessibility features
- Vehicle type compatibility

### 3. **Flexible Pricing Engine**

JSON-based configuration allows pricing evolution **without schema changes**:

**Supported Strategies:**

- Flat rate
- Hourly with tiers
- Slab-based (0-1hr: $5, 1-3hr: $12)
- Dynamic (peak/off-peak)
- Subscriptions/passes

**Example Slab Configuration:**

```json
{
  "slabs": [
    { "max_hours": 1, "price": 5 },
    { "max_hours": 3, "price": 12 },
    { "max_hours": null, "price": 30 }
  ]
}
```

### 4. **Dual Booking Flows**

**Reservation Flow:**

1. User searches available spots
2. Books in advance with estimated price
3. Arrives and activates booking
4. Exits and pays final amount

**Drive-In Flow:**

1. Driver arrives
2. Ticket generated at entry
3. Parks vehicle
4. Pays on exit

### 5. **Concurrency Control (CRITICAL)**

**Problem**: Prevent double-booking in high-traffic scenarios.

**Solution**: Database-level pessimistic locking

```python
@transaction.atomic
def create_reservation(...):
    # Lock the spot row - prevents other transactions
    spot = ParkingSpot.objects.select_for_update(nowait=False).get(id=spot_id)

    # Check availability
    if spot.status != AVAILABLE:
        raise ValidationError("Spot unavailable")

    # Create booking
    booking = Booking.objects.create(...)

    # Update spot
    spot.status = RESERVED
    spot.save()

    # Transaction commits - lock released
```

**Why select_for_update()?**

- Works across multiple app instances
- Simple and reliable for critical operations
- Small performance hit acceptable for data integrity

**Alternatives considered:**

- ❌ Optimistic locking: Requires version fields, retry logic
- ❌ Redis locks: Added complexity
- ✅ Database row locking: Proven, reliable

### 6. **Abstract Payment System**

Supports multiple providers:

- Stripe
- Razorpay
- Cash
- UPI

Design allows adding new gateways without code changes.

### 7. **Performance Optimizations**

**Strategic Indexes:**

```python
class Meta:
    indexes = [
        models.Index(fields=["user", "status"]),
        models.Index(fields=["facility", "status", "entry_time"]),
        models.Index(fields=["plate_number", "is_active"]),
    ]
```

**Query Optimization:**

- `select_related()` for foreign keys
- `prefetch_related()` for reverse relations
- Denormalized counts for facility availability

**Caching Strategy (Redis):**

- Facility availability (TTL: 5 minutes)
- Pricing rules (TTL: 1 hour)
- User subscriptions (TTL: 30 minutes)

Most benefit: **Facility search & availability checks**

### 8. **Security Features**

- ✅ JWT authentication with refresh tokens
- ✅ UUID primary keys (no sequential ID exposure)
- ✅ Role-based permissions
- ✅ Rate limiting (100/hour anon, 1000/hour authenticated)
- ✅ Audit logging for critical actions
- ✅ Input validation via serializers
- ✅ CORS configuration

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL 14+
- Redis 7+ (for caching)

### Installation

```bash
# Clone repository
cd backend

# Install dependencies
pip install -e .

# Setup environment
cp .env.dev.example .env.dev

# Configure database in .env.dev
DATABASE_NAME=parkme_db
DATABASE_USER=postgres
DATABASE_PASSWORD=yourpassword
DATABASE_HOST=localhost
DATABASE_PORT=5432

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

### Docker Setup

```bash
# Build and start services
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser
```

---

## 📡 API Examples

### Authentication

```bash
# Register driver
POST /api/users/
{
  "email": "driver@example.com",
  "password": "SecurePass123!",
  "password_confirm": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890"
}

# Login
POST /api/auth/token/
{
  "email": "driver@example.com",
  "password": "SecurePass123!"
}

# Returns
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Search Available Parking

```bash
# Find facilities with availability
GET /api/facilities/?city=New+York&has_ev_charging=true

# Get facility availability
GET /api/facilities/{facility_id}/availability/

# Search compatible spots
POST /api/facilities/{facility_id}/search_spots/
{
  "vehicle_size": "medium",
  "needs_ev": true,
  "needs_accessible": false
}
```

### Price Estimation

```bash
# Estimate parking cost
POST /api/pricing/estimate/
{
  "facility_id": "550e8400-e29b-41d4-a716-446655440000",
  "duration_hours": 3.5,
  "vehicle_type": "CAR"
}

# Returns
{
  "base_price": "15.00",
  "penalties": "0.00",
  "discounts": "0.00",
  "total": "15.00",
  "duration_minutes": 210,
  "applied_rule": "Hourly Standard Rate",
  "subscription_used": false
}
```

### Create Reservation

```bash
# Book spot in advance
POST /api/bookings/reserve/
Authorization: Bearer {access_token}
{
  "vehicle_id": "550e8400-e29b-41d4-a716-446655440001",
  "spot_id": "550e8400-e29b-41d4-a716-446655440002",
  "entry_time": "2026-02-10T14:00:00Z",
  "expected_exit": "2026-02-10T18:00:00Z"
}

# Returns booking with ticket number
{
  "id": "550e8400-e29b-41d4-a716-446655440003",
  "ticket_number": "PKM-A3F7B2C1",
  "status": "CONFIRMED",
  "estimated_price": "16.00",
  ...
}
```

---

## 🔮 Future Scalability

### License Plate Recognition (LPR)

Automatic entry via camera detection - integration points prepared in `bookings/services.py`

### IoT Occupancy Sensors

Real-time spot status updates via sensor integration

### WebSocket for Real-Time Availability

Push notifications for availability changes using Django Channels

### Multi-City Scaling

Database sharding by geographic region with Django database routing

---

## 🛡️ Production Deployment Checklist

- [ ] Set `DEBUG=False`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Use strong `SECRET_KEY`
- [ ] Enable HTTPS only
- [ ] Configure PostgreSQL connection pooling (pgBouncer)
- [ ] Setup Redis for caching
- [ ] Configure Celery for async tasks
- [ ] Setup monitoring (Sentry, New Relic)
- [ ] Configure backup strategy (daily DB backups)
- [ ] Setup log aggregation (ELK, CloudWatch)
- [ ] Configure CDN for static/media files
- [ ] Setup rate limiting at load balancer level
- [ ] Enable database query logging for slow queries
- [ ] Configure auto-scaling rules

---

## 📚 API Documentation

Full interactive API documentation available at:

- Swagger UI: `http://localhost:8000/api/docs/`
- OpenAPI Schema: `http://localhost:8000/api/schema/`

---

## 👨‍💼 Production Recommendations

### Deployment Architecture

```
┌─────────────┐
│ Load Balancer│ (AWS ALB / nginx)
└──────┬──────┘
       │
   ┌───┴────┐
   │        │
┌──▼──┐  ┌─▼───┐
│App 1│  │App 2│ (Gunicorn/uWSGI)
└──┬──┘  └─┬───┘
   │       │
   └───┬───┘
       │
┌──────▼──────┐
│  PostgreSQL │ (Primary + Replicas)
└─────────────┘
       │
┌──────▼──────┐
│    Redis    │ (Cache + Celery broker)
└─────────────┘
       │
┌──────▼──────┐
│   Celery    │ (Async workers)
└─────────────┘
```

### Performance Targets

- API response time: < 200ms (p95)
- Booking creation: < 500ms
- Database connection pool: 50-100
- Cache hit rate: > 80%

### Monitoring Metrics

- Active bookings count
- Booking creation rate (per minute)
- Payment success rate
- API error rate
- Database query performance
- Cache hit/miss ratio

---

**Built with ❤️ for scale and reliability**
