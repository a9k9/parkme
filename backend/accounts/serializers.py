"""
Serializers for User Management

Separates public and private data exposure
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import AuditLog

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    User registration - driver signup
    """
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            "email", "password", "password_confirm",
            "first_name", "last_name", "phone"
        ]
    
    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password": "Passwords do not match"})
        attrs.pop("password_confirm")
        return attrs
    
    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    """
    Public user profile - safe for external exposure
    """
    full_name = serializers.CharField(source="get_full_name", read_only=True)
    
    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name", "full_name",
            "phone", "role", "is_email_verified", "is_phone_verified",
            "created_at"
        ]
        read_only_fields = ["id", "role", "created_at"]


class UserDetailSerializer(serializers.ModelSerializer):
    """
    Detailed user profile - for authenticated user accessing their own data
    """
    full_name = serializers.CharField(source="get_full_name", read_only=True)
    
    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name", "full_name",
            "phone", "role", "is_email_verified", "is_phone_verified",
            "is_active", "created_at", "updated_at", "last_login_at"
        ]
        read_only_fields = ["id", "role", "created_at", "updated_at", "last_login_at"]


class AuditLogSerializer(serializers.ModelSerializer):
    """
    Audit log entries - admin only
    """
    user_email = serializers.EmailField(source="user.email", read_only=True)
    
    class Meta:
        model = AuditLog
        fields = [
            "id", "user", "user_email", "action", "resource_type",
            "resource_id", "ip_address", "metadata", "timestamp"
        ]
        read_only_fields = ["id", "timestamp"]
