from django.shortcuts import render
from rest_framework import viewsets
from .models import Prompt


class PromptViewSet(viewsets.ModelViewSet):
    """提示词视图集"""
    queryset = Prompt.objects.all()
    # serializer_class = PromptSerializer  # TODO: 创建序列化器 