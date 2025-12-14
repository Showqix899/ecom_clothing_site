from django.urls import path
from . import views

urlpatterns = [
    # Colors
    path('add-color/', views.add_color, name='add_color'),
    path('delete-color/<str:color_id>/', views.delete_color, name='delete_color'),

    # Sizes
    path('add-size/', views.add_size, name='add_size'),
    path('delete-size/<str:size_id>/', views.delete_size, name='delete_size'),
    
    # Categories
    path('add-category/', views.add_category, name='add_category'),
    path('delete-category/<str:category_id>/', views.delete_category, name='delete_category'),

    # Products
    path('create-product/', views.create_product, name='create_product'),

]
