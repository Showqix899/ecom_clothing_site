from django.urls import path
from .views import (place_order ,cancel_order,get_all_orders,
                    search_orders,update_order,delete_order
                    )

urlpatterns = [
    
    path('place/', place_order, name='place_order'),
    path('cancel/<str:order_id>/', cancel_order, name='cancel_order'),
    path('all/', get_all_orders, name='get_all_orders'),
    path('search/', search_orders, name='search_orders'),
    path('update-order/<str:order_id>/',update_order,name='update-order'),
    path('delete-order/<str:order_id>/',delete_order,name = "delete-order"),
    
]