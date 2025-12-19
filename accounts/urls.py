from django.urls import path
from .views import (
    register, login, refresh_token, 
    logout,test_data,create_modarator_or_admin,
    update_user,admin_update_user,
    delete_user,list_users,get_user_details,
    get_normal_user_details,search_users
)

urlpatterns = [
    path('register/', register, name='register'),
    path('login/', login, name='login'),
    path('refresh/', refresh_token, name='refresh_token'),
    path('logout/', logout, name='logout'),
    path('create-modarator_or_admin/<str:user_id>/',create_modarator_or_admin,name='create-modarator'),
    path('test/',test_data,name="test-data"),
    path('update-user/',update_user,name="update-user"),
    path('admin-update-user/<str:user_id>/',admin_update_user,name="admin-update-user"),
    path('delete-user/<str:user_id>/',delete_user,name="delete-user"),
    path('list-users/',list_users,name="list-users"),
    path('admin-user-details/<str:user_id>/',get_user_details,name="user-details"),
    path('user-details/',get_normal_user_details,name="normal-user-details"),
    path('search/',search_users,name='search-user'),
]
