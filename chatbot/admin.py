from django.contrib import admin
from .models import ChatSession, ChatMessage

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ("session_id", "user", "ip_address", "created_at")
    search_fields = ("session_id", "user__username",)
    readonly_fields = ("session_id", "ip_address", "user_agent", "created_at")

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("session", "sender", "intent", "created_at")
    list_filter = ("sender", "intent")
    search_fields = ("message",)
    readonly_fields = ("session", "sender", "message", "intent", "created_at")

