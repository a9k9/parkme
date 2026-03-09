"""
Role-Based Permission Classes

Implements fine-grained access control:
- IsAdmin: Full system access
- IsOwner: Can manage their own facilities
- IsStaff: Operational access to assigned facilities
- IsDriver: Can book and manage their vehicles
"""

from rest_framework import permissions
from .models import UserRole


class IsAdmin(permissions.BasePermission):
    """
    Admin-only access
    """
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == UserRole.ADMIN
        )


class IsOwner(permissions.BasePermission):
    """
    Parking owner access
    """
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == UserRole.PARKING_OWNER
        )


class IsStaff(permissions.BasePermission):
    """
    Parking staff access
    """
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == UserRole.PARKING_STAFF
        )


class IsDriver(permissions.BasePermission):
    """
    Driver access
    """
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == UserRole.DRIVER
        )


class IsOwnerOrStaff(permissions.BasePermission):
    """
    Combined owner/staff permission for operational endpoints
    """
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role
            in [
                UserRole.ADMIN,
                UserRole.PARKING_OWNER,
                UserRole.PARKING_STAFF,
            ]
        )


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Allow anyone to view, but only owners can modify
    Safe methods: GET, HEAD, OPTIONS
    """
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == UserRole.PARKING_OWNER
        )


class IsObjectOwner(permissions.BasePermission):
    """
    Generic permission: user can only access their own objects
    
    Expects object to have a 'user' or 'owner' field
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin can access everything
        if request.user.role == UserRole.ADMIN:
            return True
        
        # Check if object has user field
        if hasattr(obj, "user"):
            return obj.user == request.user
        
        # Check if object has owner field
        if hasattr(obj, "owner"):
            return obj.owner == request.user
        
        return False
