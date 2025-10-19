from django.urls import path
from .views import chat_interface_view

urlpatterns = [
    path('', chat_interface_view, name='home'),
]