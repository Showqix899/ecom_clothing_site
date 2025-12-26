from django.urls import path
from .views import add_banner,delete_banner,search_banner,add_image_to
urlpatterns = [
    path('add/',add_banner,name='add-banner'),
    path('delete/<str:banner_id>/',delete_banner,name='banner-delete'),
    path('search/',search_banner,name='search-banner'),
    path('add-image-to/<str:type>/<str:banner_id>/',add_image_to,name='add-image-to'),    
]
