"""
Custom User Model with Role-Based Access Control

This implements a production-ready user system with:
- UUID primary keys for security
- Role-based permissions (Admin, Owner, Staff, Driver)
- Phone verification for parking operations
- Audit timestamps
"""

import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserRole(models.TextChoices):
    """
    Enum for user roles - extensible for future roles
    """
    ADMIN = "ADMIN", "Administrator"
    PARKING_OWNER = "PARKING_OWNER", "Parking Owner"
    PARKING_STAFF = "PARKING_STAFF", "Parking Staff"
    DRIVER = "DRIVER", "Driver"


class CustomUserManager(BaseUserManager):
    """
    Manager for custom user model with email as primary identifier
    """

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", UserRole.ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User Model
    
    Design decisions:
    - UUID for public-facing IDs (security best practice)
    - Email as username (modern standard)
    - Role field for RBAC
    - Phone for parking operations (SMS notifications, verification)
    - Soft delete support via is_active
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    phone = models.CharField(max_length=20, blank=True, null=True, db_index=True)
    
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.DRIVER,
        db_index=True
    )
    
    # Verification flags
    is_email_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)
    
    # Django built-in flags
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    # Audit fields
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_at = models.DateTimeField(null=True, blank=True)
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]
    
    class Meta:
        db_table = "users"
        indexes = [
            models.Index(fields=["email", "is_active"]),
            models.Index(fields=["role", "is_active"]),
        ]
        verbose_name = "User"
        verbose_name_plural = "Users"
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        return self.first_name
    
    def is_owner(self):
        return self.role == UserRole.PARKING_OWNER
    
    def is_driver(self):
        return self.role == UserRole.DRIVER
    
    def is_parking_staff(self):
        return self.role == UserRole.PARKING_STAFF


class AuditLog(models.Model):
    """
    Audit logging for security and compliance
    
    Tracks all critical actions:
    - User logins
    - Permission changes
    - Payment transactions
    - Booking modifications
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="audit_logs")
    
    action = models.CharField(max_length=100, db_index=True)
    resource_type = models.CharField(max_length=50, db_index=True)
    resource_id = models.UUIDField(null=True, blank=True)
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    metadata = models.JSONField(default=dict, blank=True)
    
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    
    class Meta:
        db_table = "audit_logs"
        indexes = [
            models.Index(fields=["user", "timestamp"]),
            models.Index(fields=["resource_type", "resource_id"]),
            models.Index(fields=["action", "timestamp"]),
        ]
        ordering = ["-timestamp"]
    
    def __str__(self):
        return f"{self.user} - {self.action} - {self.timestamp}"
