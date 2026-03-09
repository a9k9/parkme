"""
Business Logic Layer for Accounts

Separates business logic from views - cleaner architecture
"""

from django.contrib.auth import get_user_model
from django.db import transaction
from .models import AuditLog

User = get_user_model()


class UserService:
    """
    Service layer for user operations
    """
    
    @staticmethod
    def create_audit_log(user, action, resource_type, resource_id=None, 
                        ip_address=None, user_agent=None, metadata=None):
        """
        Create audit log entry
        
        Used for tracking critical operations for security and compliance
        """
        return AuditLog.objects.create(
            user=user,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {}
        )
    
    @staticmethod
    @transaction.atomic
    def register_driver(email, password, first_name, last_name, phone=None):
        """
        Register a new driver
        
        Transaction ensures atomicity - if any step fails, roll back
        """
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role="DRIVER"
        )
        
        # Create audit log
        AuditLog.objects.create(
            user=user,
            action="USER_REGISTERED",
            resource_type="USER",
            resource_id=user.id,
            metadata={"role": "DRIVER"}
        )
        
        return user
    
    @staticmethod
    def get_user_statistics(user):
        """
        Get user activity statistics
        
        Can be extended to include:
        - Total bookings
        - Total spend
        - Favorite locations
        """
        return {
            "total_logins": user.audit_logs.filter(action="USER_LOGIN").count(),
            "account_age_days": (timezone.now() - user.created_at).days,
            "email_verified": user.is_email_verified,
            "phone_verified": user.is_phone_verified,
        }


from django.utils import timezone
