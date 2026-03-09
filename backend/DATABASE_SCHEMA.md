# Database Schema Overview

## Entity Relationship Diagram

```
┌─────────────────┐
│     USERS       │
│   (accounts)    │
├─────────────────┤
│ id (UUID) PK    │
│ email           │
│ role (enum)     │
│ phone           │
│ is_verified     │
└────────┬────────┘
         │
         │ owns
         ├────────────────────────────────┐
         │                                │
         │ drives                          │ reports
         ├───────────────┐                │
         │               │                │
┌────────▼────────┐ ┌───▼──────────┐ ┌──▼─────────────┐
│    VEHICLES     │ │   FACILITIES  │ │  AUDIT_LOGS    │
├─────────────────┤ ├───────────────┤ ├────────────────┤
│ id (UUID) PK    │ │ id (UUID) PK  │ │ id (UUID) PK   │
│ user_id FK      │ │ owner_id FK   │ │ user_id FK     │
│ plate_number*   │ │ name          │ │ action         │
│ vehicle_type    │ │ city*         │ │ resource_type  │
│ is_verified     │ │ latitude      │ │ timestamp*     │
└─────────────────┘ │ longitude     │ └────────────────┘
                    │ total_spots   │
                    │ available_spots│
                    └───────┬────────┘
                            │
                            │ contains
                    ┌───────▼────────┐
                    │     ZONES      │
                    ├────────────────┤
                    │ id (UUID) PK   │
                    │ facility_id FK │
                    │ name           │
                    │ code           │
                    │ total_spots    │
                    │ available_spots│
                    └───────┬────────┘
                            │
                            │ contains
                    ┌───────▼────────┐
                    │ PARKING_SPOTS  │
                    ├────────────────┤
                    │ id (UUID) PK   │
                    │ zone_id FK     │
                    │ spot_number    │
                    │ size (enum)    │
                    │ status* (enum) │
                    │ has_ev_charger │
                    │ is_accessible  │
                    │ current_booking│
                    └───────┬────────┘
                            │
                            │ reserved_by
         ┌──────────────────┴──────────────────┐
         │                                     │
┌────────▼────────┐                   ┌───────▼────────┐
│    BOOKINGS     │                   │ PRICING_RULES  │
├─────────────────┤                   ├────────────────┤
│ id (UUID) PK    │                   │ id (UUID) PK   │
│ user_id FK      │                   │ facility_id FK │
│ vehicle_id FK   │                   │ strategy (enum)│
│ spot_id FK      │◄──────────────────│ config (JSON)  │
│ facility_id FK  │   applies_to      │ priority       │
│ ticket_number*  │                   │ free_minutes   │
│ booking_type    │                   └────────────────┘
│ status* (enum)  │
│ entry_time*     │
│ expected_exit   │
│ actual_exit     │
│ estimated_price │
│ final_price     │
│ payment_id FK   │
└────────┬────────┘
         │
         │ pays_with
┌────────▼────────┐
│    PAYMENTS     │
├─────────────────┤
│ id (UUID) PK    │
│ user_id FK      │
│ amount          │
│ provider (enum) │
│ status* (enum)  │
│ provider_txn_id*│
└─────────────────┘

┌──────────────────┐
│  SUBSCRIPTIONS   │
├──────────────────┤
│ id (UUID) PK     │
│ facility_id FK   │
│ name             │
│ price            │
│ duration_days    │
│ entry_count      │
└────────┬─────────┘
         │
         │ purchased_by
┌────────▼──────────┐
│USER_SUBSCRIPTIONS │
├───────────────────┤
│ id (UUID) PK      │
│ user_id FK        │
│ subscription_id FK│
│ activated_at      │
│ expires_at        │
│ entries_remaining │
└───────────────────┘

┌──────────────────┐
│   VIOLATIONS     │
├──────────────────┤
│ id (UUID) PK     │
│ user_id FK       │
│ vehicle_id FK    │
│ facility_id FK   │
│ booking_id FK    │
│ violation_type   │
│ penalty_amount   │
│ status (enum)    │
│ violation_time   │
└──────────────────┘

┌──────────────────┐
│ FACILITY_STAFF   │
├──────────────────┤
│ id (UUID) PK     │
│ facility_id FK   │
│ staff_member FK  │
│ permissions      │
└──────────────────┘

* = Indexed field
```

## Key Relationships

### One-to-Many

- User → Vehicles (1:N)
- User → Bookings (1:N)
- User → Payments (1:N)
- Facility → Zones (1:N)
- Zone → ParkingSpots (1:N)
- Facility → PricingRules (1:N)
- Facility → Bookings (1:N)

### Many-to-Many

- Facility ↔ Staff (through FacilityStaff)
- User ↔ Subscriptions (through UserSubscriptions)

### Special Relationships

- ParkingSpot.current_booking (denormalized for performance)
- Booking.payment (optional, set after payment)

---

## Critical Indexes

### High-Traffic Queries

```sql
-- Booking lookups by facility and status
CREATE INDEX idx_bookings_facility_status
ON bookings (facility_id, status, entry_time);

-- Active bookings for users
CREATE INDEX idx_bookings_user_status
ON bookings (user_id, status);

-- Spot availability checks
CREATE INDEX idx_spots_status_size
ON parking_spots (status, size, is_active)
WHERE is_active = true;

-- Vehicle plate lookups (entry/exit)
CREATE INDEX idx_vehicles_plate
ON vehicles (plate_number, is_active)
WHERE is_active = true;

-- Facility search by city
CREATE INDEX idx_facilities_city
ON facilities (city, is_active)
WHERE is_active = true;

-- Recent audit logs
CREATE INDEX idx_audit_logs_recent
ON audit_logs (timestamp DESC);
```

### Concurrency-Critical Indexes

```sql
-- For select_for_update() locks
CREATE INDEX idx_spots_locking
ON parking_spots (id, status, is_active)
WHERE is_active = true;

-- For booking conflict checks
CREATE INDEX idx_bookings_overlap
ON bookings (spot_id, status, entry_time, expected_exit)
WHERE status IN ('CONFIRMED', 'ACTIVE');
```

---

## Table Statistics (Expected Production Scale)

| Table         | Expected Rows | Growth Rate   | Retention |
| ------------- | ------------- | ------------- | --------- |
| users         | 100,000+      | 1,000/month   | Permanent |
| vehicles      | 150,000+      | 1,500/month   | Permanent |
| facilities    | 500+          | 10/month      | Permanent |
| zones         | 5,000+        | 50/month      | Permanent |
| parking_spots | 250,000+      | 2,500/month   | Permanent |
| bookings      | 10M+          | 300,000/month | 2 years   |
| payments      | 10M+          | 300,000/month | 7 years   |
| pricing_rules | 5,000+        | 50/month      | Permanent |
| violations    | 100,000+      | 5,000/month   | 5 years   |
| audit_logs    | 50M+          | 1.5M/month    | 1 year    |

---

## Database Sizing Estimates

### Storage Requirements (1 Year)

- Bookings: ~3.6M records × 1KB = 3.6GB
- Payments: ~3.6M records × 0.5KB = 1.8GB
- Audit Logs: ~18M records × 0.5KB = 9GB
- Other tables: ~2GB
- **Total: ~16GB** (+ indexes ~24GB total)

### IOPS Requirements

- Read: 5,000 IOPS (peak)
- Write: 1,000 IOPS (peak)
- Recommend: PostgreSQL on SSD (provisioned IOPS)

---

## Data Archival Strategy

### Archive After

- Bookings: Completed > 2 years → Archive table
- Payments: > 7 years → Cold storage (compliance)
- Audit Logs: > 1 year → S3/Glacier
- Violations: Resolved > 5 years → Archive

### Partitioning Strategy

```sql
-- Partition bookings by month (PostgreSQL 12+)
CREATE TABLE bookings (
    ...
) PARTITION BY RANGE (entry_time);

CREATE TABLE bookings_2026_02 PARTITION OF bookings
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');

-- Auto-create partitions via cron/Celery
```

---

## Backup & Recovery

### Backup Schedule

- **Full backup**: Daily at 2 AM (pg_dump)
- **Incremental**: Every 6 hours (WAL archiving)
- **Retention**: 30 days local, 90 days S3

### Recovery Time Objectives

- **RTO**: < 1 hour (full restore)
- **RPO**: < 15 minutes (WAL replay)

### Point-in-Time Recovery

```bash
# Restore to specific timestamp
pg_restore -d parkme_db -t "2026-02-05 14:30:00" backup.dump
```

---

## Query Performance Baselines

### Target Query Times

- Spot availability search: < 50ms
- Create booking: < 200ms (with lock)
- Price calculation: < 100ms
- User login: < 150ms
- Facility list: < 100ms (cached)

### Slow Query Monitoring

```sql
-- Enable slow query logging
ALTER SYSTEM SET log_min_duration_statement = 1000;  -- 1 second

-- Find slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
WHERE mean_exec_time > 1000
ORDER BY mean_exec_time DESC
LIMIT 20;
```

---

## Connection Pooling (pgBouncer)

```ini
[databases]
parkme_production = host=localhost dbname=parkme_production

[pgbouncer]
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
reserve_pool_size = 5
reserve_pool_timeout = 3
```

---

This schema is designed for:
✅ High concurrency
✅ Fast lookups
✅ Data integrity
✅ Scalability
✅ Performance
✅ Compliance (audit logs, payment retention)
