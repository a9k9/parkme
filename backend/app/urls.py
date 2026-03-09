"""
Main URL Configuration for ParkMe Platform
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

# Import ViewSets
from accounts.views import UserViewSet, AuditLogViewSet
from vehicles.views import VehicleViewSet
from parking.views import FacilityViewSet, ZoneViewSet, ParkingSpotViewSet, FacilityStaffViewSet
from pricing.views import PricingRuleViewSet, SubscriptionViewSet, UserSubscriptionViewSet, PricingEstimateViewSet
from bookings.views import BookingViewSet, BookingExtensionViewSet

# API Router
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'audit-logs', AuditLogViewSet, basename='auditlog')
router.register(r'vehicles', VehicleViewSet, basename='vehicle')
router.register(r'facilities', FacilityViewSet, basename='facility')
router.register(r'zones', ZoneViewSet, basename='zone')
router.register(r'parking-spots', ParkingSpotViewSet, basename='parkingspot')
router.register(r'facility-staff', FacilityStaffViewSet, basename='facilitystaff')
router.register(r'pricing-rules', PricingRuleViewSet, basename='pricingrule')
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')
router.register(r'user-subscriptions', UserSubscriptionViewSet, basename='usersubscription')
router.register(r'pricing', PricingEstimateViewSet, basename='pricing')
router.register(r'bookings', BookingViewSet, basename='booking')
router.register(r'booking-extensions', BookingExtensionViewSet, basename='bookingextension')

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    
    # API Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    
    # Authentication
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # API Routes
    path('api/', include(router.urls)),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

