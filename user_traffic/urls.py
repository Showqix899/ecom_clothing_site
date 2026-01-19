from django.urls import path

from user_traffic.views import site_analytics,filtered_site_traffic


urlpatterns = [
    path('analytics/', site_analytics, name='site_analytics'),
    path('filtered-traffic/', filtered_site_traffic, name='filtered_site_traffic'),
]
