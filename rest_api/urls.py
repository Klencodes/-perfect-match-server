from django.urls import path
from .views import *

urlpatterns = [
    path('user/swipe_to_like/', swipe_to_like),  
    path('user/matches/', Matches.as_view()),  
    path('user/all/', AllUsers.as_view()),  
    path('user/payment_method/', PaymentMethod.as_view()),  
    path('user/payment_method/<str:pk>/', PaymentMethod.as_view()),  
    path('user/make_card_primary/', MakeCardPrimary.as_view()),  
    path('chat_rooms/', ChatRooms.as_view()),  
    path('chat_rooms/details/<str:pk>/', ChatRoomDetails.as_view()),
  
]
