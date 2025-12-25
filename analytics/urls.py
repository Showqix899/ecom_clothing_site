from django.urls import path
from .views import (
    # ----- BASIC ORDER ANALYTICS -----
    analytics_total_orders,
    analytics_order_status_distribution,
    analytics_average_order_value,
    analytics_total_revenue,

    # ----- REVENUE ANALYTICS -----
    analytics_revenue_summary,

    # ----- PRODUCT ANALYTICS -----
    analytics_product_sold_count,
    product_analytics_revenue_dashboard,
    
    
    # ----- DASHBOARD ANALYTICS -----
    analytics_dashboard,
    analytics_time_based,
    
    
)

urlpatterns = [

    # ================== ORDER ANALYTICS ==================

    # Total orders (date range supported)
    path(
        'orders/total/',
        analytics_total_orders,
        name='analytics-total-orders'
    ),

    # Order status distribution
    path(
        'orders/status-distribution/',
        analytics_order_status_distribution,
        name='analytics-order-status-distribution'
    ),

    # Average Order Value (AOV)
    path(
        'orders/average-order-value/',
        analytics_average_order_value,
        name='analytics-average-order-value'
    ),

    # Total revenue (paid orders only)
    path(
        'orders/total-revenue/',
        analytics_total_revenue,
        name='analytics-total-revenue'
    ),

    # Revenue summary (paid / pending / expired)
    path(
        'orders/revenue-summary/',
        analytics_revenue_summary,
        name='analytics-revenue-summary'
    ),


    # ================== PRODUCT ANALYTICS ==================

   
    # Product-wise sold count
    path(
        'products/sold-count/',
        analytics_product_sold_count,
        name='analytics-product-sold-count'
    ),



    

   
    
    
    # ================== DASHBOARD ANALYTICS ==================
    path(
        'dashboard/',
        analytics_dashboard,
        name='analytics-dashboard'
    ),
    
    # ==================== TIME-BASED ANALYTICS ====================
    path(
        'time-based/',
        analytics_time_based,
        name='analytics-time-based'
    ),
    
    
    # ==================== PRODUCT REVENUE DASHBOARD ====================
    path(
        'products/revenue-dashboard/',
        product_analytics_revenue_dashboard,
        name='product-analytics-revenue-dashboard'
    ),
    
]
