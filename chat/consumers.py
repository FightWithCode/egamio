from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.core.cache import cache
from django.utils import timezone

from .models import ConversationMember, Message
from .serializers import MessageSerializer

PRESENCE_TTL_SECONDS = 120


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.user = self.scope.get("user")

        if not self.user or not self.user.is_authenticated:
            await self.close(code=4401)
            return

        is_member = await self._is_member(self.user.id, self.conversation_id)
        if not is_member:
            await self.close(code=4403)
            return

        self.group_name = f"chat_{self.conversation_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        await self._set_presence(self.user.id, self.conversation_id, True)
        online_ids = await self._get_online_participants(self.conversation_id)
        await self.send_json({"type": "presence_snapshot", "user_ids": online_ids})
        await self.channel_layer.group_send(
            self.group_name,
            {"type": "chat.presence", "user_id": self.user.id, "status": "online"},
        )

        await self._mark_read(self.user.id, self.conversation_id, timezone.now())

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self._set_presence(self.user.id, self.conversation_id, False)
            await self.channel_layer.group_send(
                self.group_name,
                {"type": "chat.presence", "user_id": self.user.id, "status": "offline"},
            )
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        # Optional client-driven actions.
        if content.get("type") == "ping":
            await self._set_presence(self.user.id, self.conversation_id, True)
            return
        if content.get("type") == "read":
            message_id = content.get("message_id")
            if message_id:
                await self._mark_read(self.user.id, self.conversation_id, timezone.now())
                await self.channel_layer.group_send(
                    self.group_name,
                    {"type": "chat.read", "message_id": message_id, "reader_id": self.user.id},
                )

    async def chat_message(self, event):
        message_id = event.get("message_id")
        if not message_id:
            return

        message = await self._get_message(message_id)
        if not message:
            return

        payload = await self._serialize_message(message)

        if message.sender_id != self.user.id:
            await self._mark_read(self.user.id, self.conversation_id, message.created_at)
            await self.channel_layer.group_send(
                self.group_name,
                {"type": "chat.read", "message_id": message.id, "reader_id": self.user.id},
            )

        await self.send_json({"type": "message", "data": payload})

    async def chat_read(self, event):
        await self.send_json({
            "type": "read",
            "message_id": event.get("message_id"),
            "reader_id": event.get("reader_id"),
        })

    async def chat_presence(self, event):
        await self.send_json({
            "type": "presence",
            "user_id": event.get("user_id"),
            "status": event.get("status"),
        })

    @database_sync_to_async
    def _is_member(self, user_id, conversation_id):
        return ConversationMember.objects.filter(conversation_id=conversation_id, user_id=user_id).exists()

    @database_sync_to_async
    def _get_message(self, message_id):
        return Message.objects.select_related("sender", "conversation").filter(id=message_id).first()

    @database_sync_to_async
    def _serialize_message(self, message):
        return MessageSerializer(message, context={"user": self.user}).data

    @database_sync_to_async
    def _mark_read(self, user_id, conversation_id, timestamp):
        ConversationMember.objects.update_or_create(
            conversation_id=conversation_id,
            user_id=user_id,
            defaults={"last_read_at": timestamp},
        )

    @database_sync_to_async
    def _set_presence(self, user_id, conversation_id, is_online):
        key = f"chat_presence:{conversation_id}:{user_id}"
        if is_online:
            cache.set(key, True, timeout=PRESENCE_TTL_SECONDS)
        else:
            cache.delete(key)

    @database_sync_to_async
    def _get_online_participants(self, conversation_id):
        user_ids = list(
            ConversationMember.objects.filter(conversation_id=conversation_id).values_list("user_id", flat=True)
        )
        online_ids = []
        for user_id in user_ids:
            if cache.get(f"chat_presence:{conversation_id}:{user_id}"):
                online_ids.append(user_id)
        return online_ids
