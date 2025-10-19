# ai_chat/urls.py
from django.urls import path
from .views import ChatAPIView, LoginAPIView, LogoutAPIView, IndexAPIView

urlpatterns = [
    path('', IndexAPIView.as_view(), name='index'),
    path('chat/', ChatAPIView.as_view(), name='chatbot_api'),
    path('login/', LoginAPIView.as_view(), name='login_api'),
    path('logout/', LogoutAPIView.as_view(), name='logout_api'),
]