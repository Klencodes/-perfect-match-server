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
        users = User.objects.all().exclude(id=user.id)
        serializer = UserSerializer(users, many=True, context={"request": request})
        return Response({"response": "SUCCESSFUL", "message": "Users successfully fetched", "results": serializer.data}, status=status.HTTP_200_OK)


# CHAT VIEW
class ChatRoomDetails(APIView):
    permission_classes = [IsAuthenticated]

    #This show details for a specific chat histories which containes list of messages tied to a chat room
    def get(self, request, pk):
        chat_room = get_object_or_404(ChatRoom, pk=pk)
        chat_messages = ChatMessage.objects.filter(chat_room=chat_room)
        serializer = ChatMessageSerializer(chat_messages, many=True)
        return Response({"response": "SUCCESSFUL", "message": "Chat details successfully fetched", "results": serializer.data})

class ChatRooms(APIView):
    permission_classes = [IsAuthenticated]

    #This show list of available groups 
    def get(self, request):
        chat_groups = ChatRoom.objects.all()
        serializer = ChatRoomSerializer(chat_groups, many=True)
        return Response({"response": "SUCCESSFUL", "message": "Chat rooms successfully fetched", "results": serializer.data})

# Web Socket consumer Api. This create and return live chats 
class GroupChatConsumer(WebsocketConsumer):
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
            sender = User.objects.get(id=user_id)
            chat_message = ChatMessage.objects.create(message=message, chat_room=chat_room, sender=sender)
        except:
            return ''

        out_data =  {
            "message": message,
            "user_id": json.dumps(sender.id, default=str),
            "user_name": "%s %s"%(sender.first_name, sender.last_name),
            "user_picture": sender.profile_picture,
            "created_at": json.dumps(chat_message.created, default=str)
        }
        async_to_sync(self.channel_layer.group_send)(
            self.group_chat_room,
            { 
                "type": "chat.message", 
                "text": json.dumps(out_data), 
            },
        )
    
    def chat_message(self, event):
        self.send(text_data=event["text"])