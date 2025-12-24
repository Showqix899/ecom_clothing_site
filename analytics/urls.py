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
    analytics_product_revenue,
    analytics_product_sold_count,

    # ----- CATEGORY ANALYTICS -----
    analytics_category_revenue,

    # ----- EXPIRED ORDERS -----
    analytics_expired_orders,
    analytics_expired_order_items,
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

    # Product-wise revenue
    path(
        'products/revenue/',
        analytics_product_revenue,
        name='analytics-product-revenue'
    ),

    # Product-wise sold count
    path(
        'products/sold-count/',
        analytics_product_sold_count,
        name='analytics-product-sold-count'
    ),


    # ================== CATEGORY ANALYTICS ==================

    # Category-wise revenue
    path(
        'categories/revenue/',
        analytics_category_revenue,
        name='analytics-category-revenue'
    ),


    # ================== EXPIRED ORDER ANALYTICS ==================

    # Expired orders
    path(
        'orders/expired/',
        analytics_expired_orders,
        name='analytics-expired-orders'
    ),

    # Expired order items
    path(
        'orders/expired/items/',
        analytics_expired_order_items,
        name='analytics-expired-order-items'
    ),
]
