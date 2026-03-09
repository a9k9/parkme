"""
Abstract Payment Provider System

Supports multiple payment gateways:
- Stripe
- Razorpay
- Cash
- UPI
- Future gateways (extensible)
"""

import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


class PaymentProvider(models.TextChoices):
    """Supported payment providers"""
    STRIPE = "STRIPE", "Stripe"
    RAZORPAY = "RAZORPAY", "Razorpay"
    CASH = "CASH", "Cash"
    UPI = "UPI", "UPI"
    WALLET = "WALLET", "Digital Wallet"


class PaymentStatus(models.TextChoices):
    """Payment lifecycle states"""
    PENDING = "PENDING", "Pending"
    PROCESSING = "PROCESSING", "Processing"
    COMPLETED = "COMPLETED", "Completed"
    FAILED = "FAILED", "Failed"
    REFUNDED = "REFUNDED", "Refunded"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED", "Partially Refunded"


class Payment(models.Model):
    """
    Payment transactions
    
    Abstract design allows any payment provider integration
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="payments"
    )
    
    # Amount
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    
    # Provider details
    provider = models.CharField(
        max_length=20,
        choices=PaymentProvider.choices,
        default=PaymentProvider.STRIPE
    )
    provider_transaction_id = models.CharField(
        max_length=200,
        blank=True,
        db_index=True
    )
    
    # Status
    status = models.CharField(
        max_length=30,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        db_index=True
    )
    
    # Provider response (for debugging/reconciliation)
    provider_response = models.JSONField(default=dict, blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    # Audit
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = "payments"
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["provider", "status"]),
            models.Index(fields=["created_at"]),
        ]
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"{self.user.email} - {self.amount} {self.currency} - {self.status}"


class Refund(models.Model):
    """
    Refund transactions
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.ForeignKey(
        Payment,
        on_delete=models.PROTECT,
        related_name="refunds"
    )
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    
    provider_refund_id = models.CharField(max_length=200, blank=True)
    
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING
    )
    
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="requested_refunds"
    )
    
    created_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = "refunds"
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"Refund {self.amount} for {self.payment.id}"
