import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import ChatMessage, LiveSession
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        
        # Check if session exists and user is registered
        session_exists = await self.session_exists(self.room_name)
        if not session_exists:
            await self.close()
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send user joined message
        if self.scope['user'].is_authenticated:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_join',
                    'message': f"{self.scope['user'].username} joined the session",
                    'username': 'System',
                    'timestamp': timezone.now().isoformat(),
                }
            )
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    # Receive message from WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        
        if self.scope['user'].is_authenticated:
            # Save message to database
            await self.save_message(message)
            
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'username': self.scope['user'].username,
                    'timestamp': timezone.now().isoformat(),
                }
            )
    
    # Receive message from room group
    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'username': event['username'],
            'timestamp': event['timestamp'],
        }))
    
    # Send user join notification
    async def user_join(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'username': event['username'],
            'timestamp': event['timestamp'],
        }))
    
    @database_sync_to_async
    def session_exists(self, room_name):
        try:
            session = LiveSession.objects.get(room_name=room_name)
            return True
        except LiveSession.DoesNotExist:
            return False
    
    @database_sync_to_async
    def save_message(self, message):
        user = self.scope['user']
        session = LiveSession.objects.get(room_name=self.room_name)
        ChatMessage.objects.create(session=session, user=user, message=message)