from django.urls import path
from .views import *

urlpatterns = [
    path('user/swipe_to_like/', swipe_to_like),  
    path('user/matches/', Matches.as_view()),  
    path('user/all/', AllUsers.as_view()),  
    path('user/chat_rooms/', ChatRoomAPIView.as_view()),  
    path('user/create_chat_message/', ChatMessageAPIView.as_view()),  
    path('user/details/<str:pk>/', ChatMessageDetailAPIView.as_view()),  
]
