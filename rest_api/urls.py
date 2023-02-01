from django.urls import path
from .views import *

urlpatterns = [
    path('user/swipe_to_like/', swipe_to_like),  
    path('user/matches/', Matches.as_view()),  
    path('user/all/', AllUsers.as_view()),  
    path('user/payment_method/', PaymentMethod.as_view()),  
    path('user/payment_method/<uuid:pk>/', PaymentMethod.as_view()),  
    path('user/make_card_primary/', MakeCardPrimary.as_view()), 

    path('group_chats/', GroupMessages.as_view()),  
    path('group_chats/details/', ChatRoomDetails.as_view()),
    path('group_chats/details/<uuid:pk>/', ChatRoomDetails.as_view()),
  
]
