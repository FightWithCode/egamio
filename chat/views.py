from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models import Count
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Conversation, ConversationMember, Message
from .serializers import MessageSerializer


def _direct_conversations_for(user):
    user_convo_ids = ConversationMember.objects.filter(user=user).values_list("conversation_id", flat=True)
    return Conversation.objects.filter(id__in=user_convo_ids)\
        .annotate(member_count=Count("participants", distinct=True))\
        .filter(member_count=2)\
        .prefetch_related("participants")


class ConversationList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        conversations = _direct_conversations_for(request.user)
        data = []
        seen_users = set()

        for conversation in conversations:
            other_participants = conversation.participants.exclude(id=request.user.id)
            member_names = [participant.name or participant.email for participant in other_participants]
            title = ", ".join(member_names) if member_names else "Direct Chat"
            other_user = other_participants.first()
            if other_user and other_user.id in seen_users:
                continue
            if other_user:
                seen_users.add(other_user.id)

            last_message = conversation.messages.order_by("-created_at").first()
            last_read_at = ConversationMember.objects.filter(
                conversation=conversation, user=request.user
            ).values_list("last_read_at", flat=True).first()

            unread_query = conversation.messages.exclude(sender=request.user)
            if last_read_at:
                unread_query = unread_query.filter(created_at__gt=last_read_at)
            unread_count = unread_query.count()

            data.append({
                "id": conversation.id,
                "title": title,
                "participants": [
                    {"id": participant.id, "name": participant.name}
                    for participant in other_participants
                ],
                "other_user": {
                    "id": other_user.id,
                    "name": other_user.name,
                } if other_user else None,
                "last_message": last_message.content if last_message else "",
                "last_message_at": last_message.created_at if last_message else None,
                "unread_count": unread_count,
            })

        return Response({"msg": "fetched", "data": data}, status=status.HTTP_200_OK)


class ConversationMessages(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request, conversation_id):
        conversation = get_object_or_404(
            Conversation.objects.filter(participants=request.user),
            id=conversation_id,
        )

        since = request.query_params.get("since")
        queryset = conversation.messages.select_related("sender").order_by("created_at")
        if since:
            since_dt = parse_datetime(since)
            if since_dt:
                queryset = queryset.filter(created_at__gt=since_dt)

        serializer = MessageSerializer(queryset, many=True, context={"request": request})

        ConversationMember.objects.update_or_create(
            conversation=conversation,
            user=request.user,
            defaults={"last_read_at": timezone.now()},
        )

        return Response({"msg": "fetched", "data": serializer.data}, status=status.HTTP_200_OK)

    def post(self, request, conversation_id):
        conversation = get_object_or_404(
            Conversation.objects.filter(participants=request.user),
            id=conversation_id,
        )

        content = (request.data.get("content") or "").strip()
        image = request.FILES.get("image")

        if not content and not image:
            return Response({"msg": "Message content or image is required."}, status=status.HTTP_400_BAD_REQUEST)

        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=content,
            image=image,
        )

        conversation.updated_at = timezone.now()
        conversation.save(update_fields=["updated_at"])

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"chat_{conversation_id}",
            {"type": "chat.message", "message_id": message.id},
        )

        serializer = MessageSerializer(message, context={"request": request})
        return Response({"msg": "sent", "data": serializer.data}, status=status.HTTP_201_CREATED)


class StartConversation(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        participant_id = request.data.get("participant_id")
        if not participant_id:
            return Response({"msg": "participant_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        if str(participant_id) == str(request.user.id):
            return Response({"msg": "Cannot start a conversation with yourself."}, status=status.HTTP_400_BAD_REQUEST)

        User = request.user.__class__
        try:
            other_user = User.objects.get(id=participant_id)
        except User.DoesNotExist:
            return Response({"msg": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        user_convo_ids = ConversationMember.objects.filter(user=request.user).values_list("conversation_id", flat=True)
        other_convo_ids = ConversationMember.objects.filter(user_id=participant_id).values_list("conversation_id", flat=True)
        candidates = Conversation.objects.filter(id__in=user_convo_ids)\
            .filter(id__in=other_convo_ids)\
            .annotate(member_count=Count("participants", distinct=True))\
            .filter(member_count=2)\
            .order_by("-updated_at", "-id")

        conversation = candidates.first()
        if not conversation:
            conversation = Conversation.objects.create()
            ConversationMember.objects.create(conversation=conversation, user=request.user)
            ConversationMember.objects.create(conversation=conversation, user=other_user)
        else:
            extras = list(candidates[1:])
            for extra in extras:
                if not extra.messages.exists():
                    extra.delete()

        other_participant = conversation.participants.exclude(id=request.user.id).first()
        title = other_participant.name if other_participant else "Direct Chat"

        return Response({
            "msg": "created",
            "data": {
                "id": conversation.id,
                "title": title,
                "participants": [{"id": other_participant.id, "name": other_participant.name}] if other_participant else [],
                "other_user": {"id": other_participant.id, "name": other_participant.name} if other_participant else None,
                "last_message": "",
                "last_message_at": None,
                "unread_count": 0,
            }
        }, status=status.HTTP_200_OK)


class UserSearch(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        User = request.user.__class__
        query = (request.query_params.get("q") or "").strip()
        users = User.objects.exclude(id=request.user.id)
        if query:
            from django.db.models import Q
            users = users.filter(Q(name__icontains=query) | Q(email__icontains=query))

        data = [
            {"id": user.id, "name": user.name, "email": user.email}
            for user in users.order_by("name")[:20]
        ]
        return Response({"msg": "fetched", "data": data}, status=status.HTTP_200_OK)


class ChatUnreadCount(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        conversations = _direct_conversations_for(request.user)
        unread_conversations = 0
        total_unread = 0
        seen_users = set()

        for conversation in conversations:
            other_user = conversation.participants.exclude(id=request.user.id).first()
            if other_user and other_user.id in seen_users:
                continue
            if other_user:
                seen_users.add(other_user.id)
            last_read_at = ConversationMember.objects.filter(
                conversation=conversation, user=request.user
            ).values_list("last_read_at", flat=True).first()
            unread_query = conversation.messages.exclude(sender=request.user)
            if last_read_at:
                unread_query = unread_query.filter(created_at__gt=last_read_at)
            count = unread_query.count()
            if count > 0:
                unread_conversations += 1
                total_unread += count

        return Response(
            {
                "msg": "fetched",
                "unread_conversations": unread_conversations,
                "unread_messages": total_unread,
            },
            status=status.HTTP_200_OK,
        )
