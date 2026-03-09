from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, AuditLog


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["email", "first_name", "last_name", "role", "is_active", "created_at"]
    list_filter = ["role", "is_active", "is_email_verified", "is_phone_verified"]
    search_fields = ["email", "first_name", "last_name", "phone"]
    ordering = ["-created_at"]
    
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("first_name", "last_name", "phone")}),
        ("Permissions", {"fields": ("role", "is_active", "is_staff", "is_superuser")}),
        ("Verification", {"fields": ("is_email_verified", "is_phone_verified")}),
        ("Timestamps", {"fields": ("created_at", "updated_at", "last_login_at")}),
    )
    
    readonly_fields = ["created_at", "updated_at", "last_login_at"]
    
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2", "first_name", "last_name", "role"),
        }),
    )


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["user", "action", "resource_type", "resource_id", "timestamp"]
    list_filter = ["action", "resource_type", "timestamp"]
    search_fields = ["user__email", "action", "resource_type"]
    readonly_fields = ["user", "action", "resource_type", "resource_id", 
                      "ip_address", "user_agent", "metadata", "timestamp"]
    ordering = ["-timestamp"]
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
