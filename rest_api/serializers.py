from rest_framework import serializers
from .models import *

class MatchSerializer(serializers.ModelSerializer):
    class Meta:
        model=Match
        # exclude=[]
        fields=[ 'id', 'created_at', 'liked_user', ]
        depth=1

class ChatRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatRoom
        fields = ('id', 'name', 'created_at')

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ('id', 'chat_room', 'user', 'message', 'read', 'created_at')
        