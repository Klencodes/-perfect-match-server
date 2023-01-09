from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from authentication.serializers import *
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



#This list all the chat histories available
class ChatRoomAPIView(APIView):
    def get(self, request):
        chat_rooms = ChatRoom.objects.all()
        serializer = ChatRoomSerializer(chat_rooms, many=True)
            
        return Response({"response": "SUCCESSFUL", "messgage": "Chats successfully fetched", "results": serializer.data})

    def post(self, request):
        print(request.user.id, request.data["receiver_id"])
        model_instance = ChatRoom()
        model_instance.participants.add([request.user.id, request.data["receiver_id"]])
        print(model_instance, 'model_instance')
        model_instance.save()
        return Response({"response": "SUCCESSFUL", "messgage": "Chat room successfully created", "results": serializer.data})

class ChatMessageAPIView(APIView):
    def post(self, request):
        chat_room = get_object_or_404(ChatRoom, pk=request.data['chat_room_id'])
        serializer = PostChatMessageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(sender=request.user, chat_room=chat_room)
            return Response({"response": "SUCCESSFUL", "messgage": "Message successfully created", "results": serializer.data})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ChatMessageDetailAPIView(APIView):
    #This show details for a specific chat histories which containes listr of message tied to a chat room
    def get(self, request, pk):
        chat_room = get_object_or_404(ChatRoom, pk=pk)
        chat_messages = ChatMessage.objects.filter(chat_room=chat_room)
        print(chat_messages.values_list('sender',))
        serializer = ChatMessageSerializer(chat_messages, many=True)
        return Response({"response": "SUCCESSFUL", "messgage": "Chat details successfully fetched", "results": serializer.data})