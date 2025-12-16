from django.urls import path
from .views import place_order ,cancel_order

urlpatterns = [
    
    path('place/', place_order, name='place_order'),
    path('cancel/<str:order_id>/', cancel_order, name='cancel_order'),
    
]