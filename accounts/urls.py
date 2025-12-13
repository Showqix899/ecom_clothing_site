from django.urls import path
from .views import register, login, refresh_token, logout,test_data,create_modarator

urlpatterns = [
    path('register/', register, name='register'),
    path('login/', login, name='login'),
    path('refresh/', refresh_token, name='refresh_token'),
    path('logout/', logout, name='logout'),
    path('create-modarator/',create_modarator,name='create-modarator'),
    path('test',test_data,name="test-data"),
]
