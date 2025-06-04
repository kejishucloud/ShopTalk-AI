from django.shortcuts import render
from django.http import JsonResponse
from rest_framework import viewsets
from .models import ChatHistory


class ChatHistoryViewSet(viewsets.ModelViewSet):
    """聊天历史视图集"""
    queryset = ChatHistory.objects.all()
    # serializer_class = ChatHistorySerializer  # TODO: 创建序列化器 


def test_view(request):
    """测试视图"""
    return JsonResponse({
        'status': 'success',
        'message': 'History app is working',
        'app': 'apps.history'
    }) 