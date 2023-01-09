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



class ChatListView(APIView):
    
    def get(self, request):
        user = request.user
        chats = ChatMessage.objects.filter(Q(sender=user) | Q(receiver=user)).order_by('-created_at')
        serializer = ChatMessageSerializer(chats, many=True)
        return Response(serializer.data)

class ChatDetailView(APIView):

    def get(self, request, pk):
        chat = get_object_or_404(ChatMessage, pk=pk)
        serializer = ChatMessageSerializer(chat)
        return Response(serializer.data)

class CreateChatView(APIView):

    def post(self, request, pk):
        chat = get_object_or_404(ChatMessage, pk=pk)
        serializer = ChatMessageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(sender=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)