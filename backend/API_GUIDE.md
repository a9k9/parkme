# API Quick Start Guide

## Base URL

```
http://localhost:8000/api/
```

## Authentication

All authenticated requests must include JWT token:

```
Authorization: Bearer {your_access_token}
```

### 1. Register a New User (Driver)

```bash
POST /api/users/
Content-Type: application/json

{
  "email": "john.doe@example.com",
  "password": "SecurePassword123!",
  "password_confirm": "SecurePassword123!",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890"
}
```

### 2. Login

```bash
POST /api/auth/token/
Content-Type: application/json

{
  "email": "john.doe@example.com",
  "password": "SecurePassword123!"
}

# Response:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### 3. Add a Vehicle

```bash
POST /api/vehicles/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "plate_number": "ABC-1234",
  "vehicle_type": "CAR",
  "make": "Toyota",
  "model": "Camry",
  "year": 2023,
  "color": "Silver"
}
```

### 4. Search for Parking Facilities

```bash
GET /api/facilities/?city=NewYork&has_ev_charging=true
Authorization: Bearer {access_token}

# Response:
{
  "count": 5,
  "results": [
    {
      "id": "550e8400-...",
      "name": "Downtown Mall Parking",
      "city": "New York",
      "total_spots": 500,
      "available_spots": 87,
      "availability": "Medium",
      "has_ev_charging": true
    }
  ]
}
```

### 5. Check Available Spots

```bash
POST /api/facilities/{facility_id}/search_spots/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "vehicle_size": "medium",
  "needs_ev": false,
  "needs_accessible": false
}

# Response:
{
  "count": 12,
  "spots": [
    {
      "id": "650e8400-...",
      "spot_number": "A-101",
      "size": "MEDIUM",
      "has_ev_charger": false,
      "is_accessible": false,
      "status": "AVAILABLE"
    }
  ]
}
```

### 6. Get Price Estimate

```bash
POST /api/pricing/estimate/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "facility_id": "550e8400-e29b-41d4-a716-446655440000",
  "duration_hours": 3.5,
  "vehicle_type": "CAR"
}

# Response:
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

### 7. Create Reservation (Advance Booking)

```bash
POST /api/bookings/reserve/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "vehicle_id": "750e8400-...",
  "spot_id": "650e8400-...",
  "entry_time": "2026-02-10T14:00:00Z",
  "expected_exit": "2026-02-10T18:00:00Z"
}

# Response:
{
  "id": "850e8400-...",
  "ticket_number": "PKM-A3F7B2C1",
  "status": "CONFIRMED",
  "estimated_price": "16.00",
  "entry_time": "2026-02-10T14:00:00Z",
  "expected_exit": "2026-02-10T18:00:00Z",
  "spot_number": "A-101",
  "facility_name": "Downtown Mall Parking"
}
```

### 8. Drive-In Entry (Immediate Parking)

```bash
POST /api/bookings/drive_in/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "vehicle_id": "750e8400-...",
  "spot_id": "650e8400-..."
}

# Response:
{
  "id": "850e8400-...",
  "ticket_number": "PKM-F8D3E1A9",
  "status": "ACTIVE",
  "entry_time": "2026-02-05T10:23:45Z",
  "spot_number": "B-205"
}
```

### 9. Complete Booking (Exit)

```bash
POST /api/bookings/{booking_id}/complete/
Authorization: Bearer {access_token}

# Response:
{
  "id": "850e8400-...",
  "ticket_number": "PKM-F8D3E1A9",
  "status": "COMPLETED",
  "entry_time": "2026-02-05T10:23:45Z",
  "actual_exit": "2026-02-05T14:10:22Z",
  "duration": 227,
  "final_price": "14.50",
  "is_overstay": false
}
```

### 10. View My Bookings

```bash
GET /api/bookings/?status=ACTIVE
Authorization: Bearer {access_token}

# Response:
{
  "count": 1,
  "results": [
    {
      "id": "850e8400-...",
      "ticket_number": "PKM-F8D3E1A9",
      "status": "ACTIVE",
      "facility_name": "Downtown Mall Parking",
      "spot_number": "B-205",
      "entry_time": "2026-02-05T10:23:45Z"
    }
  ]
}
```

## Common Query Parameters

### Pagination

```
?page=2&page_size=20
```

### Filtering

```
?status=ACTIVE&facility={facility_id}
```

### Search

```
?search=Downtown
```

### Ordering

```
?ordering=-created_at
```

## Error Responses

```json
{
  "error": "Spot is OCCUPIED, cannot book"
}
```

```json
{
  "detail": "Authentication credentials were not provided."
}
```

```json
{
  "email": ["This field is required."],
  "password": ["Passwords do not match"]
}
```

## Rate Limits

- **Anonymous**: 100 requests/hour
- **Authenticated**: 1000 requests/hour

## Interactive Documentation

Visit these URLs for full API exploration:

- **Swagger UI**: http://localhost:8000/api/docs/
- **API Schema**: http://localhost:8000/api/schema/
