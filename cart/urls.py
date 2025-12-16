from django.urls import path
from .views import (
    get_cart,
    add_to_cart,
    update_cart_quantity,
    update_cart_variant,
    remove_cart_item,
    clear_cart,
    select_cart_items
)

urlpatterns = [
    path('', get_cart, name='get_cart'),

    path('add/', add_to_cart, name='add_to_cart'),

    path('update-quantity/', update_cart_quantity, name='update_cart_quantity'),

    path('update-variant/', update_cart_variant, name='update_cart_variant'),

    path('remove-item/', remove_cart_item, name='remove_cart_item'),

    path('clear/', clear_cart, name='clear_cart'),
    
    path('select-item/', select_cart_items, name='select_cart_item'),
]
