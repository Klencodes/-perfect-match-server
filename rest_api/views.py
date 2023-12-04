from datetime import datetime
from rest_framework.generics import ListAPIView, RetrieveAPIView
from channels.generic.websocket import WebsocketConsumer
from channels.generic.websocket import AsyncWebsocketConsumer
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
        if request.data["is_primary"]:
            cards = PaymentCard.objects.all()
            for item in cards:
                item.is_primary = False
                item.save()
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

# ADD FEEDBACK
class AddFeedback(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        print(request.data, "equest.data")
        serializer = FeedbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=self.request.user)
        return Response({"response": "SUCCESSFUL", "message": "Feedback successfully added", "results": serializer.data}, status=status.HTTP_201_CREATED)

# CHAT VIEW
class ChatRoomDetails(APIView):
    permission_classes = [IsAuthenticated]

    #This show details for a specific chat histories which containes list of messages tied to a chat room
    def get(self, request, pk):
        group = get_object_or_404(Group, pk=pk)
        messages = Message.objects.filter(group=group)
        message_data = []
        for message in messages:
            message_data.append({
                "message": message.message,
                "sender_id": message.sender.id,
                "sender_name": message.sender.full_name,
                "sender_picture": message.sender.profile_picture,
                "created_at": message.created_at,
            })

        return Response({"response": "SUCCESSFUL", "message": "Chat details successfully fetched", "results": message_data})
        
    def post(self, request):
        #Create group
        group, created = Group.objects.create(name=request.data['group_name'], image=request.data['group_image'],  purpose=request.data['purpose'],)
        group_id = group.id
        group = Group.objects.get(id=group_id)
        users = User.objects.filter(id__in=[request.data["users_ids"]])
        group.members.add(*users)
        if created:
            return Response({"response": "SUCCESSFUL", "message": "Group created successfully."})
        else:
            return Response({"response": "FAILED", "message": "Group already exists."})

    def put(self, request):
        # join a group
        group_id = request.data.get('group_id')
        try:
            group = Group.objects.get(id=group_id)
            group.add(request.user.username)
            return Response({"response": "SUCCESSFUL", "message": "User joined the group successfully."})
        except Group.DoesNotExist:
            return Response({"response": "FAILED", "message": "Group does not exist."})

class GroupMessages(APIView):
    permission_classes = [IsAuthenticated]
    
    #This show list of available groups 
    def get(self, request):
        groups = Group.objects.all()
        serializer = GroupSerializer(groups, many=True)
        chat_data = serializer.data
        for item in chat_data:
            messages = Message.objects.filter(group_id=item["id"])
            message_data = []
            for message in messages:
                message_data.append({
                    "message": message.message,
                    "sender_id": message.sender.id,
                    "sender_name": message.sender.full_name,
                    "sender_picture": message.sender.profile_picture,
                    "created_at": message.created_at,
                })
            item["messages"] = message_data
        return Response({"response": "SUCCESSFUL", "message": "Chat rooms successfully fetched", "results": chat_data})

# Web Socket consumer Api. This create and return live chats 
class GroupChatConsumer(WebsocketConsumer):
    http_user_and_session = True

    def connect(self):
        self.accept()
        group_id = self.scope['url_route']['kwargs']['group_id']
        group = 'group%s'%(group_id)
        self.group = group
        async_to_sync(self.channel_layer.group_add)(group, self.channel_name)
       
    def disconnect(self, close_code):
        pass

    def receive(self, text_data):
        #Abstract chat room id from the url
        group_id = self.scope['url_route']['kwargs']['group_id']
        # user = self.scope['user']
        data = json.loads(text_data)
        user_id = data["user_id"] 
        message = data["message"] 

        try:
            group = Group.objects.get(id=group_id)
            sender = User.objects.get(id=user_id)
            msg = Message.objects.create(message=message, group=group, sender=sender)
        except:
            return ''

        message_data =  {
            "message": message,
            "sender_id": json.dumps(sender.id, default=str),
            "sender_name": "%s %s"%(sender.first_name, sender.last_name),
            "sender_picture": sender.profile_picture,
            "created_at": json.dumps(msg.created_at, default=str)
        }
        async_to_sync(self.channel_layer.group_send)(
            self.group, { 
                "type": "chat_message", 
                "text": json.dumps(message_data), 
            },
        )
    
    def chat_message(self, event):
        self.send(text_data=event["text"])


class PrivateChatConsumer(AsyncWebsocketConsumer):
    print('CONNECTION.....')
    
    async def connect(self):
        print(self, 'self...')
        self.sender = self.scope['url_route']['kwargs']['sender_id']
        self.recepient = self.scope['url_route']['kwargs']['recepient_id']
        recepient = User.objects.filter(id=self.recepient)

        group = Group.objects.create(group_name=recepient.full_name, group_image=recepient.profile_picture, purpose='')
        group_id = group.id
        group = Group.objects.get(id=group_id)
        users = User.objects.filter(id__in=[self.sender, recepient.id])
        group.members.add(*users)
        print('connected and created group')
        await self.channel_layer.group_add(
            recepient.full_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        print('DISCONNECTED')
        pass
        # await self.channel_layer.group_discard(
        #     self.username1 + '-' + self.username2,
        #     self.channel_name
        # )

    async def receive(self, text_data):
        print('RECEIVED WORKES')

        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        sender_id = text_data_json['sender_id']
        sender = User.objects.filter(id=sender_id)
        group_id = self.scope['url_route']['kwargs']['group_id']

        try:
            group = Group.objects.get(id=group_id)
            sender = User.objects.get(id=sender_id)
            msg = Message.objects.create(message=message, group=group, sender=sender)
        except:
            return ''

        message_data =  {
            "message": message,
            "sender_id": json.dumps(sender.id, default=str),
            "sender_name": "%s %s"%(sender.first_name, sender.last_name),
            "sender_picture": sender.profile_picture,
            "created_at": json.dumps(msg.created_at, default=str)
        }
        await self.channel_layer.group_send(
            self.recepient.full_name,
            {
                'type': 'private_message',
                "text": json.dumps(message_data), 

            }
        )

    async def chat_message(self, event):
        self.send(text_data=event["text"])

