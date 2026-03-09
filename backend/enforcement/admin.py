from django.contrib import admin
from .models import Violation


@admin.register(Violation)
class ViolationAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "facility", "violation_type", "penalty_amount", "status", "violation_time"]
    list_filter = ["violation_type", "status", "facility", "violation_time"]
    search_fields = ["user__email", "vehicle__plate_number"]
    readonly_fields = ["id", "created_at", "violation_time"]
