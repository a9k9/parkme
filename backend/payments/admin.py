from django.contrib import admin
from .models import Payment, Refund


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "amount", "currency", "provider", "status", "created_at"]
    list_filter = ["provider", "status", "created_at"]
    search_fields = ["user__email", "provider_transaction_id"]
    readonly_fields = ["id", "created_at", "updated_at", "completed_at"]


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ["id", "payment", "amount", "status", "created_at"]
    list_filter = ["status", "created_at"]
    readonly_fields = ["id", "created_at", "completed_at"]
