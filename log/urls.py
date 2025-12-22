from django.urls import path
from .views import list_logs,get_log,update_log,delete_log,log_search_filter

urlpatterns = [
    
    path("all/",list_logs,name='all'),
    path("details/<str:log_id>/",get_log,name="details-log"),
    path("update/<str:log_id>/",update_log,name="update-log"),
    path("delete/<str:log_id>/",delete_log,name="delete-log"),
    path("search/",log_search_filter,name="search-log"),
    
    
    
]
