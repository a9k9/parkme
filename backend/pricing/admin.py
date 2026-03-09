from django.contrib import admin
from .models import PricingRule, Subscription, UserSubscription


@admin.register(PricingRule)
class PricingRuleAdmin(admin.ModelAdmin):
    list_display = ["name", "facility", "strategy", "priority", "is_active"]
    list_filter = ["strategy", "is_active", "facility"]
    search_fields = ["name", "facility__name"]
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering = ["-priority", "name"]


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ["name", "facility", "price", "duration_days", "entry_count", "is_active"]
    list_filter = ["is_active", "facility"]
    search_fields = ["name", "facility__name"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ["user", "subscription", "activated_at", "expires_at", "is_active"]
    list_filter = ["is_active", "subscription__facility"]
    search_fields = ["user__email", "subscription__name"]
    readonly_fields = ["id", "activated_at"]
