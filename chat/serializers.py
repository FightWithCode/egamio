from rest_framework import serializers
from accounts.serializers import UserMinimalSerializer
from .models import Message


class MessageSerializer(serializers.ModelSerializer):
    sender = UserMinimalSerializer(read_only=True)
    image_url = serializers.SerializerMethodField()
    delivery_status = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ["id", "sender", "content", "image_url", "created_at", "delivery_status"]
        read_only_fields = fields

    def get_image_url(self, obj):
        if not obj.image:
            return None
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url

    def get_delivery_status(self, obj):
        request = self.context.get("request")
        user = self.context.get("user") if not request else request.user
        if not user or not user.is_authenticated:
            return "sent"

        member = obj.conversation.members.exclude(user=user).first()
        if not member:
            return "sent"

        if member.last_read_at and member.last_read_at >= obj.created_at:
            return "read"

        return "delivered"
