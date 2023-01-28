from datetime import datetime
from rest_framework.generics import ListAPIView, RetrieveAPIView
from channels.generic.websocket import WebsocketConsumer
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from authentication.serializers import *
from asgiref.sync import async_to_sync
from rest_framework import generics
from rest_framework import status
from django.db.models import Q

from authentication.utils import calculate_age, calculate_age_with_string
from .serializers import *
from .models import *

@api_view(['POST', 'DELETE'])
def swipe_to_like(request):

    user = request.user
    other_user_id = request.data.get('liked_user_id')
    if request.method == 'POST':
        # User swiped right (liked)
        like, created = Like.objects.get_or_create(user=user, liked_user_id=other_user_id)
        if not created:
            return Response({"response": "FAILED", "message": "You have already liked this user."}, status=status.HTTP_226_IM_USED)
        # Check if there is a match
        if Like.objects.filter(user_id=other_user_id, liked_user=user).exists():
            # There is a match!
            Match.objects.create(user_liking_id=user.id, liked_user_id=other_user_id)
            return Response({"response": "SUCCESSFUL", "message": "Congratulation you have a match, chat now!!", "results": {"matched": True} }, status=status.HTTP_200_OK)
        return Response({"match": False})
    elif request.method == 'DELETE':
        # User swiped left (disliked)
        Like.objects.filter(user=user, liked_user_id=other_user_id).delete()
        return Response({"response": "SUCCESSFUL", "message": "You have disliked this user"}, status=status.HTTP_200_OK)


class Matches(ListAPIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk=None):
        user = self.request.user
        matches = Match.objects.filter(user_liking=user)
        serializer = MatchSerializer(matches, many=True, context={"request":request})
        return Response({"response": "SUCCESSFUL", "message": "Matches successfully fetched", "results": serializer.data}, status=status.HTTP_200_OK)

class AllUsers(ListAPIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk=None):
        user = self.request.user
        users = User.objects.all().exclude(id=user.id).order_by('-created_at')
        serializer = UsersSerializer(users, many=True, context={"request": request})
        users_data = serializer.data
        for user in users_data:
            user["age"] = calculate_age_with_string(user["birthdate"])
            address = Address.objects.filter(is_home_address=True, user_id=user["id"]).first()
            address_serializer = AddressSerializer(address, context={"request": request})
            user["address"]= address_serializer.data
        return Response({"response": "SUCCESSFUL", "message": "Users successfully fetched", "results": users_data}, status=status.HTTP_200_OK)


class MakeCardPrimary(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        cards = PaymentCard.objects.all()
        for item in cards:
            item.is_primary = False
            item.save()
        save_primary = PaymentCard.objects.get(id=request.data["card_id"])
        save_primary.is_primary = True
        save_primary.save()
        return Response({"response": "SUCCESSFUL", "message": "Primary card successfully set",}, status=status.HTTP_201_CREATED)

class PaymentMethod(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreatePaymentCard(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=self.request.user)
        return Response({"response": "SUCCESSFUL", "message": "Payment card successfully added", "results": serializer.data}, status=status.HTTP_201_CREATED)

    def get(self, request):
        user = self.request.user
        cards = PaymentCard.objects.filter(user=user).order_by('-created_at')
        serializer = PaymentSerializer(cards, many=True, context={"request": request})
        return Response({"response": "SUCCESSFUL", "message": "Payment cards successfully fetched", "results": serializer.data}, status=status.HTTP_200_OK)

    def retrieve(self, request, pk):
        pass

    def delete(self, request, pk):
        chat_room = get_object_or_404(PaymentCard, pk=pk).delete()
        return Response({"response": "SUCCESSFUL", "message": "Payment card successfully removed", }, status=status.HTTP_200_OK)


# CHAT VIEW
class ChatRoomDetails(APIView):
    permission_classes = [IsAuthenticated]

    #This show details for a specific chat histories which containes list of messages tied to a chat room
    def get(self, request, pk):
        chat_room = get_object_or_404(ChatRoom, pk=pk)
        chat_messages = ChatMessage.objects.filter(chat_room=chat_room)
        serializer = ChatMessageSerializer(chat_messages, many=True)
        return Response({"response": "SUCCESSFUL", "message": "Chat details successfully fetched", "results": serializer.data})
        
    def post(self, request):
        ChatRoom.objects.create(name=request.data['group_name'], image=request.data['image'], participants=request.data['participants'])
class ChatRooms(APIView):
    permission_classes = [IsAuthenticated]
    
    #This show list of available groups 
    def get(self, request):
        chat_groups = ChatRoom.objects.all()
        serializer = ChatRoomSerializer(chat_groups, many=True)
        chat_data = serializer.data
        for item in chat_data:
            message = ChatMessage.objects.filter(chat_room_id=item["id"])
            message_serializers = ChatMessageSerializer(message, many=True)
            item["messages"] = message_serializers.data
        return Response({"response": "SUCCESSFUL", "message": "Chat rooms successfully fetched", "results": chat_data})

# Web Socket consumer Api. This create and return live chats 
class ChatRoomConsumer(WebsocketConsumer):
    http_user_and_session = True

    def connect(self):
        self.accept()
        chat_room_id = self.scope['url_route']['kwargs']['chat_room_id']
        chat_room = 'chat_room_%s'%(chat_room_id)
        self.chat_room = chat_room
        async_to_sync(self.channel_layer.group_add)(chat_room, self.channel_name)
       
    def disconnect(self, close_code):
        pass

    def receive(self, text_data):
        #Abstract chat room id from the url
        chat_room_id = self.scope['url_route']['kwargs']['chat_room_id']
        # user = self.scope['user']
        data = json.loads(text_data)
        user_id = data["user_id"] 
        message = data["message"] 

        try:
            chat_room = ChatRoom.objects.get(id=chat_room_id)
            user = User.objects.get(id=user_id)
            chat_message = ChatMessage.objects.create(message=message, chat_room=chat_room, sender=user)
        except:
            return ''

        message_data =  {
            "message": message,
            "user_id": json.dumps(user.id, default=str),
            "user_name": "%s %s"%(user.first_name, user.last_name),
            "user_picture": user.profile_picture,
            "created_at": json.dumps(chat_message.created_at, default=str)
        }
        async_to_sync(self.channel_layer.group_send)(
            self.chat_room, { 
                "type": "chat_message", 
                "text": json.dumps(message_data), 
            },
        )
    
    def chat_message(self, event):
        self.send(text_data=event["text"])



class ChatConsumer(WebsocketConsumer):
    http_user_and_session = True

    def __init__(self, *args, **kwargs):
        self.user_inbox = None 

    def connect(self):
        self.user = self.scope['user']
        self.user_inbox = f'inbox_{self.user.first_name}'
        print(self.user, 'self.user')
        print(self.user_inbox, 'self.user_inbox')
        # accept the incoming connection
        self.accept()

        if self.user.is_authenticated:
            # create a user inbox for private messages
            async_to_sync(self.channel_layer.group_add)(
                self.user_inbox,
                self.channel_name,
            )
        
       
    def disconnect(self, close_code):
        pass

    def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        receiver_id = text_data_json['receiver_id']
        print(message, 'message')
        print(receiver_id, 'receiver_id')
        if not self.user.is_authenticated:
            return

        if message:
            # send private message to the target
            async_to_sync(self.channel_layer.group_send)(
                f'inbox_{receiver_id}',
                {
                    'type': 'private_message',
                    'user': self.user,
                    'message': message,
                }
            )
            # send private message delivered to the user
            self.send(json.dumps({
                'type': 'private_message_delivered',
                'message': message,
            }))
            return
        
    def private_message(self, event):
        self.send(text_data=json.dumps(event))

    def private_message_delivered(self, event):
        self.send(text_data=json.dumps(event))