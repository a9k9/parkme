# Production Deployment Guide

## Infrastructure Requirements

### Minimum Production Setup

**Application Servers:**

- 2+ instances (AWS EC2 t3.medium or equivalent)
- 2 vCPUs, 4GB RAM each
- Auto-scaling group for traffic spikes

**Database:**

- PostgreSQL 15+ (RDS or managed)
- Primary + 1 read replica minimum
- db.t3.large (2 vCPUs, 8GB RAM)
- 100GB SSD storage (expandable)

**Cache Layer:**

- Redis 7+ (ElastiCache or managed)
- cache.t3.medium (2 vCPUs, 3.09GB RAM)
- Cluster mode enabled for HA

**Task Queue:**

- Celery workers (2+ instances)
- Same specs as app servers
- Separate auto-scaling group

**Load Balancer:**

- AWS ALB or nginx
- SSL termination
- Health checks on /admin/login/

---

## Environment Variables (Production)

Create `.env.prod`:

```bash
# Django
SECRET_KEY={use-strong-random-key-50-chars}
DEBUG=False
DJANGO_ALLOWED_HOSTS=api.parkme.com,parkme.com

# Database
DATABASE_NAME=parkme_production
DATABASE_USER=parkme_user
DATABASE_PASSWORD={strong-password}
DATABASE_HOST=parkme-db.rds.amazonaws.com
DATABASE_PORT=5432

# Redis
REDIS_URL=redis://parkme-cache.cache.amazonaws.com:6379/1

# Celery
CELERY_BROKER_URL=redis://parkme-cache.cache.amazonaws.com:6379/0
CELERY_RESULT_BACKEND=redis://parkme-cache.cache.amazonaws.com:6379/0

# AWS S3 (for media files)
AWS_ACCESS_KEY_ID={your-key}
AWS_SECRET_ACCESS_KEY={your-secret}
AWS_STORAGE_BUCKET_NAME=parkme-media
AWS_S3_REGION_NAME=us-east-1

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD={sendgrid-api-key}
DEFAULT_FROM_EMAIL=noreply@parkme.com

# Monitoring
SENTRY_DSN={your-sentry-dsn}

# Security
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
```

---

## Deployment Steps

### 1. Database Setup

```bash
# Create production database
CREATE DATABASE parkme_production;
CREATE USER parkme_user WITH PASSWORD 'strong-password';
GRANT ALL PRIVILEGES ON DATABASE parkme_production TO parkme_user;

# Run migrations
python manage.py migrate --settings=app.settings.prod

# Create superuser
python manage.py createsuperuser --settings=app.settings.prod
```

### 2. Static Files

```bash
# Collect static files to S3 or CDN
python manage.py collectstatic --noinput --settings=app.settings.prod
```

### 3. Application Deployment (Using Gunicorn)

```bash
# Install gunicorn
pip install gunicorn

# Run with production settings
gunicorn app.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --threads 2 \
  --timeout 60 \
  --access-logfile - \
  --error-logfile - \
  --log-level info \
  --env DJANGO_SETTINGS_MODULE=app.settings.prod
```

### 4. Celery Workers

```bash
# Start Celery worker
celery -A app worker \
  --loglevel=info \
  --concurrency=4 \
  --max-tasks-per-child=1000

# Start Celery beat (scheduler)
celery -A app beat \
  --loglevel=info \
  --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### 5. Nginx Configuration (Reverse Proxy)

```nginx
upstream parkme_backend {
    least_conn;
    server app1.internal:8000;
    server app2.internal:8000;
}

server {
    listen 80;
    server_name api.parkme.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.parkme.com;

    ssl_certificate /etc/ssl/certs/parkme.crt;
    ssl_certificate_key /etc/ssl/private/parkme.key;
    ssl_protocols TLSv1.2 TLSv1.3;

    client_max_body_size 10M;

    location /static/ {
        alias /var/www/parkme/static/;
        expires 30d;
    }

    location /media/ {
        alias /var/www/parkme/media/;
        expires 30d;
    }

    location / {
        proxy_pass http://parkme_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint
    location /health/ {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

---

## Monitoring & Logging

### 1. Application Monitoring (Sentry)

Add to `settings/prod.py`:

```python
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn=os.getenv('SENTRY_DSN'),
    integrations=[DjangoIntegration()],
    traces_sample_rate=0.1,
    send_default_pii=False
)
```

### 2. Database Monitoring

```sql
-- Slow query logging
ALTER SYSTEM SET log_min_duration_statement = 1000;  -- Log queries > 1s

-- Connection pooling (pgBouncer)
[databases]
parkme_production = host=localhost dbname=parkme_production

[pgbouncer]
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
```

### 3. Redis Monitoring

```bash
# Monitor Redis performance
redis-cli --stat

# Check memory usage
redis-cli INFO memory
```

### 4. Application Logs

```python
# CloudWatch logging (AWS)
LOGGING = {
    'handlers': {
        'watchtower': {
            'class': 'watchtower.CloudWatchLogHandler',
            'log_group': 'parkme-production',
            'stream_name': 'django-{instance_id}',
        },
    },
}
```

---

## Database Optimization

### Indexes for Production

```sql
-- High-traffic query indexes
CREATE INDEX CONCURRENTLY idx_bookings_active_status
ON bookings (facility_id, status, entry_time)
WHERE status IN ('ACTIVE', 'CONFIRMED');

CREATE INDEX CONCURRENTLY idx_spots_available
ON parking_spots (zone_id, status, is_active)
WHERE status = 'AVAILABLE' AND is_active = true;

CREATE INDEX CONCURRENTLY idx_vehicles_plate_lookup
ON vehicles (plate_number, is_active)
WHERE is_active = true;

-- Partial index for recent bookings
CREATE INDEX CONCURRENTLY idx_bookings_recent
ON bookings (created_at DESC)
WHERE created_at > NOW() - INTERVAL '30 days';
```

### Connection Pooling

```python
# settings/prod.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DATABASE_NAME'),
        'USER': os.getenv('DATABASE_USER'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD'),
        'HOST': os.getenv('DATABASE_HOST'),
        'PORT': os.getenv('DATABASE_PORT'),
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000'  # 30s query timeout
        },
        'CONN_MAX_AGE': 600,  # Connection pooling
    }
}
```

---

## Backup Strategy

### 1. Database Backups

```bash
# Automated daily backups
0 2 * * * pg_dump -h $DATABASE_HOST -U $DATABASE_USER $DATABASE_NAME | \
  gzip > /backups/parkme_$(date +\%Y\%m\%d).sql.gz

# Retention: 30 days local, 90 days S3
aws s3 sync /backups/ s3://parkme-backups/database/ \
  --storage-class STANDARD_IA
```

### 2. Redis Persistence

```bash
# Enable RDB snapshots
save 900 1
save 300 10
save 60 10000

# AOF for durability
appendonly yes
appendfsync everysec
```

---

## Scaling Strategies

### Horizontal Scaling (App Servers)

```bash
# Auto-scaling based on metrics
- CPU > 70% for 5 minutes → Scale up
- CPU < 30% for 10 minutes → Scale down
- Min instances: 2
- Max instances: 10
```

### Database Scaling

```
Primary (Write) → Read Replica 1 (Read)
                → Read Replica 2 (Read)

# Django database routing
class ReadReplicaRouter:
    def db_for_read(self, model, **hints):
        return random.choice(['default', 'replica1', 'replica2'])

    def db_for_write(self, model, **hints):
        return 'default'
```

### Caching Strategy

```python
# View-level caching
from django.views.decorators.cache import cache_page

@cache_page(60 * 5)  # 5 minutes
def facility_list(request):
    ...

# Query-level caching
from django.core.cache import cache

def get_available_spots(facility_id):
    cache_key = f'spots:{facility_id}:available'
    spots = cache.get(cache_key)

    if spots is None:
        spots = ParkingSpot.objects.filter(
            zone__facility_id=facility_id,
            status='AVAILABLE'
        )
        cache.set(cache_key, spots, 300)  # 5 minutes

    return spots
```

---

## Security Hardening

### 1. Django Security Settings

```python
# settings/prod.py

# HTTPS
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# HSTS
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Content Security
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
```

### 2. Database Security

```sql
-- Restrict database access
REVOKE ALL ON DATABASE parkme_production FROM PUBLIC;
GRANT CONNECT ON DATABASE parkme_production TO parkme_user;

-- Row-level security (if needed)
ALTER TABLE bookings ENABLE ROW LEVEL SECURITY;
```

### 3. API Rate Limiting

```python
# settings/prod.py
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'booking': '100/hour',  # Critical endpoints
    }
}
```

---

## Health Checks

```python
# Create health check view
from django.http import JsonResponse
from django.db import connection

def health_check(request):
    try:
        # Check database
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")

        # Check Redis
        cache.set('health_check', 'ok', 10)
        cache.get('health_check')

        return JsonResponse({'status': 'healthy'})
    except Exception as e:
        return JsonResponse({'status': 'unhealthy', 'error': str(e)}, status=500)
```

---

## Zero-Downtime Deployment

```bash
# Blue-Green deployment strategy

# 1. Deploy to "green" environment
# 2. Run migrations (if backward compatible)
# 3. Health check on green
# 4. Switch load balancer to green
# 5. Monitor for 10 minutes
# 6. Decommission blue (keep as backup)

# Rolling deployment (alternative)
# 1. Take 1 instance out of load balancer
# 2. Deploy new code
# 3. Health check
# 4. Add back to load balancer
# 5. Repeat for other instances
```

---

## Cost Optimization

**Estimated Monthly Cost (AWS):**

- EC2 (4x t3.medium): $120
- RDS (db.t3.large): $130
- ElastiCache (cache.t3.medium): $50
- ALB: $20
- S3 Storage (100GB): $2
- Data Transfer: $50
- **Total: ~$372/month** (before traffic scaling)

**Optimization Tips:**

- Use Reserved Instances (40% savings)
- Implement CDN for static files
- Compress images and media
- Use S3 lifecycle policies for old backups
- Monitor and right-size instances

---

## Support & Maintenance

### Regular Tasks

- [ ] Daily: Check error logs and Sentry alerts
- [ ] Weekly: Review slow query logs, optimize indexes
- [ ] Monthly: Database vacuum and analyze
- [ ] Monthly: Review and update dependencies
- [ ] Quarterly: Load testing and capacity planning
- [ ] Quarterly: Security audit and penetration testing

### Incident Response

1. Acknowledge alert within 15 minutes
2. Assess severity and impact
3. Implement temporary fix if needed
4. Root cause analysis
5. Permanent fix deployment
6. Post-mortem documentation

---

**Production deployment is complete when all checklist items are verified and monitoring shows green status.**
