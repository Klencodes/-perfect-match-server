from rest_framework import serializers
from .models import *
from authentication.models import User

class SimpleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model=User
        exclude=['user_type', 'prefered_gender', 'username', 'full_name', 'email', 'birthdate', 'verified_phone', 'verified_email', 'onboarding_completed', 'onboarding_percentage', 'is_staff', 'allow_push_notification', 'push_notifications', 'chat_notifications', 'news_letter', 'first_login', 'id_card', 'auth_provider', 'created_at', 'updated_at', 'password']
class MatchSerializer(serializers.ModelSerializer):
    class Meta:
        model=Match
        fields=[ 'id', 'created_at', 'liked_user', ]
    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['liked_user'] = SimpleUserSerializer(instance.liked_user_id).data
        return response

class ChatRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatRoom
        fields = ('id', 'name', 'image', 'participants', 'created_at')

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ('id', 'chat_room', 'sender', 'message', 'read', 'created_at')
        
class CreatePaymentCard(serializers.ModelSerializer):
    class Meta:
        model = PaymentCard
        fields = ('authorize_payment', 'is_primary', 'card_number', 'type', 'cvc', 'expiry_date', 'card_holder')

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentCard
        exclude = []
