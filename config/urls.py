
from django.contrib import admin
from django.urls import path,include





urlpatterns = [

    path('admin/', admin.site.urls),
    path('auth/',include('accounts.urls')),
    path('products/',include('products.urls')),
    path('cart/',include('cart.urls')),
    path('order/',include('order.urls')),
    path('logs/',include('log.urls')),
    path('banner/',include('banner.urls')),
    path('analytics/',include('analytics.urls')),
    path('traffic/',include('user_traffic.urls')),
    
]
