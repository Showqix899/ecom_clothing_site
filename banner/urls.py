from django.urls import path
from .views import add_banner,delete_banner,search_banner
urlpatterns = [
    path('add/',add_banner,name='add-banner'),
    path('delete/<str:banner_id>/',delete_banner,name='banner-delete'),
    path('search/',search_banner,name='search-banner'),
]
