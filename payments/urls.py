from django.urls import path
from .views import submit_payment

urlpatterns = [
    path('submit/', submit_payment, name='submit_payment'),
]
