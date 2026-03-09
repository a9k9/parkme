"""
ViewSets for User Management

Implements REST endpoints with proper permissions and throttling
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model

from .models import AuditLog
from .serializers import (
    UserRegistrationSerializer,
    UserSerializer,
    UserDetailSerializer,
    AuditLogSerializer
)
from .permissions import IsAdmin, IsObjectOwner
from .services import UserService

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """
    User management endpoints
    
    - Public: Registration
    - Authenticated: Profile view/update
    - Admin: Full user management
    """
    queryset = User.objects.filter(is_active=True)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["role", "is_email_verified"]
    search_fields = ["email", "first_name", "last_name", "phone"]
    ordering_fields = ["created_at", "email"]
    
    def get_serializer_class(self):
        if self.action == "create":
            return UserRegistrationSerializer
        elif self.action == "retrieve" or self.action == "me":
            return UserDetailSerializer
        return UserSerializer
    
    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]
        elif self.action in ["update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsObjectOwner()]
        elif self.action in ["list"]:
            return [IsAuthenticated(), IsAdmin()]
        return [IsAuthenticated()]
    
    @action(detail=False, methods=["get"])
    def me(self, request):
        """
        Get current user profile
        
        GET /api/users/me/
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=["get"])
    def stats(self, request):
        """
        Get user statistics
        
        GET /api/users/stats/
        """
        stats = UserService.get_user_statistics(request.user)
        return Response(stats)
    
    def perform_create(self, serializer):
        """
        Custom user registration with audit logging
        """
        user = serializer.save()
        
        # Create audit log
        UserService.create_audit_log(
            user=user,
            action="USER_REGISTERED",
            resource_type="USER",
            resource_id=user.id,
            ip_address=self.request.META.get("REMOTE_ADDR"),
            user_agent=self.request.META.get("HTTP_USER_AGENT", ""),
        )


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Audit log viewing - admin only
    
    Critical for compliance and security investigations
    """
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["user", "action", "resource_type"]
    ordering_fields = ["timestamp"]
    ordering = ["-timestamp"]
