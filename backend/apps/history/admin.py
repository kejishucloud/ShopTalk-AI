from django.contrib import admin
from .models import ChatHistory


@admin.register(ChatHistory)
class ChatHistoryAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'user', 'is_user_message', 'created_at']
    list_filter = ['is_user_message', 'created_at']
    search_fields = ['session_id', 'message', 'response']
    readonly_fields = ['created_at'] 