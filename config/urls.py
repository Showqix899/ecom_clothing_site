
from django.contrib import admin
from django.urls import path,include





urlpatterns = [

    path('admin/', admin.site.urls),
    path('api/auth/',include('accounts.urls')),
    path('api/products/',include('products.urls')),
    path('api/cart/',include('cart.urls')),
    path('api/order/',include('order.urls')),
    path('api/logs/',include('log.urls')),
    path('api/banner/',include('banner.urls')),
    path('api/analytics/',include('analytics.urls')),
    path('api/traffic/',include('user_traffic.urls')),
    
]
