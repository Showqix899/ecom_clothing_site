from django.urls import path
from .views import (
    analytics_dashboard,
    analytics_product_dashboard,
    analytics_time_based,
)

urlpatterns = [
    # ==================== DASHBOARD ====================
    path(
        'dashboard/',
        analytics_dashboard,
        name='analytics-dashboard'
    ),

    # ==================== PRODUCT ANALYTICS ====================
    path(
        'products/',
        analytics_product_dashboard,
        name='analytics-product-dashboard'
    ),

    # ==================== TIME-BASED ANALYTICS ====================
    path(
        'time-based/',
        analytics_time_based,
        name='analytics-time-based'
    ),
]
