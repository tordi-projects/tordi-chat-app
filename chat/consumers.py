import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'
        user = self.scope['user']

        if not user.is_authenticated:
            await self.close()
            return

        is_member = await self.is_participant(user)
        if not is_member:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        await self.set_online(user, True)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        user = self.scope['user']
        if user.is_authenticated:
            await self.set_online(user, False)

    async def receive(self, text_data):
        data = json.loads(text_data)
        event_type = data.get('type', 'message')
        user = self.scope['user']

        if event_type == 'typing':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_notification',
                    'sender_id': user.id,
                    'sender_name': user.display_name(),
                }
            )
            return

        message_text = (data.get('message') or '').strip()
        if not message_text:
            return

        message = await self.save_message(user, message_text)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message_text,
                'sender_id': user.id,
                'sender_name': user.display_name(),
                'timestamp': message['timestamp'],
                'message_id': message['id'],
                'attachment_url': None,
                'attachment_kind': None,
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def typing_notification(self, event):
        await self.send(text_data=json.dumps({'type': 'typing', **event}))

    @database_sync_to_async
    def is_participant(self, user):
        from .models import Conversation
        return Conversation.objects.filter(id=self.conversation_id, participants=user).exists()

    @database_sync_to_async
    def save_message(self, user, text):
        from .models import Conversation, Message
        conversation = Conversation.objects.get(id=self.conversation_id)
        msg = Message.objects.create(conversation=conversation, sender=user, text=text)
        return {'id': msg.id, 'timestamp': msg.timestamp.strftime('%H:%M')}

    @database_sync_to_async
    def set_online(self, user, is_online):
        user.is_online = is_online
        if not is_online:
            user.last_seen = timezone.now()
        user.save(update_fields=['is_online', 'last_seen'])
