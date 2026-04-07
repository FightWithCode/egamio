from django.urls import path
from . import views

urlpatterns = [
    path("conversations/", views.ConversationList.as_view(), name="chat_conversations"),
    path("conversations/start/", views.StartConversation.as_view(), name="chat_start_conversation"),
    path("conversations/<int:conversation_id>/messages/", views.ConversationMessages.as_view(), name="chat_messages"),
    path("users/search/", views.UserSearch.as_view(), name="chat_user_search"),
    path("unread-count/", views.ChatUnreadCount.as_view(), name="chat_unread_count"),
]
