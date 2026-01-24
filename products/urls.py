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
    
    #subcategories
    path('add-subcategory/<str:category_id>/', views.add_subcategory, name='add_subcategory'),
    path('delete-subcategory/<str:subcategory_id>/', views.delete_subcategory, name='delete_subcategory'),
    path('get-subcategories/<str:category_id>/', views.list_subcategories, name='get_subcategories'),
    path('all-subcategories/', views.all_subcategories, name='all_subcategories'),
    

    
    
    #get all attributes
    path('get-attributes/', views.get_attributes, name='get_attributes'),

    # Products
    path('create-product/', views.create_product, name='create_product'),
    
    #get products details
    path('product-details/<str:product_id>/', views.get_product_details, name='product_details'),
    
    #update product
    path('update-product/<str:product_id>/', views.update_product, name='update_product'),
    
    #delete product
    path('delete-product/<str:product_id>/', views.delete_product, name='delete_product'),
    
    #get all products
    path('all-products/', views.get_products, name='all_products'),
    
    #search and filtering products
    path('search-products/', views.product_list, name='search_products'),
    
    
    #update product images
    path('update-product-images/<str:product_id>/', views.update_product_images, name='update_product_images'),
    
    #export products to csv
    path('export-csv/', views.export_products_csv, name='export_products_csv'),

]
