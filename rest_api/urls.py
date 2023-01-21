from django.urls import path
from .views import *

urlpatterns = [
    path('user/swipe_to_like/', swipe_to_like),  
    path('user/matches/', Matches.as_view()),  
    path('user/all/', AllUsers.as_view()),  
    path('chat_rooms/', ChatRooms.as_view()),  
    path('chat_rooms/chat_histories/<int:pk>/', ChatRoomDetails.as_view()),  
]
