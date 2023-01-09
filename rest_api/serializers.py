from rest_framework import serializers
from .models import *

class MatchSerializer(serializers.ModelSerializer):
    class Meta:
        model=Match
        # exclude=[]
        fields=[ 'id', 'created_at', 'liked_user', ]
        depth=1

from rest_framework import serializers

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ('id',  'receiver', 'message', 'created_at')
